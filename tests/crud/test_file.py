import random
import os
from faker import Faker
from sqlalchemy.orm import Session
from streaming_form_data.targets import FileTarget

from app import crud
from app.core.config import settings
from app.object_storage.disk import DiskStorageProvider
from app.api.deps import AuditLogger
from app.enums import TlpEnum, PermissionEnum, TargetTypeEnum
from app.models import File
from app.schemas.file import FileCreate, FileUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.file import create_random_file
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user, create_user_with_role
from tests.utils.settings import reset_storage_settings


def test_get_file(db: Session, faker: Faker) -> None:
    file = create_random_file(db, faker)
    db_obj = crud.file.get(db, file.id)

    assert db_obj.id == file.id

    db_obj = crud.file.get(db, -1)

    assert db_obj is None


def test_get_multi_file(db: Session, faker: Faker) -> None:
    files = []
    for _ in range(5):
        files.append(create_random_file(db, faker))

    db_objs = crud.file.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == files[0].id for i in db_objs)

    db_objs = crud.file.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == files[1].id for i in db_objs)

    db_objs = crud.file.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.file.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_file(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    file = FileCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        file_pointer=faker.uuid4(),
        filename=faker.file_name(),
        filesize=faker.pyint(),
        sha256=faker.sha256(),
        description=faker.sentence(),
        content_type=faker.mime_type()
    )
    db_obj = crud.file.create(db, obj_in=file)

    assert db_obj.id is not None
    assert db_obj.owner == file.owner
    assert db_obj.tlp == file.tlp
    assert db_obj.file_pointer == file.file_pointer
    assert db_obj.filename == file.filename
    assert db_obj.filesize == file.filesize
    assert db_obj.sha256 == file.sha256
    assert db_obj.description == file.description
    assert db_obj.content_type == file.content_type


def test_update_file(db: Session, faker: Faker) -> None:
    file = create_random_file(db, faker)
    owner = create_random_user(db, faker)
    update = FileUpdate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        file_pointer=faker.uuid4(),
        filename=faker.file_name(),
        filesize=faker.pyint(),
        sha256=faker.sha256(),
        description=faker.sentence(),
        content_type=faker.mime_type()
    )

    db_obj = crud.file.update(db, db_obj=file, obj_in=update)

    assert db_obj.id == file.id
    assert db_obj.owner == update.owner
    assert db_obj.tlp == update.tlp
    assert db_obj.file_pointer == update.file_pointer
    assert db_obj.filename == update.filename
    assert db_obj.filesize == update.filesize
    assert db_obj.sha256 == update.sha256
    assert db_obj.description == update.description
    assert db_obj.content_type == update.content_type

    update = {}

    db_obj = crud.file.update(db, db_obj=file, obj_in=update)

    assert db_obj.id == file.id

    update = {
        "test": "test"
    }

    db_obj = crud.file.update(db, db_obj=file, obj_in=update)

    assert db_obj.id == file.id
    assert not hasattr(db_obj, "test")

    owner = create_random_user(db, faker)
    update = {
        "owner": owner.username,
        "tlp": random.choice(list(TlpEnum)),
        "file_pointer": faker.uuid4(),
        "filename": faker.file_name(),
        "filesize": faker.pyint(),
        "sha256": faker.sha256(),
        "description": faker.sentence(),
        "content_type": faker.mime_type()
    }

    db_obj = crud.file.update(db, db_obj=File(), obj_in=update)

    assert db_obj.id == file.id + 1
    assert db_obj.owner == update["owner"]
    assert db_obj.file_pointer == update["file_pointer"]
    assert db_obj.filename == update["filename"]
    assert db_obj.filesize == update["filesize"]
    assert db_obj.sha256 == update["sha256"]
    assert db_obj.description == update["description"]
    assert db_obj.content_type == update["content_type"]


def test_remove_file(db: Session, faker: Faker) -> None:
    reset_storage_settings(db)
    file = create_random_file(db, faker)

    db_obj = crud.file.remove_file(db, file_id=file.id)

    assert db_obj.id == file.id

    db_obj_del = crud.file.get(db, _id=db_obj.id)

    assert db_obj_del is None
    assert os.path.exists(os.path.join(settings.FILE_DELETED_LOCATION, db_obj.file_pointer))
    assert not os.path.exists(os.path.join(settings.FILE_STORAGE_LOCATION, db_obj.file_pointer))

    db_obj = crud.file.remove_file(db, file_id=-1)

    assert db_obj is None


def test_get_or_create_file(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    file = FileCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        file_pointer=faker.uuid4(),
        filename=faker.file_name(),
        filesize=faker.pyint(),
        sha256=faker.sha256(),
        description=faker.sentence(),
        content_type=faker.mime_type()
    )

    db_obj = crud.file.get_or_create(db, obj_in=file)

    assert db_obj.id is not None

    same_db_obj = crud.file.get_or_create(db, obj_in=file)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_file(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    files = []
    for _ in range(5):
        files.append(create_random_file(db, faker, owner))

    random_file = random.choice(files)

    db_obj, count = crud.file.query_with_filters(db, filter_dict={"id": random_file.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_file.id

    db_obj, count = crud.file.query_with_filters(db, filter_dict={"owner": owner.username})

    assert db_obj is not None
    assert len(db_obj) == len(files)
    assert len(db_obj) == count
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.file.query_with_filters(db, filter_dict={"owner": owner.username}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == len(files) - 1
    assert len(db_obj) == count - 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.file.query_with_filters(db, filter_dict={"owner": owner.username}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert all(a.owner == owner.username for a in db_obj)

    filename = f"*{random_file.filename[1:-1]}_"
    db_obj, count = crud.file.query_with_filters(db, filter_dict={"glob": filename})

    assert db_obj is not None
    assert len(db_obj) >= 1
    assert count >= 1
    assert any(i.id == random_file.id for i in db_obj)

    filename = f"*{random_file.filename[1:-1]}_"
    db_obj, count = crud.file.query_with_filters(db, filter_dict={"glob": f"!{filename}"})

    assert db_obj is not None
    assert all(a.filename != random_file.filename for a in db_obj)

    db_obj, count = crud.file.query_with_filters(db, filter_dict={"sha256": [random_file.sha256]})

    assert db_obj is not None
    assert len(db_obj) >= 1
    assert count >= 1
    assert any(i.id == random_file.id for i in db_obj)

    db_obj, count = crud.file.query_with_filters(db, filter_dict={"sha256": f"!{random_file.sha256}"})

    assert db_obj is not None
    assert all(a.sha256 != random_file.sha256 for a in db_obj)

    db_obj, count = crud.file.query_with_filters(db, filter_dict={"description": random_file.description})

    assert db_obj is not None
    assert len(db_obj) >= 1
    assert count >= 1
    assert any(i.id == random_file.id for i in db_obj)

    db_obj, count = crud.file.query_with_filters(db, filter_dict={"description": f"!{random_file.description}"})

    assert db_obj is not None
    assert all(a.description != random_file.description for a in db_obj)


def test_get_with_roles_file(db: Session, faker: Faker) -> None:
    files = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        file = FileCreate(
            owner=owner.username,
            tlp=random.choice(list(TlpEnum)),
            file_pointer=faker.uuid4(),
            filename=faker.file_name(),
            filesize=faker.pyint(),
            sha256=faker.sha256(),
            description=faker.sentence(),
            content_type=faker.mime_type()
        )
        roles.append(role)

        files.append(crud.file.create_with_permissions(db, obj_in=file, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.file.get_with_roles(db, [random_role])

    assert len(db_obj) >= 1


def test_query_objects_with_roles_file(db: Session, faker: Faker) -> None:
    files = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        file = FileCreate(
            owner=owner.username,
            tlp=random.choice(list(TlpEnum)),
            file_pointer=faker.uuid4(),
            filename=faker.file_name(),
            filesize=faker.pyint(),
            sha256=faker.sha256(),
            description=faker.sentence(),
            content_type=faker.mime_type()
        )
        roles.append(role)

        files.append(crud.file.create_with_permissions(db, obj_in=file, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.file.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) >= 1


def test_create_with_owner_file(db: Session, faker: Faker) -> None:
    file = FileCreate(
        tlp=random.choice(list(TlpEnum)),
        file_pointer=faker.uuid4(),
        filename=faker.file_name(),
        filesize=faker.pyint(),
        sha256=faker.sha256(),
        description=faker.sentence(),
        content_type=faker.mime_type()
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.file.create_with_owner(db, obj_in=file, owner=owner)

    assert db_obj is not None
    assert db_obj.file_pointer == file.file_pointer
    assert hasattr(db_obj, "owner")
    assert db_obj.owner == owner.username


def test_create_with_permissions_file(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, [role], faker)
    file = FileCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        file_pointer=faker.uuid4(),
        filename=faker.file_name(),
        filesize=faker.pyint(),
        sha256=faker.sha256(),
        description=faker.sentence(),
        content_type=faker.mime_type()
    )

    db_obj = crud.file.create_with_permissions(db, obj_in=file, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.owner == file.owner
    assert db_obj.tlp == file.tlp
    assert db_obj.file_pointer == file.file_pointer
    assert db_obj.filename == file.filename
    assert db_obj.filesize == file.filesize
    assert db_obj.sha256 == file.sha256
    assert db_obj.description == file.description
    assert db_obj.content_type == file.content_type

    permission = crud.permission.get_permissions_from_roles(db, [role], TargetTypeEnum.file, db_obj.id)

    assert len(permission) == 1
    assert permission[0] == PermissionEnum.read


def test_create_in_object_file(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    file = FileCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        file_pointer=faker.uuid4(),
        filename=faker.file_name(),
        filesize=faker.pyint(),
        sha256=faker.sha256(),
        description=faker.sentence(),
        content_type=faker.mime_type()
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.file.create_in_object(db, obj_in=file, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.file_pointer == file.file_pointer

    link, _ = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v1_id": db_obj.id})

    assert any(i.v0_id == alert_group.id for i in link)
    assert any(i.v1_id == db_obj.id for i in link)


def test_get_history_file(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    file = FileCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        file_pointer=faker.uuid4(),
        filename=faker.file_name(),
        filesize=faker.pyint(),
        sha256=faker.sha256(),
        description=faker.sentence(),
        content_type=faker.mime_type()
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.file.create(db, obj_in=file, audit_logger=audit_logger)
    audit_logger.save_audits()

    assert db_obj is not None

    db_history = crud.file.get_history(db, db_obj.id)

    assert len(db_history) == 1
    assert db_history[0].what == "create"
    assert db_history[0].thing_id == db_obj.id


def test_undelete_file(db: Session, faker: Faker) -> None:
    reset_storage_settings(db)
    user = create_random_user(db, faker)
    file = create_random_file(db, faker, user)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.file.remove_file(db, file_id=file.id, audit_logger=audit_logger)
    audit_logger.save_audits()

    assert db_obj.id == file.id

    undelete_db_obj = crud.file.unremove_file(db, file_id=db_obj.id, by_user=user.username)

    assert undelete_db_obj is not None
    assert os.path.exists(os.path.join(settings.FILE_STORAGE_LOCATION, undelete_db_obj.file_pointer))
    assert not os.path.exists(os.path.join(settings.FILE_DELETED_LOCATION, undelete_db_obj.file_pointer))


def test_get_storage_provider(db: Session) -> None:
    reset_storage_settings(db)
    sp = crud.file.get_storage_provider(db)

    assert sp is not None
    assert isinstance(sp, DiskStorageProvider)
    assert hasattr(sp, "deleted_items_folder")
    assert sp.deleted_items_folder == settings.FILE_DELETED_LOCATION
    assert hasattr(sp, "root_directory")
    assert sp.root_directory == settings.FILE_STORAGE_LOCATION


def test_get_storage_target(db: Session, faker: Faker) -> None:
    reset_storage_settings(db)
    file = create_random_file(db, faker)

    st = crud.file.get_storage_target(db, file.file_pointer)

    assert st is not None
    assert isinstance(st, FileTarget)


def test_retrieve_element_files(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alertgroup = create_random_alertgroup_no_sig(db, faker, user, False)
    file = create_random_file(db, faker, user, TargetTypeEnum.alertgroup, alertgroup.id)

    db_obj, count = crud.file.retrieve_element_files(db, alertgroup.id, TargetTypeEnum.alertgroup)

    assert len(db_obj) == 1
    assert count == 1
    assert db_obj[0].id == file.id


def test_get_content_files(db: Session, faker: Faker) -> None:
    reset_storage_settings(db)
    file = create_random_file(db, faker)

    content = crud.file.get_content(db, file)

    assert content is not None

    file_content = open(os.path.join(settings.FILE_STORAGE_LOCATION, file.file_pointer), "rb").read()
    db_content = content.read()

    assert db_content == file_content


def test_move_file_location(db: Session, faker: Faker) -> None:
    reset_storage_settings(db)
    file = create_random_file(db, faker)

    crud.file.move_file_to_deleted_location(db, file.file_pointer)

    assert not os.path.exists(os.path.join(settings.FILE_STORAGE_LOCATION, file.file_pointer))
    assert os.path.exists(os.path.join(settings.FILE_DELETED_LOCATION, file.file_pointer))

    crud.file.move_file_to_default_location(db, file.file_pointer)

    assert os.path.exists(os.path.join(settings.FILE_STORAGE_LOCATION, file.file_pointer))
    assert not os.path.exists(os.path.join(settings.FILE_DELETED_LOCATION, file.file_pointer))
