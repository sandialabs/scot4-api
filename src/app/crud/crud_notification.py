from app.crud.base import CRUDBase
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationUpdate


class CRUDNotification(CRUDBase[Notification, NotificationCreate, NotificationUpdate]):
    pass


notification = CRUDNotification(Notification)
