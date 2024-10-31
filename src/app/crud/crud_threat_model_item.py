from app.enums import TargetTypeEnum
from app.crud.base import CRUDBase
from app.models.threat_model_item import ThreatModelItem
from app.schemas.threat_model_item import ThreatModelItemCreate


class CRUDThreatModelItem(
    CRUDBase[ThreatModelItem, ThreatModelItemCreate, ThreatModelItemCreate]
):
    def filter(self, query, filter_dict):
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.tag)
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.source)

        return super().filter(query, filter_dict)


threat_model_item = CRUDThreatModelItem(ThreatModelItem)
