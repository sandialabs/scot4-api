import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud, schemas
from app.enums import ThreatModelName, TargetTypeEnum, EntryClassEnum

try:
    from tests.utils.entry import create_random_entry
    from tests.utils.user import create_random_user
    from tests.utils.popularity import create_random_popularity
    from tests.utils.user_links import create_random_user_links
except ImportError:
    # needed to make initial_data.py function properly
    from entry import create_random_entry
    from user import create_random_user
    from popularity import create_random_popularity
    from user_links import create_random_user_links


ATTACK_ITEMS = [
    {
        "ids": ["T1595", "T1595.001", "T1595.002", "T1595.003", "T1592", "T1592.001", "T1592.002", "T1592.003", "T1592.004"],
        "tactic": "reconnaissance"
    },
    {
        "ids": ["T1650", "T1584", "T1584.001", "T1584.002", "T1584.003", "T1584.004", "T1584.005", "T1584.006", "T1584.007", "T1584.008"],
        "tactic": "resource development"
    },
    {
        "ids": ["T1189", "T1200", "T1195.001", "T1195.002", "T1195.003", "T1669"],
        "tactic": "initial access"
    },
    {
        "ids": ["T1651", "T1609", "T1675", "T1559.001", "T1559.002", "T1559.003", "T1677", "T1569.001", "T1569.002", "T1569.003"],
        "tactic": "execution"
    },
    {
        "ids": ["T1098", "T1098.001", "T1098.002", "T1098.003", "T1098.004", "T1098.005", "T1098.006", "T1098.007", "T1197", "T1671"],
        "tactic": "persistence"
    },
    {
        "ids": ["T1548", "T1548.001", "T1548.002", "T1548.003", "T1548.004", "T1548.005", "T1548.006", "T1484", "T1484.001", "T1484.002"],
        "tactic": "privilege escalation"
    },
    {
        "ids": ["T1548", "T1548.001", "T1548.002", "T1548.003", "T1548.004", "T1548.005", "T1548.006", "T1612", "T1610", "T1672"],
        "tactic": "defense evasion"
    },
    {
        "ids": ["T1557", "T1557.001", "T1557.002", "T1557.003", "T1557.004", "T1212", "T1187", "T1606.001", "T1606.002", "T1621"],
        "tactic": "credential access"
    },
    {
        "ids": ["T1087", "T1087.001", "T1087.002", "T1087.003", "T1087.004", "T1217", "T1580", "T1526", "T1482", "T1046"],
        "tactic": "discovery"
    },
    {
        "ids": ["T1210", "T1570", "T1563.001", "T1563.002", "T1091", "T1080", "T1550", "T1550.001", "T1550.002", "T1550.003", "T1550.004"],
        "tactic": "lateral movement"
    },
    {
        "ids": ["T1557", "T1557.001", "T1557.002", "T1557.003", "T1557.004", "T1123", "T1185", "T1602.001", "T1602.002", "T1005", "T1113"],
        "tactic": "collection"
    },
    {
        "ids": ["T1071", "T1071.001", "T1071.002", "T1071.003", "T1071.004", "T1071.005", "T1659", "T1568", "T1568.001", "T1568.002", "T1568.003"],
        "tactic": "command and control"
    },
    {
        "ids": ["T1020", "T1020.001", "T1011", "T1011.001", "T1567.001", "T1567.002", "T1567.003", "T1567.004", "T1537"],
        "tactic": "exfiltration"
    },
    {
        "ids": ["T1531", "T1486", "T1491.001", "T1491.002", "T1667", "T1495", "T1496", "T1496.001", "T1496.002", "T1496.003", "T1496.004"],
        "tactic": "impact"
    }
]


def create_random_threat_model_data(faker: Faker, threat_model_name: ThreatModelName) -> tuple[str, dict]:
    data = {}
    threat_threat_model_id = faker.word()
    if threat_model_name == ThreatModelName.attack:
        attack_item = random.choice(ATTACK_ITEMS)
        threat_threat_model_id = random.choice(attack_item["ids"])
        data["url"] = faker.url()
        data["version"] = "18"
        data["tactics"] = [attack_item["tactic"]]
    
    return threat_threat_model_id, data


def create_random_threat_model_item(db: Session, faker: Faker, threat_model_name: ThreatModelName | None = None, owner: schemas.User | None = None, create_extras: bool = True):
    if threat_model_name is None:
        threat_model_name = random.choice(list(ThreatModelName))

    if owner is None:
        owner = create_random_user(db, faker)

    threat_threat_model_id, data = create_random_threat_model_data(faker, threat_model_name)
    threat_model_item = crud.threat_model_item.create(db, obj_in=schemas.ThreatModelItemCreate(
        threat_model_name=threat_model_name,
        threat_model_id=threat_threat_model_id,
        title=faker.sentence(),
        description=faker.paragraph(),
        data=data,
        owner=owner.username
    ))

    if create_extras:
        crud.tag.assign_by_name(
            db,
            tag_name=f"{faker.word().lower()}_{faker.pyint()}",
            target_type=TargetTypeEnum.threat_model_item,
            target_id=threat_model_item.id,
            create=True,
            tag_description=faker.text(),
        )
        crud.source.assign_by_name(
            db,
            source_name=f"{faker.word().lower()}_{faker.pyint()}",
            target_type=TargetTypeEnum.threat_model_item,
            target_id=threat_model_item.id,
            create=True,
            source_description=faker.text(),
        )
        entry = create_random_entry(
            db,
            faker,
            owner,
            target_type=TargetTypeEnum.threat_model_item,
            target_id=threat_model_item.id,
            entry_class=EntryClassEnum.summary,
        )
        create_random_popularity(db, faker, TargetTypeEnum.entry, entry.id, owner=owner)
        create_random_user_links(db, faker, entry.id, TargetTypeEnum.entry, owner)
        parent = create_random_entry(
            db,
            faker,
            owner,
            target_type=TargetTypeEnum.threat_model_item,
            target_id=threat_model_item.id,
            entry_class=EntryClassEnum.entry,
        )
        create_random_popularity(db, faker, TargetTypeEnum.entry, parent.id, owner=owner)
        create_random_user_links(db, faker, parent.id, TargetTypeEnum.entry, owner)
        entry = create_random_entry(
            db,
            faker,
            owner,
            parent_entry_id=parent.id,
            target_type=TargetTypeEnum.threat_model_item,
            target_id=threat_model_item.id,
            entry_class=EntryClassEnum.entry,
        )
        create_random_popularity(db, faker, TargetTypeEnum.entry, entry.id, owner=owner)
        create_random_user_links(db, faker, entry.id, TargetTypeEnum.entry, owner)

    return threat_model_item