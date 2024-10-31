from app.crud.base import CRUDBase
from app.models.tag_type import TagType
from app.schemas.tag_type import TagTypeCreate, TagTypeUpdate


class CRUDTagType(CRUDBase[TagType, TagTypeCreate, TagTypeUpdate]):
    pass


tag_type = CRUDTagType(TagType)
