import re
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.db.base_class import Base
from app.models.notification import Notification
from app.models.user_links import UserLinks
from app.models.user import User
from app.enums import TargetTypeEnum, PriorityEnum, UserLinkEnum
from app.schemas.notification import NotificationCreate, NotificationUpdate

HTML_REMOVE_TAGS = re.compile("<.*?>")


class CRUDNotification(CRUDBase[Notification, NotificationCreate, NotificationUpdate]):
    def get_subscribed_users(self, db_session: Session, target_type: TargetTypeEnum, target_id: int):
        query = db_session.query(User).join(UserLinks).filter(
            (UserLinks.link_type == UserLinkEnum.subscription)
            & (target_type == UserLinks.target_type)
            & (target_id == UserLinks.target_id)
        )
        return query.all()

    def get_notifications_for_user(
        self,
        db_session: Session,
        user_id: int,
        limit: int = 100,
        skip: int = 0,
        include_acked: bool = False
    ):
        query = db_session.query(Notification).filter(
            (Notification.user_id == user_id)
            & ((Notification.expires > datetime.now(timezone.utc))
                | (Notification.expires.is_(None)))
        )
        if not include_acked:
            query = query.filter(Notification.ack.is_(False))
        count = self.get_count_from_query(query)
        # Get high priority notifications first if we're only getting unread
        # Otherwise, just get them all in order of creation
        if not include_acked:
            query = query.order_by(
                Notification.priority, Notification.created.desc()
            )
        else:
            query = query.order_by(Notification.created.desc())
        notifications = query.offset(skip).limit(limit).all()
        return notifications, count

    def ack_notifications(
        self,
        db_session: Session,
        notification_ids: list[int],
        user_id: int,
        audit_logger=None
    ):
        updated = []
        for notification_id in notification_ids:
            notification_db = self.get(db_session=db_session, _id=notification_id)
            if not notification_db or notification_db.user_id != user_id:
                raise ValueError(f"Notification {notification_id} not found")
            if not notification_db.ack:
                obj_in = NotificationUpdate(ack=True)
                self.update(
                    db_session=db_session, db_obj=notification_db, obj_in=obj_in
                )
                updated.append(notification_id)
                if audit_logger is not None:
                    audit_logger.log(
                        'update', {'ack': True},
                        thing_type='notification',
                        thing_pk=notification_id
                    )
        db_session.flush()
        return updated

    def broadcast_notification(
        self,
        db_session: Session,
        message: str,
        priority: PriorityEnum = PriorityEnum.medium,
        expires: datetime | None = None
    ) -> Notification:
        """
        Sends a notification to all users
        """
        limit = 100
        skip = 0
        users = db_session.query(User).limit(limit).all()
        while len(users) > 0:
            for user in users:
                notification_create = NotificationCreate(
                    user_id=user.id, message=message, priority=priority,
                    expires=expires, ref_id="broadcast"
                )
                # This is a little slow, but this probably won't get called much
                self.create(db_session, obj_in=notification_create)
            if len(users) < limit:
                break
            skip += limit
            users = db_session.query(User).offset(skip).limit(limit).all()

    def ellipsis_message(self, message: str, length: int = 128) -> str:
        if len(message) > length:
            message = message[:length - 3] + "..."
        return message

    def send_create_notifications(
        self,
        db_session: Session,
        obj: Base,
        creating_user: User,
        extra_data={}
    ):
        if obj.target_type_enum() == TargetTypeEnum.entry:
            # Notify when someone replies to a subscribed entry
            parent_entry_users = self.get_subscribed_users(
                db_session, obj.target_type_enum(), obj.parent_entry_id
            )
            # Notify when someone creates an entry in any other subscribed object
            parent_object_users = self.get_subscribed_users(
                db_session, obj.target_type, obj.target_id
            )
            users = list(set(parent_entry_users + parent_object_users))
            for user in users:
                if creating_user.id == user.id:
                    continue  # Skip notifying users of their own activity
                if user in parent_entry_users:
                    message = self.ellipsis_message(
                        f"{creating_user.username} replied to entry {obj.id} in "
                        f"{obj.target_type.value} {obj.target_id}"
                    )
                else:
                    message = self.ellipsis_message(
                        f"{creating_user.username} created a new entry in "
                        f"{obj.target_type.value} {obj.target_id}"
                    )
                if obj.entry_data.get("plain_text"):
                    message += ": " + obj.entry_data["plain_text"]
                elif obj.entry_data.get("html"):
                    message += ": " + re.sub(HTML_REMOVE_TAGS, "", obj.entry_data["html"])
                entry_ref_id = obj.target_type.value + " " + str(obj.target_id)
                entry_ref_id += " entry " + str(obj.id)
                notification_create = NotificationCreate(
                    user_id=user.id, message=message, priority=PriorityEnum.low,
                    ref_id=entry_ref_id
                )
                self.create(db_session, obj_in=notification_create)
        else:
            pass  # Only entry creations can generate notifications for now

    def send_update_notifications(
        self,
        db_session: Session,
        obj: Base,
        creating_user: User,
        extra_data={}
    ):
        # Notify when someone updates a subscribed object
        target_type = obj.target_type_enum()
        users = self.get_subscribed_users(
            db_session, target_type, obj.id
        )
        for user in users:
            if creating_user.id == user.id:
                continue  # Skip notifying users of their own activity
            message = self.ellipsis_message(
                f"{creating_user.username} updated {target_type.value} {obj.id}"
            )
            extra_message = ""
            for data_item in extra_data:
                if data_item in ["data", "entry_data"]:
                    continue
                item_representation = extra_data[data_item]
                if isinstance(item_representation, Enum):
                    item_representation = item_representation.value
                item_representation = repr(item_representation)
                if extra_message == "":
                    extra_message += f":\nChanged {data_item} to {item_representation}"
                else:
                    extra_message += f", changed {data_item} to {item_representation}"
            message += extra_message
            message = self.ellipsis_message(message)
            obj_ref_id = target_type.value + " " + str(obj.id)
            if target_type == TargetTypeEnum.entry:
                obj_ref_id = obj.target_type.value + " " + str(obj.target_id) + " " + obj_ref_id
            notification_create = NotificationCreate(
                user_id=user.id, message=message, priority=PriorityEnum.low,
                ref_id=obj_ref_id
            )
            self.create(db_session, obj_in=notification_create)


notification = CRUDNotification(Notification)
