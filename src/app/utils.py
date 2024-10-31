import json
import logging
import meilisearch
import requests
import traceback
import nh3
from os import environ

from faker import Faker
from pathlib import Path
from pydantic import BaseModel
from pydantic.fields import PydanticUndefined
from datetime import datetime, timedelta
from typing import Union, Tuple
from fastapi import HTTPException, Request, status
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from jose import jwt

from app.core.config import settings
from app.models import Entry, Alert
from app.core.logger import logger
from app.enums import TargetTypeEnum


def index_for_search(parent_subject: str, entry: Entry = None, alert: Alert = None):
    try:
        if settings.SEARCH_HOST != "" and settings.SEARCH_API_KEY != "" and settings.SEARCH_API_KEY is not None:
            client = meilisearch.Client(settings.SEARCH_HOST, settings.SEARCH_API_KEY)
            if entry is not None:
                client.index('entries').add_documents([{'parent_text': parent_subject, 'entry_id': entry.id, 'target_id': entry.target_id, 'target_type': entry.target_type.value, 'entry_text': entry.entry_data['plain_text']}])
            elif alert is not None:
                client.index('entries').add_documents([{'parent_text': parent_subject, 'entry_id': alert.id, 'target_id': alert.alertgroup_id, 'target_type': TargetTypeEnum.alertgroup.value, 'entry_text': dict(alert.data) if alert.data else None}])  # or should the be the parse data?
    except Exception:
        logging.exception(traceback.format_exc())


def send_flair_entry_request(flair_type: TargetTypeEnum, flair_entry) -> None:
    session = requests.Session()
    session.trust_env = False
    if settings.FLAIR_HOST is not None:
        post_url = settings.FLAIR_HOST + settings.FLAIR_API_FLAIR_ENDPOINT
        flair_data = None
        flair_id = flair_entry.id
        if flair_type == TargetTypeEnum.alertgroup:
            flair_data = {
                "alerts": [{"id": a.id, "row": dict(a.data)} for a in flair_entry.alerts]
            }
        elif flair_type == TargetTypeEnum.alert:
            flair_data = {"alerts": [{"id": flair_entry.id, "row": flair_entry.data}]}
            flair_type == TargetTypeEnum.alertgroup
            flair_id = flair_entry.alertgroup_id
        elif flair_type == TargetTypeEnum.entry:
            flair_data = flair_entry.entry_data["html"]
        else:
            flair_data = flair_entry.data
        post_data = {"id": flair_id, "type": flair_type.value, "data": flair_data}
        resp = None
        try:
            resp = session.post(post_url, data=json.dumps(post_data), headers={'Authorization': f'apikey {settings.FLAIR_API_KEY}', 'Content-Type': 'application/json'})
            print('Sent flair request')
            print(resp.text)
        except Exception:
            logging.exception("Error while connecting to flair host")
        if resp and resp.status_code >= 400:
            logging.error("Error while sending flair notification: %s" % resp.body)


def send_new_regex_request(entity_value, entity_type) -> None:
    session = requests.Session()
    session.trust_env = False
    if settings.FLAIR_HOST is not None:
        post_url = settings.FLAIR_HOST + settings.FLAIR_API_REGEX_ENDPOINT
        scot4_regex_body = {"name": entity_value, "description": "User Defined Flair", "match": f"\\b{entity_value}\\b", "entity_type": entity_type, "regex_type": "udef", "re_order": 30, "multiword": False}
        resp = None
        try:
            resp = session.post(post_url, data=json.dumps(scot4_regex_body), headers={'Authorization': f'apikey {settings.FLAIR_API_KEY}', 'Content-Type': 'application/json'})
            print('Sent Create Regex request')
            print(resp.text)
        except Exception:
            logging.exception("Error while connecting to flair host")
        if resp and resp.status_code >= 400:
            logging.error("Error while sending flair notification: %s" % resp.body)


def send_reflair_request(id: int, flair_type: TargetTypeEnum, object_to_flair: Union[dict | str]) -> None:
    session = requests.Session()
    session.trust_env = False
    if settings.FLAIR_HOST is not None:
        resp = None
        try:
            resp = session.post(
                settings.FLAIR_HOST + settings.FLAIR_API_FLAIR_ENDPOINT,
                data=json.dumps({"id": id, "type": flair_type.value, "data": object_to_flair}),
                headers={'Authorization': f'apikey {settings.FLAIR_API_KEY}', 'Content-Type': 'application/json'}
            )
        except Exception:
            logging.exception("Error while connecting to flair host")
        if resp and resp.status_code >= 400:
            logging.error("Error while sending flair notification: %s" % resp.body)


def send_flair_enrichment_request(entity, enrichments: list[str] | None = None) -> None:
    session = requests.Session()

    # verify this is an entity type with enrichments available
    if settings.ENRICHMENT_TYPES is not None and settings.ENRICHMENT_TYPES != "":
        if entity.type_name not in settings.ENRICHMENT_TYPES.split(";"):
            logging.info(f"Not enriching entity {entity.id}. No enrichments available for type {entity.type_name}")
            return False

    if settings.ENRICHMENT_HOST is not None and settings.ENRICHMENT_HOST != "":
        post_url = settings.ENRICHMENT_HOST + settings.ENRICHMENT_API_JOB_ENDPOINT
        post_url = post_url.replace('[ENTITY_TYPE_PLACEHOLDER]', entity.type_name)
        req_dict = {
            'conf': {
                'entity_id': entity.id,
                'entity_type': entity.type_name,
                'entity_value': entity.value,
                'callback_url': settings.API_EXTERNAL_BASE
            }
        }
        resp = None
        try:
            resp = session.post(post_url, data=json.dumps(req_dict), auth=(settings.ENRICHMENT_USERNAME, settings.ENRICHMENT_PASSWORD),
                                headers={'Content-Type': 'application/json'}, verify=environ.get('REQUESTS_CA_BUNDLE')
                                )
        except Exception:
            logging.exception("Error while connecting to enrichment host")
            logging.exception(traceback.format_exc())
            return False
        if resp is not None and resp.status_code >= 400 and resp.text:
            logging.error("Error while sending enrichment notification: %s" % resp.text)
            return False

        # Enrichment successfully sent to Enrichment Host
        return True


def send_new_account_email(email_to: str, username: str, password: str) -> None:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - New account for user {username}"
    with open(Path(settings.EMAIL_TEMPLATES_DIR) / "new_account.html") as f:
        template_str = f.read()
    link = settings.SERVER_HOST
    # send_email(
    #     email_to=email_to,
    #     subject_template=subject,
    #     html_template=template_str,
    #     environment={
    #         "project_name": settings.PROJECT_NAME,
    #         "username": username,
    #         "password": password,
    #         "email": email_to,
    #         "link": link,
    #     },
    # )


def generate_password_reset_token(email: str) -> str:
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email}, settings.SECRET_KEY, algorithm="HS256"
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> str | None:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return decoded_token["email"]
    except jwt.JWTError:
        return None


def generate_unique_reference_id_for_background_task(endpoint=None, verb=None, username=None):
    return hash(f"{endpoint}-{verb}-{username}-{datetime.now().timestamp()}")


class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: str | None = None,
        scopes: dict[str, str] | None = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> str | None:
        authorization: str = request.headers.get(
            "Authorization"
        )  # check the Authorization header like normal
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            authorization: str = request.cookies.get(
                "access_token"
            )  # changed to accept access token from httpOnly Cookie
            scheme, param = get_authorization_scheme_param(authorization)
            if not authorization or scheme.lower() != "bearer":
                if self.auto_error:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Not authenticated",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                else:
                    return None

            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return param
        return param


# These should be allowed on svg elements
# Taken from dompurify
svg_attributes = ['accent-height', 'accumulate', 'additive', 'alignment-baseline', 'ascent',
                  'attributename', 'attributetype', 'azimuth', 'basefrequency', 'baseline-shift',
                  'begin', 'bias', 'by', 'class', 'clip', 'clippathunits', 'clip-path', 'clip-rule',
                  'color', 'color-interpolation', 'color-interpolation-filters', 'color-profile',
                  'color-rendering', 'cx', 'cy', 'd', 'dx', 'dy', 'diffuseconstant', 'direction',
                  'display', 'divisor', 'dur', 'edgemode', 'elevation', 'end', 'fill', 'fill-opacity',
                  'fill-rule', 'filter', 'filterunits', 'flood-color', 'flood-opacity', 'font-family',
                  'font-size', 'font-size-adjust', 'font-stretch', 'font-style', 'font-variant',
                  'font-weight', 'fx', 'fy', 'g1', 'g2', 'glyph-name', 'glyphref', 'gradientunits',
                  'gradienttransform', 'height', 'href', 'id', 'image-rendering', 'in', 'in2', 'k',
                  'k1', 'k2', 'k3', 'k4', 'kerning', 'keypoints', 'keysplines', 'keytimes', 'lang',
                  'lengthadjust', 'letter-spacing', 'kernelmatrix', 'kernelunitlength', 'lighting-color',
                  'local', 'marker-end', 'marker-mid', 'marker-start', 'markerheight', 'markerunits',
                  'markerwidth', 'maskcontentunits', 'maskunits', 'max', 'mask', 'media', 'method', 'mode',
                  'min', 'name', 'numoctaves', 'offset', 'operator', 'opacity', 'order', 'orient', 'orientation',
                  'origin', 'overflow', 'paint-order', 'path', 'pathlength', 'patterncontentunits',
                  'patterntransform', 'patternunits', 'points', 'preservealpha', 'preserveaspectratio',
                  'primitiveunits', 'r', 'rx', 'ry', 'radius', 'refx', 'refy', 'repeatcount', 'repeatdur',
                  'restart', 'result', 'rotate', 'scale', 'seed', 'shape-rendering', 'specularconstant',
                  'specularexponent', 'spreadmethod', 'startoffset', 'stddeviation', 'stitchtiles', 'stop-color',
                  'stop-opacity', 'stroke-dasharray', 'stroke-dashoffset', 'stroke-linecap', 'stroke-linejoin',
                  'stroke-miterlimit', 'stroke-opacity', 'stroke', 'stroke-width', 'style', 'surfacescale',
                  'systemlanguage', 'tabindex', 'targetx', 'targety', 'transform', 'transform-origin',
                  'text-anchor', 'text-decoration', 'text-rendering', 'textlength', 'type', 'u1', 'u2',
                  'unicode', 'values', 'viewbox', 'viewBox', 'visibility', 'version', 'vert-adv-y', 'vert-origin-x',
                  'vert-origin-y', 'width', 'word-spacing', 'wrap', 'writing-mode', 'xchannelselector',
                  'ychannelselector', 'x', 'x1', 'x2', 'xmlns', 'y', 'y1', 'y2', 'z', 'zoomandpan']
# Tags that can appear in svgs
# Also taken from dompurify
svg_tags = ['svg', 'a', 'altglyph', 'altglyphdef', 'altglyphitem', 'animatecolor', 'animatemotion',
            'animatetransform', 'circle', 'clippath', 'defs', 'desc', 'ellipse', 'filter', 'font', 'g',
            'glyph', 'glyphref', 'hkern', 'image', 'line', 'lineargradient', 'marker', 'mask', 'metadata',
            'mpath', 'path', 'pattern', 'polygon', 'polyline', 'radialgradient', 'rect', 'stop',
            'switch', 'symbol', 'text', 'textpath', 'title', 'tref', 'tspan', 'view', 'vkern']
sanitize_attributes = {'a': set(['href', 'hreflang']),
                       'bdo': set(['dir']),
                       'blockquote': set(['cite']),
                       'col': set(['align', 'char', 'charoff', 'span']),
                       'colgroup': set(['align', 'char', 'charoff', 'span']),
                       'del': set(['cite', 'datetime']),
                       'hr': set(['align', 'size', 'width']),
                       'img': set(['align', 'alt', 'src', 'height', 'width']),
                       'ins': set(['cite', 'datetime']),
                       'ol': set(['start']),
                       'q': set(['cite']),
                       'table': set(['align', 'char', 'charoff', 'summary', 'cellpadding', 'cellspacing']),
                       'tbody': set(['align', 'char', 'charoff']),
                       'td': set(['align', 'char', 'charoff', 'colspan', 'headers', 'rowspan']),
                       'tfoot': set(['align', 'char', 'charoff']),
                       'thead': set(['align', 'char', 'charoff', 'colspan', 'headers', 'rowspan', 'scope']),
                       'tr': set(['align', 'char', 'charoff']),
                       'span': set(['data-entity-value', 'data-entity-type', 'class']),
                       '*': set(['style', 'bgcolor', 'background', 'tabindex', 'align', 'border', 'color', 'width', 'height', 'valign', 'vspace', 'hspace', 'hidden'] + svg_attributes)
                       }
# Allow svg attributes only on svg tags
for t in svg_tags:
    if t in sanitize_attributes:
        for a in svg_attributes:
            sanitize_attributes[t].add(a)
    else:
        sanitize_attributes[t] = set(svg_attributes)

sanitize_tags = set(['a', 'abbr', 'acronym', 'area', 'article', 'aside',
                     'b', 'bdi', 'bdo', 'blockquote', 'br', 'caption', 'center',
                     'cite', 'code', 'col', 'colgroup', 'data', 'dd', 'del', 'details',
                     'dfn', 'div', 'dl', 'dt', 'em', 'figcaption', 'figure', 'footer', 'h1',
                     'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'hgroup', 'hr', 'i', 'img', 'ins', 'kbd',
                     'kbd', 'li', 'map', 'mark', 'nav', 'ol', 'p', 'pre', 'q', 'rp', 'rt', 'rtc', 'ruby',
                     's', 'samp', 'small', 'span', 'strike', 'strong', 'sub', 'summary', 'sup', 'table', 'tbody',
                     'td', 'th', 'thead', 'time', 'tr', 'tt', 'u', 'ul', 'var', 'wbr'] + svg_tags)


def sanitize_attribute_filter_flaired_alert(element, attribute, value):
    if (attribute == 'href' or attribute == 'src') and value.startswith('data:'):
        if attribute != 'src' or element != 'img' or not value.startswith('data:image/'):
            return None
    if element == 'span' and attribute == 'class' and "entity" in value:
        return "entity"
    elif element == 'span' and attribute == 'class' and "entity" not in value:
        return None
    elif element == 'span' and (attribute == 'data-entity-type' or attribute == 'data-entity-value'):
        value = value.replace('"', "")
        value = value.replace('\\', '')
        return value
    else:
        return value


def sanitize_attribute_filter(element, attribute, value):
    if (attribute == 'href' or attribute == 'src') and value.startswith('data:'):
        if attribute != 'src' or element != 'img' or not value.startswith('data:image/'):
            return None
    if element == 'span' and attribute == 'class' and "entity" in value:
        return "entity"
    elif element == 'span' and attribute == 'class' and "entity" not in value:
        return None
    elif element == 'span' and (attribute == 'data-entity-type' or attribute == 'data-entity-value'):
        return value
    else:
        return value


# Add "data" to the permitted list of url schemes (data urls other than img src
# will be removed in the attribute filter)
# This list is hardcoded here until the PyPi version of nh3 exposes it in the next version
NH3_ALLOWED_URL_SCHEMES = {"bitcoin", "ftp", "ftps", "geo", "http", "https", "im", "irc",
                           "ircs", "magnet", "mailto", "mms", "mx", "news", "nntp",
                           "openpgp4fpr", "sip", "sms", "smsto", "ssh", "tel", "url",
                           "webcal", "wtai", "xmpp"}
allowed_url_schemes = NH3_ALLOWED_URL_SCHEMES.union({"data"})


def sanitize_html(html: str, flaired_alert=False):
    if isinstance(html, str):
        if flaired_alert is True:
            # This should come in the form of an array. We are going to change it instead to <br> separated html string
            try:
                html = json.loads(html)
                if isinstance(html, list):
                    html = "<br/>".join(html)
                res = nh3.clean(html, tags=sanitize_tags, attributes=sanitize_attributes, attribute_filter=sanitize_attribute_filter_flaired_alert, url_schemes=allowed_url_schemes)
                return res
            except Exception:
                logger.warning('Unable to parse flaired data as an array, defaulting to regular sanitization')
                res = nh3.clean(html, tags=sanitize_tags, attributes=sanitize_attributes, attribute_filter=sanitize_attribute_filter, url_schemes=allowed_url_schemes)
                return res
        else:
            res = nh3.clean(html, tags=sanitize_tags, attributes=sanitize_attributes, attribute_filter=sanitize_attribute_filter, url_schemes=allowed_url_schemes)
            return res
    else:
        return ""


def escape_sql_like(like_string: str):
    return like_string.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


def is_bool(value: str) -> bool:
    value = value.lower()
    if value in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif value in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    else:
        raise ValueError(f"invalid truth value {value}")


def filter_fixup(value: str) -> str:
    """
    Clean up all filter searches by removing leading/trailing whitespace
    removes any escape characters i.e. \\
    """
    return value.strip().replace("\\", "")


def create_schema_details(schema: BaseModel) -> Tuple[str, dict[str, dict]]:
    """
    Dynamically create schema descriptions and examples
    """

    # add possible entries to description
    key_name = schema.__name__.lower()
    faker = Faker()
    examples = {
        f"{key_name}_basic": {
            "summary": "Basic Example",
            "description": "All basic fields",
            "value": {}
        },
        f"{key_name}_required": {
            "summary": "Required Example",
            "description": "Only Required Fields",
            "value": {}
        }
    }

    description = "\n\n### Fields\n"
    # add field type to the description
    for field_name, field_value in schema.model_fields.items():
        # if set to exclude from schema then dont add anything
        if field_value.exclude:
            continue

        description += f"- `{field_name}`\n\n"
        # if deprecated report that
        if field_value.deprecated:
            description += f"  - **{field_value.deprecation_message}**\n\n"

        # if any description was provided
        if field_value.description:
            description += f"  - Description: {field_value.description}\n\n"

        # indicate if the field is required or not and then add it to the required example
        description += f"  - Required: `{field_value.is_required()}`\n\n"

        # display the field type str, int, etc do some cleanup on the string
        annotation = str(field_value.annotation).replace("pydantic.types.", "")\
            .replace("<class '", "")\
            .replace("<enum '", "")\
            .replace("'>", "")\
            .replace("datetime.", "")\
            .replace("app.", "")\
            .replace("enums.", "")\
            .replace("schemas.", "")
        description += f"  - Type: `{annotation}`\n\n"

        # if a field has a default value
        if field_value.default is not None and field_value.default != PydanticUndefined:
            # special case for enums
            description += f"  - Default Value: `{field_value.default}`\n\n"
            if field_value.is_required():
                examples[f"{key_name}_required"]["value"][field_name] = field_value.default
            examples[f"{key_name}_basic"]["value"][field_name] = field_value.default
        # if a field has an example
        elif field_value.examples:
            if field_value.is_required():
                examples[f"{key_name}_required"]["value"][field_name] = field_value.examples[0]
            examples[f"{key_name}_basic"]["value"][field_name] = field_value.examples[0]
        # otherwise generate some fake data to fill everything else out
        else:
            # if no default value make some up
            if field_value.annotation == str | None or field_value.annotation == str:
                if field_value.is_required():
                    examples[f"{key_name}_required"]["value"][field_name] = faker.word()
                examples[f"{key_name}_basic"]["value"][field_name] = faker.word()
            elif field_value.annotation == int | None or field_value.annotation == int:
                if field_value.is_required():
                    examples[f"{key_name}_required"]["value"][field_name] = faker.pyint()
                examples[f"{key_name}_basic"]["value"][field_name] = faker.pyint()
            elif field_value.annotation == bool | None or field_value.annotation == bool:
                if field_value.is_required():
                    examples[f"{key_name}_required"]["value"][field_name] = faker.pybool()
                examples[f"{key_name}_basic"]["value"][field_name] = faker.pybool()
            elif field_value.annotation == datetime | None or field_value.annotation == datetime:
                if field_value.is_required():
                    examples[f"{key_name}_required"]["value"][field_name] = faker.date_time_this_month()
                examples[f"{key_name}_basic"]["value"][field_name] = faker.date_time_this_month()
            else:
                # everything else for now just add the annotation
                if field_value.is_required():
                    examples[f"{key_name}_required"]["value"][field_name] = annotation
                examples[f"{key_name}_basic"]["value"][field_name] = annotation

        if field_value.examples:
            for i, example in enumerate(field_value.examples):
                examples[f"{key_name}_{field_name}_{i}"] = {
                    "summary": f"Field {field_name} #{i} Example",
                    "description": f"Using Field {field_name} #{i} with other basic Fields",
                    "value": {
                        field_name: example
                    }
                }
    # merge the other examples (if any) with the basic one
    delete_keys = []
    for key, value in examples.items():
        if value["summary"].startswith("Field") and value["summary"].endswith("Example"):
            value["value"] = {**examples[f"{key_name}_basic"]["value"], **value["value"]}
        # mark any empty examples for deletion
        if value["value"] == {}:
            delete_keys.append(key)
    # delete any examples
    for key in delete_keys:
        del examples[key]

    return description, examples


"""
Default Tags
-----------------
a, abbr, acronym, area, article, aside, b, bdi, bdo, blockquote, br, caption, center, cite, code,col, colgroup, data, dd, del, details, dfn, div,dl, dt, em, figcaption, figure, footer, h1, h2,h3, h4, h5, h6, header, hgroup, hr, i, img,ins, kbd, kbd, li, map, mark, nav, ol, p, pre,q, rp, rt, rtc, ruby, s, samp, small, span,strike, strong, sub, summary, sup, table, tbody, td, th, thead, time, tr, tt, u, ul, var, wbr


Default Attributes allowed by tag
-----------------------------------------------------
a =>
    href, hreflang
bdo =>
    dir
blockquote =>
    cite
col =>
    align, char, charoff, span
colgroup =>
    align, char, charoff, span
del =>
    cite, datetime
hr =>
    align, size, width
img =>
    align, alt, height, src, width
ins =>
    cite, datetime
ol =>
    start
q =>
    cite
table =>
    align, char, charoff, summary
tbody =>
    align, char, charoff
td =>
    align, char, charoff, colspan, headers, rowspan
tfoot =>
    align, char, charoff
th =>
    align, char, charoff, colspan, headers, rowspan, scope
thead =>
    align, char, charoff
tr =>
    align, char, charoff
"""
