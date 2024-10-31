import time
import logging

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from sqlalchemy.engine import Engine

# from sqlalchemy.ext.asyncio import create_async_engine

"""
session https://github.com/tiangolo/fastapi/issues/726
"""

# engine
if "sqlite" in settings.SQLALCHEMY_DATABASE_URI:
    engine = create_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, connect_args={"connect_timeout": 100000}, pool_size=15, max_overflow=-1)
# scoped_session
# db_session = scoped_session(
#     sessionmaker(autocommit=False, autoflush=False, bind=engine)
# )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


DB_Subscriber = {}


def publish(action):
    for key in DB_Subscriber.keys():
        DB_Subscriber[key].append({"action": action})


@event.listens_for(SessionLocal, "before_commit")
def new_item_catch(session: Session):
    if session.new:
        publish({"new": session.new})


@event.listens_for(SessionLocal, "do_orm_execute")
def statement_catch(session: Session):
    publish({'statement': str(session.statement)})


logging.basicConfig()
logger = logging.getLogger("myapp.sqltime")
logger.setLevel(logging.DEBUG)


@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement,
                          parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())
#    logger.debug(f"Start Query: {statement}\n{parameters}")
#


@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement,
                         parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
#    if total > 5:
#        logger.debug('---------------------------')
#        logger.debug("Long Query!")
#        logger.debug(f"Query: {statement}\n{parameters}")
#        logger.debug("Total Time: %f", total)
#        logger.debug('---------------------------')
