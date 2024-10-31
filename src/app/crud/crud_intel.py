from app.enums import TargetTypeEnum
from app.crud.base import CRUDBase
from app.models.intel import Intel
from app.schemas.intel import IntelCreate, IntelUpdate


class CRUDIntel(CRUDBase[Intel, IntelCreate, IntelUpdate]):
    # Custom filtering for intel
    def filter(self, query, filter_dict):
        query = self._str_filter(query, filter_dict, "subject")
        query = self._promoted_to_or_from_filter(query, filter_dict, "to")
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.tag)
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.source)

        return super().filter(query, filter_dict)


intel = CRUDIntel(Intel)
