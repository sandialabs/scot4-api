import json
import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.schemas.signature import SignatureCreate


try:
    from tests.utils.user import create_random_user
except ImportError:
    # needed to make initial_data.py function properly
    from user import create_random_user


def create_random_signature(db: Session, faker: Faker, owner: str | None = None, signature_name: str | None = None):
    sig_type_titles = {
        "splunk": "title",
        "microsoft_sentinel": "displayName",
        "yara": "name",
        "snort": "msg",
    }
    data_formats = {
        "splunk": [
            "alert_action",
            "alert_comparator",
            "alert_condition",
            "alert_email_to",
            "cron_schedule",
            "is_scheduled",
            "owner",
            "search",
            "search_link",
            "start_time",
            "title",
            "updated",
        ],
        "microsoft_sentinel": [
            "alertRuleTemplateName",
            "displayName",
            "enabled",
            "etag",
            "id",
            "kind",
            "lastModifiedUtc",
            "name",
            "query",
            "queryFrequency",
            "queryPeriod",
            "resourceGroup",
            "severity",
            "suppressionDuration",
            "suppressionEnabled",
            "tactics",
            "triggerOperator",
            "triggerThreshold",
            "type",
        ],
        "yara": ["name", "create_date" "classifications", "strings", "condition"],
        "snort": [
            "snort_type" "protocol",
            "src_host",
            "src_port",
            "dest_host",
            "dest_port",
            "msg",
            "sid",
            "gid",
            "content",
            "depth",
            "rev",
            "classtype",
        ],
    }

    if owner is None:
        owner = create_random_user(db, faker).username

    signature_type_to_choose = random.choice(list(data_formats.keys()))
    signature_data = {
        x: faker.text(max_nb_chars=30) for x in data_formats[signature_type_to_choose]
    }
    signature_data["signature_group"] = [faker.word()]
    if signature_name is None:
        signature_name = signature_data[sig_type_titles[signature_type_to_choose]]

    signature_create = SignatureCreate(
        owner=owner,
        name=signature_name,
        description=faker.text(max_nb_chars=30),
        data=json.dumps(signature_data),
        type=signature_type_to_choose,
        status=random.choice(["enabled", "disabled"])
    )

    return crud.signature.create(db, obj_in=signature_create)
