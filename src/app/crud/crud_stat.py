from app.crud.base import CRUDBase
from app.models.stat import Stat
from app.schemas.stat import StatCreate, StatUpdate


class CRUDStat(CRUDBase[Stat, StatCreate, StatUpdate]):
    pass


stat = CRUDStat(Stat)
