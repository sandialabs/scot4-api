from sqlalchemy import Boolean, Column, Integer, ForeignKey, Table, text, VARCHAR
from sqlalchemy.orm import relationship

from app.db.base_class import Base

apikey_role_table = Table('apikeys_roles', Base.metadata,
                          Column('key', VARCHAR(length=255), ForeignKey('apikeys.key')),
                          Column('role_id', Integer, ForeignKey('roles.role_id'))
                          )


class ApiKey(Base):
    __tablename__ = "apikeys"
    key = Column('key', VARCHAR(length=255), primary_key=True)
    owner = Column('owner', VARCHAR(length=255), ForeignKey('users.username'), nullable=False)
    active = Column('active', Boolean, nullable=False, server_default=text('true'))
    roles = relationship('Role', secondary=apikey_role_table, backref='apikeys',
                         lazy='selectin')
