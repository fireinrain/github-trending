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
    push_date = Column(String, nullable=False)
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


def _migrate_every_day_bless():
    """兼容旧版 every_day_bless 表(仅有 push_flag), 新增 push_date 列并清理历史记录,
    否则旧表缺少 push_date 列会导致按日期查询报错."""
    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='every_day_bless'")
            ).fetchone()
            if not exists:
                return
            columns = [row[1] for row in conn.execute(text("PRAGMA table_info(every_day_bless)"))]
            if 'push_date' not in columns:
                conn.execute(text("ALTER TABLE every_day_bless ADD COLUMN push_date VARCHAR"))
                # 历史脏数据(已推送过的旧记录)不再复用, 删除以便当天正常推送祝福
                conn.execute(text("DELETE FROM every_day_bless"))
                print(">>> 迁移 every_day_bless 表完成: 新增 push_date 列并清理历史记录")
            conn.commit()
    except Exception as e:
        print(f">>> 迁移 every_day_bless 表失败: {e}")


_migrate_every_day_bless()

Session = sessionmaker(bind=engine)
session = Session()
