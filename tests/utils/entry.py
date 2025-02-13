import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud, schemas
from app.enums import EntryClassEnum, TargetTypeEnum, TlpEnum
from app.schemas.entry import EntryCreate
from app.schemas.flair import FlairedEntity, FlairedTarget, FlairResults

try:
    from tests.utils.utils import generate_html_entry
    from tests.utils.user import create_random_user
except ImportError:
    # needed to make initial_data.py function properly
    from utils import generate_html_entry
    from user import create_random_user


def create_random_entry(
    db: Session,
    faker: Faker,
    owner: schemas.User | None = None,
    parent_entry_id: int | None = None,
    target_type: TargetTypeEnum | None = None,
    target_id: int | None = None,
    entry_class: EntryClassEnum | None = None,
    assignee: str | None = None,
    status: str | None = None,
):
    tlp = random.choice(list(TlpEnum))
    if owner is None:
        owner = create_random_user(db, faker)
    if target_type is None:
        target_list = list(TargetTypeEnum)
        target_list.remove(TargetTypeEnum.none)
        target_list.remove(TargetTypeEnum.remote_flair)
        target_type = random.choice(target_list)
    if target_id is None:
        target_id = faker.pyint()
    if entry_class is None:
        entry_class = random.choice(list(EntryClassEnum))

    data_raw, data_flaired, entry_entities = generate_html_entry(faker)
    entry_data = {
        "html": data_raw,
        "flaired_html": data_flaired,
        "flaired": True,
        "plain_text": data_raw
    }

    if assignee is not None:
        entry_data["assignee"] = assignee
    else:
        username, address = faker.safe_email().split("@")
        email = f"{username}_{faker.pyint()}@{address}"
        entry_data["assignee"] = email

    if status is not None:
        entry_data["status"] = status
    else:
        entry_data["assignee"] = faker.word()

    entry_create = EntryCreate(
        owner=owner.username,
        tlp=tlp,
        target_type=target_type,
        parent_entry_id=parent_entry_id,
        target_id=target_id,
        entry_class=entry_class,
        entry_data=entry_data,
    )

    entry = crud.entry.create(db, obj_in=entry_create)
    flair_targets = [
        FlairedTarget(id=target_id, type=target_type),
        FlairedTarget(id=entry.id, type=TargetTypeEnum.entry),
    ]
    flair_entities = [
        FlairedEntity(entity_type=x.type_name, entity_value=x.value)
        for x in entry_entities
    ]
    flair_results = FlairResults(targets=flair_targets, entities=flair_entities)
    crud.entity.add_flair_results(db_session=db, flair_results=flair_results)
    return entry
