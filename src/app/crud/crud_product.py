from app.enums import TargetTypeEnum
from app.crud.base import CRUDBase
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):
    # Custom filtering for products
    def filter(self, query, filter_dict):
        query = self._str_filter(query, filter_dict, "subject")
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.tag)
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.source)
        query = self._promoted_to_or_from_filter(query, filter_dict, "from")

        return super().filter(query, filter_dict)


product = CRUDProduct(Product)
