import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud, schemas
from app.enums import TargetTypeEnum, UserLinkEnum
from app.schemas.user_links import UserLinksCreate

try:
    from tests.utils.alert import create_random_alert
    from tests.utils.user import create_random_user
except ImportError:
    # needed to make initial_data.py function properly
    from alert import create_random_alert
    from user import create_random_user


def create_random_user_links(db: Session, faker: Faker, target_id: int | None = None, target_type: TargetTypeEnum | None = None, owner: schemas.User | None = None):
    if target_id is None:
        target_id = create_random_alert(db, faker).id
        target_type = TargetTypeEnum.alert
    
    if owner is None:
        owner = create_random_user(db, faker)

    user_link = UserLinksCreate(
        link_type=random.choice(list(UserLinkEnum)),
        target_id=target_id,
        target_type=target_type,
        owner_id=owner.id
    )

    return crud.user_links.create(db, obj_in=user_link)
