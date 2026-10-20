from app import crud
from app.schemas.alert import AlertCreate, AlertDataCreate, AlertAdd
from app.schemas import AlertGroupDetailedCreate
from app.core.logger import logger
from app.enums import TargetTypeEnum
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models import EntityType, Entity, AlertGroup, Event, Pivot
from app.schemas.source import SourceCreate
from app.schemas.tag import TagCreate
from app.schemas.entity_type import EntityTypeCreate
from app.schemas.entity import EntityCreate
from app.schemas.flair import FlairResults, FlairedEntity, FlairedTarget
import requests
import os
from pymongo import MongoClient
import json
import traceback
from datetime import datetime
import tqdm
import pprint
from multiprocessing import Pool

def main(db_session):
    entity_type_lookup = {x.name:x.id for x in db_session.query(EntityType).all()}

    ip_pivots = [
    {"title": "Robtex", "template": "https://robtex.com/ip/{{entity}}.html",
    "description": "This pivot will take you to Robtex for the supplied IP.", "entity_type_id":entity_type_lookup['ipaddr']}
    ]

    domain_pivots = [
    {"title": "Robtex", "template": "https://robtex.com/dns/{{entity}}.html",
    "description": "This pivot will take you to Robtex for the supplied IP.", "entity_type_id":entity_type_lookup['domain']}
    ]

    bulk_array = []
    bulk_array.extend(domain_pivots)
    bulk_array.extend(ip_pivots)
    db_session.bulk_insert_mappings(Pivot, bulk_array)
    db_session.commit()
    bulk_array.clear()

    
if __name__ == "__main__":
    main()
