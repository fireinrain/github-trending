from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from sqlalchemy.orm import declarative_base

Base = declarative_base()


class GithubTrending(Base):
    __tablename__ = 'gh_trending'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    desc = Column(String)
    # Assuming trend_date is a string for simplicity
    trend_date = Column(String)
    category = Column(String)
    trend_count = Column(Integer)
    repo_see = Column(Integer, default=0)
    repo_folk = Column(Integer, default=0)
    repo_star = Column(Integer, default=0)
    repo_status = Column(Boolean, default=True)
    del_flag = Column(Boolean, default=False)
    create_time = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    update_time = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'), onupdate=datetime.now)


class EveryDayBless(Base):
    __tablename__ = 'every_day_bless'
    id = Column(Integer, primary_key=True, autoincrement=True)
    push_flag = Column(Boolean, default=False)


# Example usage
engine = create_engine('sqlite:///github-trending.db', echo=True)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()
