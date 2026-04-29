import argparse
import requests
import json
import re

from sqlalchemy.orm import Session
from sqlalchemy import Index

from app import crud, schemas
from app.core.config import settings
from app.core.logger import logger
from app.db import base
from app.models import EntityClass
from app.db.session import SessionLocal
from app.enums import AuthTypeEnum, PermissionEnum, TargetTypeEnum, StorageProviderEnum, ThreatModelName
from app.icons.flags import flags
from app.icons.default_icons import default_icons
from app.models import Entity, Link, Permission, Entry, Promotion, Audit, UserLinks, Popularity


def create_indices(db_session: Session):
    index = Index('permission_speedup_1', Permission.target_id, Permission.target_type, Permission.permission, Permission.role_id)
    index.create(bind=db_session.bind, checkfirst=True)
    index = Index('permission_speedup_2', Permission.permission, Permission.target_type, Permission.role_id, Permission.target_id)
    index.create(bind=db_session.bind, checkfirst=True)
    index = Index('permission_role_index', Permission.role_id)
    index.create(bind=db_session.bind, checkfirst=True)
    index = Index('link_speedup', Link.v0_id, Link.v1_type, Link.v0_type)
    index.create(bind=db_session.bind, checkfirst=True)
    index = Index('link_speedup_2', Link.v1_id, Link.v0_type, Link.v1_type)
    index.create(bind=db_session.bind, checkfirst=True)
    index = Index('link_speedup_3', Link.v0_type, Link.v0_id)
    index.create(bind=db_session.bind, checkfirst=True)
    index = Index('link_speedup_4', Link.v1_type, Link.v1_id)
    index.create(bind=db_session.bind, checkfirst=True)
    index = Index('entry_speedup', Entry.target_type, Entry.target_id)
    index.create(bind=db_session.bind, checkfirst=True)
    index = Index('promotion_speedup_1', Promotion.p0_id, Promotion.p0_type)
    index.create(bind=db_session.bind, checkfirst=True)
    index = Index('promotion_speedup_2', Promotion.p1_id, Promotion.p1_type)
    index.create(bind=db_session.bind, checkfirst=True)
    index = Index('entity_lookup', Entity.value, mysql_length=16)
    index.create(bind=db_session.bind, checkfirst=True)
    index = Index('enrichment_lookup', Entity.value, mysql_length=16)
    index.create(bind=db_session.bind)
    index = Index('audit_speedup_1', Audit.what, Audit.thing_type, mysql_length=16)
    index.create(bind=db_session.bind)
    index = Index('audit_speedup_2', Audit.thing_type, Audit.thing_id, mysql_length={'thing_type': 16})
    index.create(bind=db_session.bind)
    index = Index('audit_speedup_3', Audit.username, mysql_length=16)
    index.create(bind=db_session.bind)
    index = Index('audit_speedup_4', Audit.when_date)
    index.create(bind=db_session.bind)
    index = Index('user_links_speedup_1', UserLinks.target_type, UserLinks.target_id)
    index.create(bind=db_session.bind)
    index = Index('user_links_speedup_2', UserLinks.owner_id)
    index.create(bind=db_session.bind)
    index = Index('popularity_speedup_1', Popularity.target_type, Popularity.target_id)
    index.create(bind=db_session.bind)
    index = Index('popularity_speedup_2', Popularity.owner_id)
    index.create(bind=db_session.bind)


def init_db(db_session: Session, create_tables: bool = False, reset_db: bool = False, create_sql_indices=False):

    # if 'sqlite' in settings.SQLALCHEMY_DATABASE_URI:
    #     db_file = pathlib.Path(settings.SQLALCHEMY_DATABASE_URI)
    #     db_file.unlink(missing_ok=True)
    #     logger.info(f'Creating DB at: {db_file.absolute()}')

    # Create all the tables
    if reset_db is True:
        base.Base.metadata.drop_all(bind=db_session.bind)
    if create_tables or reset_db:
        base.Base.metadata.create_all(bind=db_session.bind)

    # Create the "everyone" role if it doesn't exist
    everyone_role = crud.role.get(db_session, settings.EVERYONE_ROLE_ID)

    if not everyone_role and (
        settings.EVERYONE_ROLE_ID >= 0 and settings.EVERYONE_ROLE_ID is not None
    ):
        everyone_role = crud.role.create(
            db_session=db_session,
            obj_in={"name": "everyone", "id": settings.EVERYONE_ROLE_ID},
        )
    # Create the admin role if it doesn't exist
    admin_role = crud.role.get_role_by_name(db_session, name="admin")
    if not admin_role:
        admin_role = crud.role.create(db_session=db_session, obj_in={"name": "admin"})
        admin_permission = schemas.PermissionCreate(
            role_id=admin_role.id,
            target_type=TargetTypeEnum.admin,
            target_id=0,
            permission=PermissionEnum.admin,
        )
        crud.permission.grant_permission(db_session, admin_permission)
        logger.info(f"Created {admin_role.name}")
    # Create default settings
    _setting = crud.setting.get(db_session)
    if not _setting:
        crud.setting.create(
            db_session=db_session,
            obj_in={
                "environment_level": "CUI//ISVI",
                "site_name": "",
                "it_contact": "scot-admin@sandia.gov",
            },
        )
    _auth_setting = crud.auth_setting.get(db_session, 1)
    if not _auth_setting:
        crud.auth_setting.create(
            db_session=db_session,
            obj_in={
                "auth_properties": {},
                "auth_active": True,
                "auth": AuthTypeEnum.local,
            },
        )
    # Create superuser if it doesn't exist
    user = crud.user.get_by_username(
        db_session, username=settings.FIRST_SUPERUSER_USERNAME
    )
    if not user:
        user_in = schemas.UserCreate(
            username=settings.FIRST_SUPERUSER_USERNAME,
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            fullname="SCOT-ADMIN",
            is_superuser=True,
        )
        user = crud.user.create(db_session, obj_in=user_in)
        user.roles.append(admin_role)
        db_session.add(user)
        logger.info(f"Created {user.username}")
    general_tag_create = schemas.TagTypeCreate(name="General", description="Generic/Default Tag Type")
    crud.tag_type.create(db_session=db_session, obj_in=general_tag_create)
    db_session.commit()

    if settings.FIRST_SUPERUSER_APIKEY != "":
        api_key = crud.apikey.get(db_session, settings.FIRST_SUPERUSER_APIKEY)
        if not api_key:
            first_user_flair_api_key = {"key": settings.FIRST_SUPERUSER_APIKEY, "owner": settings.FIRST_SUPERUSER_USERNAME, "active": True}
            crud.apikey.create(
                db_session=db_session,
                obj_in=first_user_flair_api_key)
            db_session.commit()

    if settings.CREATE_DEFAULT_STORAGE_PROVIDER:
        storage_setting = {"provider_name": "Local File System", "root_directory": settings.FILE_STORAGE_LOCATION, "deleted_items_directory": settings.FILE_DELETED_LOCATION}
        obj_in = schemas.StorageProviderSettingsCreate(provider=StorageProviderEnum.disk, config=storage_setting, enabled=True)

        storage_objs = crud.storage_setting.get_multi(db_session=db_session)
        if len(storage_objs) == 0:
            # Only re-create the default storage if no settings exist
            crud.storage_setting.create(
                db_session=db_session,
                new_storage_provider=obj_in)
            db_session.commit()

    if create_sql_indices:
        create_indices(db_session=db_session)
        db_session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize SCOT4 Database")
    parser.add_argument("--create_tables", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--reset_db", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--create_sql_indices", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--fix_tag_sources", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--add_mitre_attack", action=argparse.BooleanOptionalAction, default=False)
    args = parser.parse_args()

    db_session = SessionLocal()
    init_db(db_session, create_tables=args.create_tables, reset_db=args.reset_db, create_sql_indices=args.create_sql_indices)
    # readd in default flags/icons
    if args.reset_db:
        db_session.bulk_insert_mappings(EntityClass, flags)
        db_session.bulk_insert_mappings(EntityClass, default_icons)

    if args.fix_tag_sources:
        for tag in crud.tag.get_multi(db_session):
            if tag.name.strip() == "":
                crud.tag.remove(db_session, tag.id)
            elif " " in tag.name:
                new_name = tag.name.replace(" ", "_")
                new_tag = crud.tag.get_by_name(db_session, new_name)
                if new_tag is not None:
                    for link in crud.link.find_all_links(db_session, TargetTypeEnum.tag, tag.id):
                        update = {}
                        if link.v0_type == TargetTypeEnum.tag and link.v0_id == tag.id:
                            update["v0_id"] = new_tag.id
                        elif link.v1_type == TargetTypeEnum.tag and link.v1_id == tag.id:
                            update["v1_id"] = new_tag.id
                        crud.link.update(db_session, db_obj=link, obj_in=update)
                    crud.tag.remove(db_session, tag.id)
                else:
                    crud.tag.update(db_session, db_obj=tag, obj_in={"name": new_name})

        for source in crud.source.get_multi(db_session):
            if source.name.strip() == "":
                crud.source.remove(db_session, source.id)
            elif " " in source.name:
                new_name = source.name.replace(" ", "_")
                new_source = crud.source.get_by_name(db_session, new_name)
                if new_source is not None:
                    for link in crud.link.find_all_links(db_session, TargetTypeEnum.source, source.id):
                        update = {}
                        if link.v0_type == TargetTypeEnum.source and link.v0_id == source.id:
                            update["v0_id"] = new_source.id
                        elif link.v1_type == TargetTypeEnum.source and link.v1_id == source.id:
                            update["v1_id"] = new_source.id
                        crud.link.update(db_session, db_obj=link, obj_in=update)
                    crud.source.remove(db_session, source.id)
                else:
                    crud.source.update(db_session, db_obj=source, obj_in={"name": new_name})

    if args.add_mitre_attack:
        r = requests.get(f"https://github.com/mitre/cti/releases/download/ATT&CK-{settings.MITRE_VERSION}/enterprise-attack.json", verify=False, timeout=60)  # nosec: B501
        if r.status_code == 200:
            mitre_data = json.loads(r.text)
            for obj in mitre_data["objects"]:
                threat_model_id = ""
                url = ""
                tactics = []

                for external_reference in obj.get("external_references", []):
                    if external_reference.get("source_name", "") == "mitre-attack" and re.match(r"^T\d{4}\.\d{3}$|^T\d{4}$", external_reference.get("external_id", "")):
                        threat_model_id = external_reference["external_id"]
                        url = external_reference["url"]
                        break

                for kill_chain_phase in obj.get("kill_chain_phases", []):
                    if kill_chain_phase.get("kill_chain_name", "") == "mitre-attack":
                        tactics.append(kill_chain_phase["phase_name"])

                if threat_model_id != "" and len(tactics) > 0:
                    crud.threat_model_item.create(db_session=db_session, obj_in=schemas.ThreatModelItemCreate(
                        threat_model_name=ThreatModelName.attack,
                        threat_model_id=threat_model_id,
                        title=obj.get("name"),
                        description=obj.get("description"),
                        data={
                            "url": url,
                            "tactics": tactics,
                            "id": obj.get("id"),
                            "version": settings.MITRE_VERSION
                        }
                    ))
        else:
            print(f"failed to download mitre data {r.status_code} - {r.text}")

    db_session.commit()
