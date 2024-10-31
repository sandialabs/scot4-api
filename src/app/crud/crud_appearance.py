from app.crud.base import CRUDBase
from app.models.appearance import Appearance
from app.schemas.appearance import AppearanceCreate, AppearanceUpdate


class CRUDAppearance(CRUDBase[Appearance, AppearanceCreate, AppearanceUpdate]):
    # Custom filtering for appearances
    def filter(self, query, filter_dict):
        query = self._str_filter(query, filter_dict, "value_str")

        return super().filter(query, filter_dict)


appearance = CRUDAppearance(Appearance)
