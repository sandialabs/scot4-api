import uuid
import json
from os import path, remove, getcwd
from typing import Union, Any
from copy import deepcopy

from sqlalchemy.orm import Session
from fastapi import Depends
from tabulate import tabulate
from tempfile import gettempdir
from markdownify import markdownify
from xhtml2pdf import pisa
from html4docx import HtmlToDocx
from docx import Document
from bs4 import BeautifulSoup

from jinja2 import Environment, PackageLoader, select_autoescape
from weasyprint import HTML
# from objprint import op

from app import crud
from app.api import deps
from app.models import Entry, Alert, Entity, Signature, Role
from app.enums import TargetTypeEnum, ExportFormatEnum


def export_object(
    db: Session, 
    _obj: Any, 
    target_type: TargetTypeEnum, 
    format: ExportFormatEnum, 
    pretty_name: str, 
    roles: list[Role]
) -> str:
    '''
    Export a object to a requested filetype
        1. all objects first get an html representation via jinja templates
        2. get entities and use beautiful soup to "flair"
        3. weasyprint converts html to pdf, markdownify to md, htm4docs and docx to docx
        4. send to the requestor
    '''
    html = ''

    # limit the depth of the object printer
    # op.config(depth=3)
    # print("------ exporting object -------")
    # op(_obj)
    # print("-------------------------------")

    entities, count = crud.entity.retrieve_element_entities(
        db_session=db, source_id=_obj.id, source_type=target_type
    )
    # print(f"====== {count} entities =====")
    # for index, e in enumerate(entities):
    #     print(f"{index} => {e.value}")
    # op(entities)
    # print("=====================")

    # the _obj.entries ignore permissions
    # greg recommends using crud.entry.get_by_type to replace that in object

    entries, entry_count = crud.entry.get_by_type(
        db, 
        roles=roles,
        _id=_obj.id, 
        _type=target_type
    )

    if target_type == TargetTypeEnum.alertgroup:
        html = export_alertgroup(db, _obj, entries, entities)
    elif target_type == TargetTypeEnum.event:
        html = export_event(db, _obj, entries, entities)
    elif target_type == TargetTypeEnum.incident:
        html = export_incident(db, _obj, entries, entities)
    elif target_type == TargetTypeEnum.dispatch:
        html = export_dispatch(db, _obj, entries, entities)
    elif target_type == TargetTypeEnum.intel:
        html = export_intel(db, _obj, entries, entities)
    elif target_type == TargetTypeEnum.product:
        html = export_product(db, _obj, entries, entities)
    elif target_type == TargetTypeEnum.vuln_feed:
        html = export_vulnfeed(db, _obj, entries, entities)
    elif target_type == TargetTypeEnum.vuln_track:
        html = export_vulntrack(db, _obj, entries, entities)
    elif target_type == TargetTypeEnum.signature:
        html = export_signature(db, _obj, entries, entities)
    elif target_type == TargetTypeEnum.guide:
        html = export_guide(db, _obj, entries, entities)
    else:
        raise Exception(f"Unsuported Export of {str(target_type)}")

    flair_html = flair(html, entities)

    filename, mediatype = export_html_to_format(flair_html, format)
    return filename, mediatype


def export_alertgroup(db: Session, _obj: Any, entries: Any, entities: Any) -> str:
    template = get_template("alertgroup")
    content = template.render(
        alertgroup=_obj,
        entries=entries,
        entities=entities
    )
    return content


def export_event(db: Session, _obj: Any, entries: Any, entities: Any) -> str:
    alerts = get_promoted_alerts(_obj)
    template = get_template("event")
    content = template.render(
        event=_obj,
        alerts=alerts,
        entries=entries,
        entities=entities
    )
    return content


def export_incident(db: Session, _obj: Any, entries: Any, entities: Any) -> str:
    template = get_template("incident")
    content = template.render(
        incident=_obj,
        entries=entries,
        entities=entities
    )
    return content


def export_dispatch(db: Session, _obj: Any, entries: Any, entities: Any) -> str:
    template = get_template("dispatch")
    content = template.render(
        dispatch=_obj,
        entries=entries,
        entities=entities
    )
    return content


def export_intel(db: Session, _obj: Any, entries: Any, entities: Any) -> str:
    template = get_template("intel")
    content = template.render(
        intel=_obj,
        entries=entries,
        entities=entities
    )
    return content


def export_product(db: Session, _obj: Any, entries: Any, entities: Any) -> str:
    template = get_template("product")
    content = template.render(
        product=_obj,
        entries=entries,
        entities=entities
    )
    return content


def export_signature(db: Session, _obj: Any, entries: Any, entities: Any) -> str:
    template = get_template("signature")
    content = template.render(
        signature=_obj,
        entries=entries,
        entities=entities
    )
    return content


def export_guide(db: Session, _obj: Any, entries: Any, entities: Any) -> str:
    template = get_template("guide")
    content = template.render(
        guide=_obj,
        entries=entries,
        entities=entities
    )
    return content


def export_vulnfeed(db: Session, _obj: Any, entries: Any, entities: Any) -> str:
    template = get_template("vulnfeed")
    content = template.render(
        vulnfeed=_obj,
        entries=entries,
        entities=entities
    )
    return content


def export_vulntrack(db: Session, _obj: Any, entries: Any, entities: Any) -> str:
    template = get_template("vulntrack")
    content = template.render(
        vulntrack=_obj,
        entries=entries,
        entities=entities
    )
    return content


def get_promoted_alerts(_obj: Any):
    return getattr(_obj, 'alerts', [])


def get_entities(_obj: Any, target_type: TargetTypeEnum):
    _entities, count = crud.entity.retrieve_element_entities(
        db_session=db, source_id=_obj.id, source_type=target_type
    )
    return _entities


def from_json_filter(input: str):
    return json.loads(input)


def get_template(type: str):
    # print(getcwd())
    template_location = "templates"  # Directory with templates under app
    jinja_env = Environment(
        loader=PackageLoader("app", template_location),
        autoescape=select_autoescape()
    )
    jinja_env.filters['from_json'] = from_json_filter
    template = jinja_env.get_template(f"{type}.html")
    return template


def export_html_to_format(content: str, format: ExportFormatEnum):
    # get weasy to do it
    media_type = ""
    html = HTML(string=content)
    tmp_root = path.join(gettempdir(), f"{uuid.uuid4()}")
    tmp_ext = "tmp"
    tmp_file = ".".join([tmp_root, tmp_ext])
    if format == ExportFormatEnum.pdf:
        html.write_pdf(tmp_file)
        media_type = "application/pdf"
    elif format == ExportFormatEnum.html:
        with open(tmp_file, "w+b") as tmp:
            tmp.write(content.encode())
        media_type = "application/html"
    elif format == ExportFormatEnum.md:
        with open(tmp_file, "w+b") as tmp:
            tmp.write(f"{markdownify(content)}".encode())
        media_type = "text/markdown"
    elif format == ExportFormatEnum.docx:
        doc = Document()
        parser = HtmlToDocx()
        parser.add_html_to_document(content, doc)
        tmp_file = f"{tmp_root}.docx"
        doc.save(tmp_file)
    else:
        raise Exception(f"Unsuported Export format {str(format)}")

    return tmp_file, media_type


def flair(html: str, entities: Any) -> str:
    edict = {}
    for i, e in enumerate(entities):
        key = e.value
        edict[key] = i + 1

    soup = BeautifulSoup(html, features="lxml")
    flair_spans = soup.find_all('span', {"class":"entity"})
    # print(flair_spans)

    # iterate on flair_spans, apending a <a href="#entity_x">
    for fs in flair_spans:
        entity_val = fs['data-entity-value']

        fnum = 0
        if entity_val in edict:
            fnum = edict[entity_val]

        footnote = soup.new_tag("a", href=f"#entity_{fnum}")
        superscript = soup.new_tag("sup")
        superscript.append(f"{fnum}")
        footnote.append(superscript)
        fs.extend(footnote)
    flaired = soup.prettify()
    # print(flaired)
    return flaired
