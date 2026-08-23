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


class WeeklyReport(Base):
    __tablename__ = 'weekly_report'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    start_date = Column(String)
    end_date = Column(String)
    repo_count = Column(Integer, default=0)
    telegraph_url = Column(String)
    create_time = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


class StatsPage(Base):
    """固定统计页(telegra.ph), 每周通过 editPage 原地更新"""
    __tablename__ = 'stats_page'

    id = Column(Integer, primary_key=True, autoincrement=True)
    path = Column(String)
    url = Column(String)
    title = Column(String)
    last_update_date = Column(String)
    week_start = Column(String)
    total_repos = Column(Integer, default=0)
    create_time = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


class TelegraphAccount(Base):
    """telegra.ph 账号持久化, 保证固定页跨周可编辑"""
    __tablename__ = 'telegraph_account'

    id = Column(Integer, primary_key=True, autoincrement=True)
    short_name = Column(String)
    access_token = Column(String, nullable=False)
    create_time = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


# Example usage
engine = create_engine('sqlite:///github-trending.db', echo=True)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()
