from app.crud.base import CRUDBase
from app.enums import TargetTypeEnum
from app.models.checklist import Checklist
from app.schemas.checklist import ChecklistCreate, ChecklistUpdate


class CRUDChecklist(CRUDBase[Checklist, ChecklistCreate, ChecklistUpdate]):
    def filter(self, query, filter_dict):
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.tag)
        query = self._str_filter(query, filter_dict, "subject")

        return super().filter(query, filter_dict)


checklist = CRUDChecklist(Checklist)
