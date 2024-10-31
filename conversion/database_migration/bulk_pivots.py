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
    {"title": "Scanner Dashboard", "template": "https://splunkit.sandia.gov/en-US/app/cyber/jcj_what_scanner_am_i?theme=dark&form.field1.earliest=-24h%40h&form.field1.latest=now&form.this={{entity}}",
    "description": "This pivot will take you to John Jarocki's 'What Scanner Am I?' Dashboard in Splunk, which will give several extremely helpful enrichments and pivots regarding the IP.", "entity_type_id":entity_type_lookup['ipaddr']}
    ,
     {"title": "ICK Lookup", "template": "https://ick.sandia.gov/ipaddress/details?id={{entity}}",
    "description": "This pivot will take you to Sandia's internal Ifrastructure Computing Kit site which contains IT asset information for machines, DNS records, and IP addresses", "entity_type_id":entity_type_lookup['ipaddr']}
    ,
    
    {"title": "LRI Pivot", "template": "https://lri.sandia.gov/search?id={{entity}}",
    "description": "This pivot will take you to the Long Range Indexes site, which allows analysts to quickly query indicators and retrieve the log source(s) and date(s) for which that indicator was seen past normal data retention periods in splunk. ", "entity_type_id":entity_type_lookup['ipaddr']}
    
    ]

    domain_pivots = [
    {"title": "Splunk VT", "template": "https://splunkit.sandia.gov/en-US/app/cyber/search?q=search%20%60vt%60%20attributes.url=*{{entity}}*|`table_vt3_url`&display.page.search.mode=smart&dispatch.sample_ratio=1&earliest=-30d%40d&latest=now&display.page.search.tab=events&display.general.type=events",
    "description": "This pivot will show you the historical virus total queries for this uri from our internal VT collection, this is preferred over querying VT directly for opsec purposes.", "entity_type_id":entity_type_lookup['domain'] }
    ,
     {"title": "Open Silo", "template": "https://a8silo.com/launch",
    "description": "This pivot will take you tite which contains IT asset information for machines, DNS records, and IP addresses", "entity_type_id":entity_type_lookup['domain']}
    ]

    clsid_pivots = [
    {"title": "Search Azure AD App ID", "template": "https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Overview/appId/{{entity}}",
    "description": "If this is an Azure Application ID, pivot to the Azure Active Directory blade to view the application properties.", "entity_type_id":entity_type_lookup['clsid'] }
    ,
    ]

    uuid_pivots = [
    {"title": "Lookup in Laikaboss", "template": "https://lb.sandia.gov/search/{{entity}}",
    "description": "If this is a laikaboss ID, pivot to the Laikaboss GUI to view details on this scanned object (most likely email).", "entity_type_id":entity_type_lookup['uuid1'] }
    ,
    {"title": "Lookup in VMRay", "template": "https://vmray.sandia.gov/submissions?field_1=tag&operator_1=%3D%3D&value_1={{entity}}&search=advanced",
    "description": "If this is a laikaboss ID, pivot to the VMRay GUI to view details on dynamic and/or static analysis of this object (most likely email).", "entity_type_id":entity_type_lookup['uuid1'] }
    
    ]

    email_pivots = [
    {"title": "LRI Pivot", "template": "https://lri.sandia.gov/search?id={{entity}}",
    "description": "This pivot will take you to the Long Range Indexes site, which allows analysts to quickly query indicators and retrieve the log source(s) and date(s) for which that indicator was seen past normal data retention periods in splunk. ", "entity_type_id":entity_type_lookup['email']}
    ]

    bulk_array = []
    bulk_array.extend(uuid_pivots)
    bulk_array.extend(clsid_pivots)
    bulk_array.extend(domain_pivots)
    bulk_array.extend(ip_pivots)
    bulk_array.extend(email_pivots)
    db_session.bulk_insert_mappings(Pivot, bulk_array)
    db_session.commit()
    bulk_array.clear()

    
if __name__ == "__main__":
    main()
