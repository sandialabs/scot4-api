from sqlalchemy.orm import Session, join

from app.crud.base import CRUDBase
from app.models import StorageSettings
from app.enums import TargetTypeEnum
from app.models.file import File
from app.models.link import Link
from app.object_storage import storage_provider_classes
from app.schemas.file import FileCreate, FileUpdate


class CRUDFile(CRUDBase[File, FileCreate, FileUpdate]):
    def get_storage_provider(self, db_session: Session):
        storage_setting = db_session.query(StorageSettings).filter(StorageSettings.enabled).first()
        sp = storage_provider_classes[storage_setting.provider](**storage_setting.config)
        return sp

    def get_storage_target(self, db_session: Session, file_pointer: str = ""):
        sp = self.get_storage_provider(db_session=db_session)
        file_target = sp.get_target(filename=file_pointer)
        return file_target

    def retrieve_element_files(self, db_session, source_id, source_type):
        _files = (
            db_session.query(File)
            .select_from(join(File, Link, onclause=File.id == Link.v1_id))
            .filter(
                Link.v0_id == source_id,
                Link.v0_type == source_type,
                Link.v1_type == TargetTypeEnum.file,
            )
            .all()
        )
        return _files, len(_files)

    def get_content(self, db_session: Session, obj: File):
        """
        Gets the content of a file (as a file stream object)
        Use get() to get the file object from the database first
        """
        storage_provider = self.get_storage_provider(db_session=db_session)
        return storage_provider.get_file_handle(filename=obj.file_pointer)

    def move_file_to_deleted_location(self, db_session: Session, file_pointer: str = None):
        storage_provider = self.get_storage_provider(db_session=db_session)
        storage_provider.move_file_to_deleted_location(filename=file_pointer)

    def move_file_to_default_location(self, db_session: Session, file_pointer: str = None):
        storage_provider = self.get_storage_provider(db_session=db_session)
        storage_provider.move_file_to_default_location(filename=file_pointer)

    def remove_file(
        self,
        db_session: Session,
        file_id: int,
        audit_logger=None
    ):
        """
        Save the file data to persistent storage, and add the corresponding model entry in the database.
        This is meant to run
        """
        file_obj = self.get(db_session=db_session, _id=file_id)
        if not file_obj:
            return None
        self.move_file_to_deleted_location(db_session=db_session, file_pointer=file_obj.file_pointer)
        return self.remove(db_session=db_session, _id=file_id, audit_logger=audit_logger)

    def unremove_file(
        self,
        db_session: Session,
        file_id: int,
        by_user: str,
        keep_ids: bool = True,
        audit_logger=None,
    ):
        file_obj = self.undelete(db_session=db_session, target_id=file_id, by_user=by_user, keep_ids=keep_ids, audit_logger=audit_logger)
        if file_obj:
            self.move_file_to_default_location(db_session=db_session, file_pointer=file_obj.file_pointer)
        return file_obj

    def filter(self, query, filter_dict):
        # Custom filtering for file objects
        # use a dummy filter_dict to not overwrite any other filename filters
        glob_filter = {}
        glob = filter_dict.pop("glob", None)
        if glob is not None:
            glob_filter["filename"] = glob.replace("*", "%").replace("?", "_")

        not_glob = filter_dict.get("not", {}).pop("glob", None)
        if not_glob is not None:
            glob_filter["not"] = {"filename": not_glob.replace("*", "%").replace("?", "_")}

        query = self._str_filter(query, glob_filter, "filename", False)
        query = self._str_filter(query, filter_dict, "description")
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.tag)
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.source)

        return super().filter(query, filter_dict)


file = CRUDFile(File)
