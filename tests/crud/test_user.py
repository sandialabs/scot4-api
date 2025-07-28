import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.auth import get_authenticator
from app.core.config import settings
from app.core.security import verify_password
from app.enums import AuthTypeEnum, PermissionEnum, TargetTypeEnum
from app.schemas.role import RoleCreate
from app.schemas.setting import AuthSettings, AuthSettingsUpdate
from app.schemas.user import UserCreate, UserUpdate
from app.api.deps import AuditLogger
from app.models import User

from tests.utils.user import create_random_user
from tests.utils.roles import create_random_role
from tests.utils.alertgroup import create_random_alertgroup_no_sig


def test_get_user(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker, is_superuser=True)

    db_obj = crud.user.get(db, user.id)

    assert db_obj is not None
    assert user.id == db_obj.id

    db_obj = crud.user.get(db, -1)

    assert db_obj is None


def test_get_multi_user(db: Session, faker: Faker) -> None:
    users = []
    for _ in range(5):
        users.append(create_random_user(db, faker))

    db_objs = crud.user.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == users[0].id for i in db_objs)

    db_objs = crud.user.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == users[1].id for i in db_objs)

    db_objs = crud.user.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.user.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_user(db: Session, faker: Faker) -> None:
    email = faker.safe_email()
    user_in = UserCreate(
        username=email,
        email=email,
        password=faker.password()
    )

    user = crud.user.create(db, obj_in=user_in)

    assert user.id is not None
    assert user.username == email
    assert user.email == email
    assert hasattr(user, "pw_hash")


def test_update_user(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)

    user_in_update = UserUpdate(
        password=faker.password(),
        is_superuser=True
    )

    db_obj = crud.user.update(db, db_obj=user, obj_in=user_in_update)

    assert db_obj
    assert user.id == db_obj.id
    assert db_obj.is_superuser is True
    assert verify_password(user_in_update.password, db_obj.pw_hash)

    update = {}

    db_obj = crud.user.update(db, db_obj=user, obj_in=update)

    assert db_obj.id == user.id

    update = {
        "test": "test"
    }

    db_obj = crud.user.update(db, db_obj=user, obj_in=update)

    assert db_obj.id == user.id
    assert not hasattr(db_obj, "test")

    email = faker.safe_email()
    update = {
        "username": email,
        "email": email,
        "fullname": faker.word(),
        "password": faker.password(),
    }

    db_obj = crud.user.update(db, db_obj=User(), obj_in=update)

    assert db_obj.id == user.id + 1
    assert db_obj.fullname == update["fullname"]


def test_remove_user(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)

    db_obj = crud.user.remove(db, _id=user.id)

    assert db_obj.id == user.id

    db_obj_del = crud.user.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.user.remove(db, _id=-1)

    assert db_obj is None


def test_query_with_filters_user(db: Session, faker: Faker) -> None:
    users = []
    for _ in range(5):
        users.append(create_random_user(db, faker))

    random_user = random.choice(users)

    db_obj, count = crud.user.query_with_filters(db, filter_dict={"id": random_user.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_user.id


def test_get_with_roles_user(db: Session, faker: Faker) -> None:
    users = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        email = faker.safe_email()
        user = UserCreate(
            username=email,
            email=email,
            password=faker.password()
        )
        roles.append(role)

        users.append(crud.user.create_with_permissions(db, obj_in=user, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.user.get_with_roles(db, [random_role])

    assert len(db_obj) == 0


def test_query_objects_with_roles_user(db: Session, faker: Faker) -> None:
    users = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        email = faker.safe_email()
        user = UserCreate(
            username=email,
            email=email,
            password=faker.password()
        )
        roles.append(role)

        users.append(crud.user.create_with_permissions(db, obj_in=user, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.user.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) == 0


def test_create_with_owner_user(db: Session, faker: Faker) -> None:
    email = faker.safe_email()
    user = UserCreate(
        username=email,
        email=email,
        password=faker.password()
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.user.create_with_owner(db, obj_in=user, owner=owner)

    assert db_obj is not None
    assert db_obj.username == user.username
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_user(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    email = faker.safe_email()
    user = UserCreate(
        username=email,
        email=email,
        password=faker.password()
    )

    db_obj = crud.user.create_with_permissions(db, obj_in=user, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.username == user.username
    assert db_obj.email == user.email


def test_get_history_user(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    email = faker.safe_email()
    user = UserCreate(
        username=email,
        email=email,
        password=faker.password()
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.user.create(db, obj_in=user, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.user.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_user(db: Session, faker: Faker) -> None:
    audit_user = create_random_user(db, faker)
    user = create_random_user(db, faker)
    audit_logger = AuditLogger(audit_user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.user.remove(db, _id=user.id, audit_logger=audit_logger)
    audit_logger.save_audits(db)

    assert db_obj.id == user.id

    db_obj = crud.user.undelete(db, db_obj.id)

    assert db_obj is not None
    assert db_obj.id == user.id

    db_obj = crud.user.get(db, db_obj.id)

    assert db_obj is not None
    assert db_obj.id == user.id


def test_get_by_username(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)

    db_obj = crud.user.get_by_username(db, username=user.username)

    assert db_obj is not None
    assert user.id == db_obj.id

    db_obj = crud.user.get_by_username(db, username="")

    assert db_obj is None


def test_bulk_get_by_usernames(db: Session, faker: Faker) -> None:
    # Test bulk getter
    user1 = create_random_user(db, faker)
    user2 = create_random_user(db, faker)
    fake_username = faker.safe_email()

    all_users = crud.user.bulk_get_by_usernames(
        db, username_list=[user1.username, fake_username, user2.username]
    )
    assert all_users[0].username == user1.username
    assert all_users[1] is None
    assert all_users[2].username == user2.username


def test_authenticate_user_local(db: Session, faker: Faker) -> None:
    password = faker.password()
    user = create_random_user(db, faker, password=password)

    authenticated_user = crud.user.authenticate(
        db, username=user.username, password=password, allowed_methods=[AuthTypeEnum.local]
    )

    assert authenticated_user
    assert user.username == authenticated_user.username


def test_authenticate_user_ldap(
    db: Session, faker: Faker, ldap_test_settings: AuthSettings, user_data: dict
) -> None:
    # Test login to existing user with existing role with ldap
    ldap_config = dict(ldap_test_settings.auth_properties)
    ldap_users = list(user_data.keys())
    local_password = faker.password()
    ldap_password_1 = user_data[ldap_users[0]]["userPassword"]

    user_in = UserCreate(username=ldap_users[0], password=local_password)
    user = crud.user.create(db, obj_in=user_in)
    crud.role.create(db, obj_in=RoleCreate(name="group1"))

    authenticated_user = crud.user.authenticate(
        db, username=ldap_users[0], password=ldap_password_1
    )

    assert authenticated_user
    assert authenticated_user.username == user.username
    assert len(authenticated_user.roles) == 1
    assert "group1" in [g.name for g in authenticated_user.roles]

    # Test creating users and roles when logging in with ldap
    ldap_password_2 = user_data[ldap_users[1]]["userPassword"]
    new_user = crud.user.authenticate(
        db, username=ldap_users[1], password=ldap_password_2
    )

    assert new_user
    assert new_user.username == ldap_users[1]
    assert new_user.email == user_data[ldap_users[1]]["email"]
    assert new_user.fullname == user_data[ldap_users[1]]["displayName"]
    assert len(new_user.roles) == 1
    assert "group2" in [g.name for g in new_user.roles]

    # Test user filter
    ldap_config["user_filter"] = "(uid=%s)" % ldap_users[0]
    update = AuthSettingsUpdate(auth_properties=ldap_config)
    crud.auth_setting.update_auth_method(db, ldap_test_settings.id, obj_in=update)
    user_2 = crud.user.authenticate(
        db, username=ldap_users[1], password=ldap_password_2
    )

    assert user_2 is None

    user_1 = crud.user.authenticate(
        db, username=ldap_users[0], password=ldap_password_1
    )

    assert user_1
    assert user_1.username == ldap_users[0]

    ldap_config["user_filter"] = None
    update = AuthSettingsUpdate(auth_properties=ldap_config)
    crud.auth_setting.update_auth_method(db, ldap_test_settings.id, obj_in=update)
    # Test group filter and removing roles from users
    ldap_password_3 = user_data[ldap_users[2]]["userPassword"]
    user_3 = crud.user.authenticate(
        db, username=ldap_users[2], password=ldap_password_3
    )

    assert user_3
    assert user_3.username == ldap_users[2]
    assert len(user_3.roles) == 2
    assert set([r.name for r in user_3.roles]) == set(["group1", "group2"])

    ldap_config["group_filter"] = "(cn=group1)"
    update = AuthSettingsUpdate(auth_properties=ldap_config)
    crud.auth_setting.update_auth_method(db, ldap_test_settings.id, obj_in=update)
    user_3 = crud.user.authenticate(
        db, username=ldap_users[2], password=ldap_password_3
    )

    assert user_3
    assert user_3.username == ldap_users[2]
    assert len(user_3.roles) == 1
    assert "group1" in [g.name for g in user_3.roles]

    # Test incorrect password
    user_3 = crud.user.authenticate(db, username=ldap_users[2], password="notapassword")

    assert user_3 is None

    # Test inactive auth
    update = AuthSettingsUpdate(auth_active=False)
    crud.auth_setting.update_auth_method(db, ldap_test_settings.id, obj_in=update)
    user_3 = crud.user.authenticate(
        db, username=ldap_users[2], password=ldap_password_3
    )

    assert user_3 is None


def test_authenticate_user_aad(
    db: Session,
    faker: Faker,
    user_data: dict,
    azuread_test_settings: AuthSettings,
    azuread_fake_auth_endpoint,
):
    # Test login to existing user with existing role with azuread
    aad_config = dict(azuread_test_settings.auth_properties)
    aad_users = list(user_data.keys())
    local_password = faker.password()
    UserCreate(username=aad_users[0], password=local_password)
    # user = crud.user.create(db, obj_in=user_in)
    # role = crud.role.create(db, obj_in=RoleCreate(name="group1"))
    authenticator = get_authenticator(azuread_test_settings)
    url = authenticator.start_external_authenticate()
    user_aad_token = azuread_fake_auth_endpoint(aad_users[0], url)

    authenticated_user = crud.user.authenticate(db, token=user_aad_token)

    assert authenticated_user
    assert authenticated_user.username == aad_users[0]
    assert len(authenticated_user.roles) == 1
    assert authenticated_user.roles[0].name == "group1"

    # Test creating users and roles when logging in with aad
    new_url = authenticator.start_external_authenticate()
    new_user_token = azuread_fake_auth_endpoint(aad_users[1], new_url)
    new_user = crud.user.authenticate(db, token=new_user_token)

    assert new_user
    assert new_user.username == aad_users[1]
    assert new_user.email == user_data[aad_users[1]]["email"]
    assert new_user.fullname == user_data[aad_users[1]]["displayName"]
    assert len(new_user.roles) == 1
    assert new_user.roles[0].name == "group2"

    # Test users needing specific role to log in
    new_aad_config = dict(aad_config)
    new_aad_config["access_roles"] = "group1"
    update = AuthSettingsUpdate(auth_properties=new_aad_config)
    crud.auth_setting.update_auth_method(db, azuread_test_settings.id, obj_in=update)
    authenticator = get_authenticator(azuread_test_settings)
    user_2_url = authenticator.start_external_authenticate()
    user_2_token = azuread_fake_auth_endpoint(aad_users[1], user_2_url)
    user_2 = crud.user.authenticate(db, token=user_2_token)

    assert user_2 is None

    user_1_url = authenticator.start_external_authenticate()
    user_1_token = azuread_fake_auth_endpoint(aad_users[0], user_1_url)
    user_1 = crud.user.authenticate(db, token=user_1_token)

    assert user_1
    assert user_1.username == aad_users[0]

    # Test inactive auth
    update = AuthSettingsUpdate(auth_active=False)
    crud.auth_setting.update_auth_method(db, azuread_test_settings.id, obj_in=update)
    user_1_url = authenticator.start_external_authenticate()
    user_1_token = azuread_fake_auth_endpoint(aad_users[0], user_1_url)
    user_1 = crud.user.authenticate(db, token=user_1_token)

    assert user_1 is None


def test_not_authenticate_user(db: Session, faker: Faker) -> None:
    email = faker.safe_email()
    password = faker.password()
    user = crud.user.authenticate(
        db, username=email, password=password, allowed_methods=[AuthTypeEnum.local]
    )

    assert user is None


def test_update_last_activity(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    last_date = user.last_activity

    crud.user.update_last_activity(db, user)

    db_obj = crud.user.get(db, user.id)

    assert db_obj is not None
    assert db_obj.last_activity != last_date


def test_reset_failed_attempts(db: Session, faker: Faker) -> None:
    password = faker.password()
    user = create_random_user(db, faker, password=password)

    for _ in range(settings.MAX_FAILED_PASSWORD_ATTEMPTS):
        bad_password = faker.word()
        auth_result = crud.user.authenticate(
            db,
            username=user.username,
            password=bad_password,
            allowed_methods=[AuthTypeEnum.local],
        )

        assert auth_result is None

    auth_result = crud.user.authenticate(db, username=user.username, password=password)

    assert not isinstance(auth_result, type(user))  # Exceeded retry attempts

    not_real_user = faker.safe_email()
    bad_reset_result = crud.user.reset_failed_attempts(db, not_real_user)

    assert bad_reset_result is None
    good_reset_result = crud.user.reset_failed_attempts(db, user.username)

    assert good_reset_result
    assert good_reset_result.username == user.username

    auth_result = crud.user.authenticate(
        db, username=user.username, password=password, allowed_methods=[AuthTypeEnum.local]
    )

    assert isinstance(auth_result, type(user))
    assert auth_result.username == user.username


def test_check_if_user_is_active(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker, is_active=True)

    assert crud.user.is_active(user) is True

    user = create_random_user(db, faker, is_active=False)

    assert crud.user.is_active(user) is False


def test_check_if_user_is_superuser(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker, is_superuser=True)

    assert crud.user.is_superuser(user) is True

    user = create_random_user(db, faker, is_superuser=False)

    assert crud.user.is_superuser(user) is False
