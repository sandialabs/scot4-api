import meilisearch

from app import models
from app.utils import index_for_search
from app.crud.base import CRUDBase
from app.db.session import SessionLocal
from app.core.config import settings


def index_search_results():
    # connect to meilisearch instance
    client = meilisearch.Client(settings.SEARCH_HOST, settings.SEARCH_API_KEY)
    session = SessionLocal()
    try:
        # delete existing index
        client.delete_index('entries')
    except Exception:
        pass

    # create index
    client.create_index('entries', {'primaryKey': 'entry_id'})
    client.index('entries').update_settings({'searchableAttributes': ['entry_text', 'parent_text']})
    # add alert data to be indexed as well, batch_size at time to not hog too much memory
    batch_size = 10000
    alert_offset = 0
    while True:
        alerts = session.query(models.Alert).limit(batch_size).offset(alert_offset).all()
        if not alerts:
            break
        for alert in alerts:
            if alert is not None and alert.get('data') is not None:
                index_for_search(alert.alertgroup_subject, alert=alert)
        
        alert_offset += batch_size

    # index all entries
    entry_offset = 0
    while True:
        entries = session.query(models.Entry).limit(batch_size).offset(entry_offset).all()
        if not entries:
            break
        for entry in entries:
            if entry is not None and entry.get('entry_data') is not None and entry.entry_data.get('html') is not None:
                if entry.entry_data.get('plain_text') is None: 
                    continue
                parent_crud = CRUDBase.target_crud_mapping.get(entry.target_type)
                if parent_crud is not None:
                    parent_obj = parent_crud.get(db_session=session, _id=entry.target_id)
                    if hasattr(parent_obj, "subject"):
                        index_for_search(parent_obj.subject, entry)
                    elif hasattr(parent_obj, "title"):
                        index_for_search(parent_obj.title, entry)
                    elif hasattr(parent_obj, "value"):
                        index_for_search(parent_obj.value, entry)
                    elif hasattr(parent_obj, "name"):
                        index_for_search(parent_obj.name, entry)
        
        entry_offset += batch_size


if __name__ == "__main__":
    index_search_results()
