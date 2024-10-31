import os
import hashlib
import random
from faker import Faker
from sqlalchemy.orm import Session

from app.core.config import settings
from app import crud
from app.enums import TargetTypeEnum, TlpEnum
from app.schemas.file import FileCreate

try:
    from tests.utils.user import create_random_user
except ImportError:
    # needed to make initial_data.py function properly
    from user import create_random_user


def create_random_file(db: Session, faker: Faker, owner: str | None = None, target_enum: TargetTypeEnum | None = None, target_id: int | None = None):
    file_content = f"{faker.paragraph(nb_sentences=faker.pyint(max_value=100))}_{faker.pyint()}"
    file_hash = hashlib.sha256(file_content.encode("utf-8")).hexdigest()
    file_path = os.path.join(settings.FILE_STORAGE_LOCATION, file_hash)
    with open(file_path, "w") as f:
        f.write(file_content)

    if owner is None:
        owner = create_random_user(db, faker).username

    file_create = FileCreate(
        owner=owner,
        content_type=faker.mime_type(),
        filename=faker.file_name(),
        filesize=len(file_content),
        sha256=file_hash,
        file_pointer=file_hash,
        description=faker.sentence(),
        tlp=random.choice(list(TlpEnum))
    )

    if target_enum is None and target_id is None:
        return crud.file.create(db, obj_in=file_create)
    else:
        return crud.file.create_in_object(db, obj_in=file_create, source_type=target_enum, source_id=target_id)
