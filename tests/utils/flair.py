from hashlib import md5
from faker import Faker
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.enums import RemoteFlairStatusEnum
from app.schemas.flair import FlairedEntity, FlairedTarget, FlairResults


def create_flair_results(db: Session, flair_targets: list, flair_entities: list):
    _targets = [FlairedTarget(id=x["id"], type=x["type"]) for x in flair_targets]
    _entities = [FlairedEntity(entity_type=x["type_name"], entity_value=x["value"]) for x in flair_entities]
    flair_results = FlairResults(targets=_targets, entities=_entities)

    return crud.entity.add_flair_results(db_session=db, flair_results=flair_results)


def create_remote_flair_html(faker: Faker, ips: list[str] | None = None, emails: list[str] | None = None, urls: list[str] | None = None) -> str:
    if ips is None:
        ips = []
        for _ in range(faker.pyint(1,3)):
            ips.append(faker.ipv4())

    ip_text = "<p>" + f"</p><p>{faker.sentence()} ".join(ips) + "</p>"

    if emails is None:
        emails = []
        for _ in range(faker.pyint(1,3)):
            emails.append(faker.ascii_email())

    email_text = ""
    for i, email in enumerate(emails):
        email_text += f"<tr><td>{i}</td><td>{email}</td></tr>"

    if urls is None:
        urls = []
        for _ in range(faker.pyint(1,3)):
            urls.append(faker.url())

    url_text = ""
    for i, url in enumerate(url_text):
        url_text += f"<h{i}>{url} {faker.word()}</h{i}>"

    base_html = """<!DOCTYPE html>
<html>
    <head>
        <style>
            table, th, td {
                border: 1px solid black;
                border-collapse: collapse;
            }
            th, td {
                padding: 5px;
                text-align: left;
            }
        </style>
    </head>
"""
    base_html += f"""
<body>
    <h1>{faker.sentence()}</h1>
    <p>{faker.sentence()}</p>
    {ip_text}
    <div>
        <br />
        <label>Some emails:</label>
        <table style="width:100%">
            <tr>
                <th>id</th>
                <th colspan="2">email</th>
            </tr>
            {email_text}
        </table>
    </div>
    </table>
    <!-- Entity in an entity?-->
    {url_text}
</body>
</html>
"""

    return base_html


def create_random_remote_flair(db: Session, faker: Faker) -> models.RemoteFlair:
    ips = []
    for _ in range(faker.pyint(1,3)):
        ips.append(faker.ipv4())
    emails = []
    for _ in range(faker.pyint(1,3)):
        emails.append(faker.user_name())
    urls = []
    for _ in range(faker.pyint(1,3)):
        urls.append(faker.url())

    html = create_remote_flair_html(faker, ips, emails, urls)
    remote_flair = schemas.RemoteFlairCreate(
        md5=md5(html.encode("utf-8")).hexdigest(),
        uri=faker.url(),
        html=html,
        status=RemoteFlairStatusEnum.ready,
        results={
            "ipv4": [{a: 1} for a in ips],
            "domain": [{a: 1} for a in urls],
            "email": [{a: 1} for a in emails],
        }
    )
    dict_obj = remote_flair.model_dump()
    dict_obj.pop("html", None)
    return crud.remote_flair.create(db, obj_in=dict_obj)
