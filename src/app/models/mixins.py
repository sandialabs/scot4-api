from datetime import datetime, timezone

from sqlalchemy import Column, func, select, types, and_
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import (
    column_property, foreign, relationship, backref, synonym, remote
)
from app.enums import TargetTypeEnum

# BUG server-default https://github.com/sqlalchemy/alembic/issues/768

# Shim class to make sure all of our timestamps are returned from the database
# as UTC. All input timestamps should already be UTC.


class UTCDateTime(types.TypeDecorator):
    impl = types.DateTime
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is None:
            return None

        if value.tzinfo is None:  # This should always be the case with postgres
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None

        if isinstance(value, str):
            value = datetime.fromisoformat(value)

        if value.tzinfo is None:
            return value

        # For consistency, we store utc times as timezone-naive datetimes
        return value.astimezone(timezone.utc).replace(tzinfo=None)


class TimestampMixin(object):
    created = Column("created_date", UTCDateTime, default=datetime.utcnow)

    modified = Column(
        "modified_date",
        UTCDateTime,
        nullable=False,
        onupdate=datetime.utcnow,
        default=datetime.utcnow,
    )


class EntryMixin(object):
    # This needs to be lazily-loaded so that we don't fetch a bunch of
    # entries every time someone searches. Instead, it's merely loaded on
    # demand whenever another api method specifically accesses it.
    # Also dynamically creates relationships for the entry to access its
    # parent; this is much less performant and isn't used much
    entry_rel_overlaps = []

    @declared_attr
    def entries(self):
        from app.models.entry import Entry  # Avoid circular dependency
        self.entry_rel_overlaps.append("parent_%s" % self.target_type_enum().value)
        overlap_string = ",".join(self.entry_rel_overlaps) + ",entries,summaries"
        Entry.parent_class_mapping[self.target_type_enum().value] = self
        return relationship("Entry", foreign_keys=[Entry.target_id],
                            primaryjoin=(Entry.target_type == self.target_type_enum())
                            & (Entry.target_id == self.id),
                            overlaps=overlap_string, cascade="all",
                            backref=backref(
                                "parent_%s" % self.target_type_enum().value,
                                primaryjoin=remote(self.id) == foreign(Entry.target_id),
                                overlaps=overlap_string
        ))

    @declared_attr
    def entry_count(self):
        from app.models.entry import Entry  # Avoid circular dependency

        return column_property(
            select(func.count(Entry.id))
            .where(
                (Entry.target_type == self.target_type_enum())
                & (Entry.target_id == self.id)
            )
            .scalar_subquery()
        )

# Dropped for efficiency, we may want this back later
#    @declared_attr
#    def open_task_count(self):
#        from app.models.entry import Entry  # Avoid circular dependency
#
#        return column_property(
#            select(func.count(Entry.id))
#            .where(
#                (Entry.target_type == self.target_type_enum())
#                & (Entry.target_id == self.id)
#                & (Entry.entry_class == EntryClassEnum.task)
#            )
#            .filter(
#                Entry.entry_data["task_status"].as_string() == "Open"
#            )
#            .scalar_subquery()
#        )

    # Give every entry'd object a "subject" if it didn't already have one
    @declared_attr
    def subject(self):
        if hasattr(self, "name"):
            return synonym("name")
        return None


class EntityCountMixin(object):
    """
    Inherit from this mixin to indicate that this type of object can contain
    entities that are not directly tracked. Adds an "entity_count" property that
    is taken from the entities table
    """

    @declared_attr
    def entity_count(self):
        from app.models.link import Link  # Avoid circular dependency
        left_subquery = select(Link.v0_id, Link.v0_type).filter(and_((Link.v1_id == self.id), (Link.v1_type == TargetTypeEnum.entity), (Link.v0_type != TargetTypeEnum.entry), (Link.v0_type != TargetTypeEnum.alertgroup))).group_by(Link.v0_id, Link.v0_type).correlate_except(Link).subquery()
        left = select(func.count('*')).select_from(left_subquery).scalar_subquery()
        right_subquery = select(Link.v1_id, Link.v1_type).filter(and_((Link.v0_id == self.id), (Link.v0_type == TargetTypeEnum.entity), (Link.v1_type != TargetTypeEnum.entry), (Link.v1_type != TargetTypeEnum.alertgroup))).group_by(Link.v1_id, Link.v1_type).correlate_except(Link).subquery()
        right = select(func.count('*')).select_from(right_subquery).scalar_subquery()
        return column_property(right + left)

        # For some reason, the OR statement here was slowing the below query way down so I broke it into two and combined the scalar results
        # return column_property(
        #    select(func.count(Link.id))
        #    .filter(or_(and_((Link.v1_id == self.id), (Link.v1_type == TargetTypeEnum.entity)), and_((Link.v0_id == self.id) & (Link.v0_type == TargetTypeEnum.entity))))
        #    .correlate_except(Link)
        #    .scalar_subquery()
        # )


class FileCountMixin(object):
    """
    Inherit from this mixin to indicate that this type of object can be linked
    to files. Creates a new read-only attribute called file_count that is the
    number of files attached to this object.
    """
    @declared_attr
    def file_count(self):
        from app.models.link import Link  # Avoid circular dependency
        from app.models.file import File

        return column_property(
            select(func.count(Link.id))
            .join(File, Link.v1_id == File.id)
            .where(
                (Link.v0_type == self.target_type_enum())
                & (Link.v0_id == self.id)
                & (Link.v1_type == TargetTypeEnum.file)
            )
            .scalar_subquery()
        )


class SignatureForMixin(object):
    """
    Inherit from this mixin to indicate that this object can be forward-linked
    to signatures. Creates a new attribute called "associated_signatures" with
    a list of signatures linked to this object.
    """

    @declared_attr
    def associated_signatures(self):
        # Avoid circular dependencies
        from app.models.link import Link
        from app.models.signature import Signature
        return relationship("Signature", secondary="links",
                            primaryjoin=(Link.v0_type == self.target_type_enum())
                            & (Link.v0_id == self.id),
                            secondaryjoin=(Link.v1_type == TargetTypeEnum.signature)
                            & (Link.v1_id == Signature.id),
                            viewonly=True)


class GuidesForMixin(object):
    """
    Inherit from this mixin to indicate that this object can be forward-linked
    to guides. Creates a new attribute called "associated_guides" with a list of
    guides linked to this object.
    """

    @declared_attr
    def associated_guides(self):
        # Avoid circular dependencies
        from app.models.guide import Guide
        from app.models.link import Link
        return relationship("Guide", secondary="links",
                            primaryjoin=(Link.v0_type == self.target_type_enum())
                            & (Link.v0_id == self.id),
                            secondaryjoin=(Link.v1_type == TargetTypeEnum.guide)
                            & (Link.v1_id == Guide.id),
                            viewonly=True)


class TagMixin(object):
    """
    Inherit from this mixin to indicate that this object is taggable. Adds a
    "tags" relationship that contains the tag objects that this object is
    tagged with.
    """

    @declared_attr
    def tags(self):
        # Avoid circular dependencies
        from app.models.link import Link
        from app.models.tag import Tag

        return relationship(
            "Tag",
            secondary="links",
            primaryjoin=(Link.v0_type == self.target_type_enum())
            & (foreign(Link.v0_id) == self.id),
            secondaryjoin=(Link.v1_type == TargetTypeEnum.tag)
            & (foreign(Link.v1_id) == Tag.id),
            viewonly=True,
            lazy="selectin",
        )


class EntityMixin(object):
    """
    Inherit from this mixin to indicate that this object can contain entities.
    Adds an "entities" relationship that contains the entity objects related to
    this object.
    """

    @declared_attr
    def entities(self):
        # Avoid circular dependencies
        from app.models.entity import Entity
        from app.models.link import Link
        return relationship("Entity", secondary="links",
                            primaryjoin=(Link.v0_type == self.target_type_enum())
                            & (Link.v0_id == self.id),
                            secondaryjoin=(Link.v1_type == TargetTypeEnum.entity)
                            & (Link.v1_id == Entity.id),
                            viewonly=True)

    @declared_attr
    def entity_count(self):
        from app.models.link import Link  # Avoid circular dependency

        return column_property(
            select(func.count(Link.id))
            .where((Link.v1_type == TargetTypeEnum.entity) & (Link.v1_id == self.id))
            .correlate_except(Link)
            .scalar_subquery()
        )


class SourceMixin(object):
    """
    Inherit from this mixin to indicate that this object can have sources. Adds
    a "sources" relationship that contains the source objects attached to this
    object.
    """

    @declared_attr
    def sources(self):
        # Avoid circular dependencies
        from app.models.link import Link
        from app.models.source import Source

        return relationship(
            "Source",
            secondary="links",
            primaryjoin=(Link.v0_type == self.target_type_enum())
            & (foreign(Link.v0_id) == self.id),
            secondaryjoin=(Link.v1_type == TargetTypeEnum.source)
            & (foreign(Link.v1_id) == Source.id),
            viewonly=True,
            lazy="selectin",
        )


class PromotionFromMixin(object):
    """
    Inherit from this mixin to indicate that other objects can be promoted to
    this object object can be promoted. Adds a "sources" relationship that
    contains the source objects attached to this object.
    """

    @declared_attr
    def promoted_from_sources(self):
        # Avoid circular dependencies
        from app.models.promotion import Promotion
        return relationship("Promotion", foreign_keys=[Promotion.p1_id],
                            primaryjoin=(foreign(Promotion.p1_id) == self.id)
                            & (Promotion.p1_type == self.target_type_enum()),
                            overlaps="promoted_from_sources",
                            cascade="all", lazy="selectin", uselist=True)


class PromotionToMixin(object):
    """
    Inherit from this mixin to indicate that this object can be promoted to
    other objects. Adds a "targets" relationship that contains the source
    objects attached to this object.
    """

    @declared_attr
    def promoted_to_targets(self):
        # Avoid circular dependencies
        from app.models.promotion import Promotion
        return relationship("Promotion", foreign_keys=[Promotion.p0_id],
                            primaryjoin=(foreign(Promotion.p0_id) == self.id)
                            & (Promotion.p0_type == self.target_type_enum()),
                            overlaps="promoted_to_targets",
                            cascade="all", lazy="selectin", uselist=True)
