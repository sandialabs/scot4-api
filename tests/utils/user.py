from typing import Union
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.models.role import Role
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def user_authentication_headers(
    *, client: TestClient, username: str, password: str
) -> dict[str, str]:
    data = {"username": username, "password": password}

    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=data)
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


def create_random_user(db: Session, faker: Faker, **kwargs) -> User:
    # add some numbers to the username part of the email just to make sure things are unique
    username, address = faker.safe_email().split("@")
    email = f"{username}_{faker.pyint()}@{address}"
    if "password" in kwargs.keys():
        user_in = UserCreate(username=email, email=email, **kwargs)
    else:
        password = faker.password()
        user_in = UserCreate(username=email, email=email, password=password, **kwargs)
    user = crud.user.create(db, obj_in=user_in)
    return user


def create_user_with_role(db: Session, role: Union[Role, list[Role]], faker: Faker) -> User:
    user = create_random_user(db, faker)
    if isinstance(role, list):
        for r in role:
            user.roles.append(r)
    else:
        user.roles.append(role)
    db.add(user)
    db.flush()
    db.refresh(user)
    return user


def authentication_token_from_username(
    *, client: TestClient, username: str, db: Session, faker: Faker
) -> dict[str, str]:
    """
    Return a valid token for the user with given email.

    If the user doesn't exist it is created first.
    """
    password = faker.password()
    user = crud.user.get_by_username(db, username=username)
    if not user:
        user_in_create = UserCreate(
            username=username, email=username, password=password
        )
        user = crud.user.create(db, obj_in=user_in_create)
    else:
        user_in_update = UserUpdate(password=password)
        user = crud.user.update(db, db_obj=user, obj_in=user_in_update)

    return user_authentication_headers(
        client=client, username=username, password=password
    )
