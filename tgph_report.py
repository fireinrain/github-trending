# coding:utf-8
"""
每周热榜报告:
1. 从数据库汇总本周(周一~周日)首次上榜的仓库
2. 按语言分组发布为 telegra.ph 媒体周报
3. 将返回的文章地址保存到 weekly_report 表(本周已生成过则直接复用,防止重复)
4. 推送文章地址到 Telegram 频道

由 main.py 在周末自动调用, 生成的周报地址会附在当日的推送结束问候语中;
也可手动运行: python tgph_report.py
"""
import asyncio
import datetime
import json
import os
import re

import requests

import database
import telegrambot
from telegrambot import escape_markdown_v2

TELEGRAPH_API = 'https://api.telegra.ph'
CHANNEL_URL = 'https://t.me/ghtrendings'

# 数据库 category 字段 -> 周报展示标题
CATEGORY_TITLE_MAP = {
    'all': 'All Language',
    'java': 'Java',
    'python': 'Python',
    'javascript': 'Javascript',
    'typescript': 'Typescript',
    'go': 'Go',
    'c': 'C',
    'c++': 'C++',
    'c#': 'C#',
    'rust': 'Rust',
    'html': 'Html',
    'unknown': 'Unknown',
}


def is_weekend(today: datetime.date = None) -> bool:
    """周六或周日返回 True"""
    today = today or datetime.date.today()
    return today.weekday() >= 5


def get_week_range(today: datetime.date = None) -> (datetime.date, datetime.date):
    """返回本周周一和周日的日期"""
    today = today or datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    sunday = monday + datetime.timedelta(days=6)
    return monday, sunday


def query_week_trending(start_date: datetime.date, end_date: datetime.date) -> list:
    """查询本周首次上榜的仓库, 按分类和 star 数排序"""
    return (
        database.session.query(database.GithubTrending)
        .filter(database.GithubTrending.trend_date >= start_date.strftime('%Y-%m-%d'))
        .filter(database.GithubTrending.trend_date <= end_date.strftime('%Y-%m-%d'))
        .filter(database.GithubTrending.del_flag.is_(False))
        .order_by(database.GithubTrending.category.asc(), database.GithubTrending.repo_star.desc())
        .all()
    )


def build_telegraph_content(repos: list, monday: datetime.date, sunday: datetime.date) -> list:
    """
    构建 Telegraph Node 格式内容, 按语言分组展示:
    链接 + watch/fork/star 统计 + 上榜次数 + 简介
    """
    sections = {}
    for repo in repos:
        sections.setdefault(_norm_category(repo.category), []).append(repo)

    content = [{
        'tag': 'p',
        'children': [f'统计周期: {monday} ~ {sunday}, 共 {len(repos)} 个仓库登上 GitHub Trending。'],
    }]

    for category, items in sections.items():
        content.append({'tag': 'h3', 'children': [CATEGORY_TITLE_MAP.get(category, category.capitalize())]})
        repo_nodes = []
        for repo in items:
            children = [
                {'tag': 'a', 'attrs': {'href': repo.url}, 'children': [repo.title]},
                f' ⭐{repo.repo_star} | 🍴{repo.repo_folk} | 👀{repo.repo_see} | 上榜 {repo.trend_count} 次',
            ]
            desc = _short_desc(repo.desc, limit=120)
            if desc:
                children.append({'tag': 'br'})
                children.append(desc)
            repo_nodes.append({'tag': 'li', 'children': children})
        content.append({'tag': 'ul', 'children': repo_nodes})
    return content


def _telegraph_post(method: str, payload: dict) -> dict:
    resp = requests.post(f'{TELEGRAPH_API}/{method}', json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data.get('ok'):
        raise RuntimeError(f'telegra.ph {method} 调用失败: {data.get("error")}')
    return data['result']


def get_telegraph_access_token() -> str:
    """
    获取 telegra.ph access token, 优先级:
    1. 环境变量 TELEGRAPH_TOKEN(推荐在 GitHub Secrets 配置)
    2. 数据库中持久化的账号(保证固定页跨周可编辑)
    3. 临时注册新账号并入库
    """
    token = os.environ.get('TELEGRAPH_TOKEN')
    if token:
        return token
    account = database.session.query(database.TelegraphAccount).first()
    if account and account.access_token:
        return account.access_token
    result = _telegraph_post('createAccount', {
        'short_name': 'GHTrending',
        'author_name': 'Github Trending',
        'author_url': CHANNEL_URL,
    })
    token = result['access_token']
    try:
        database.session.add(database.TelegraphAccount(short_name='GHTrending', access_token=token))
        database.session.commit()
        print(">>> telegra.ph 账号已注册并保存到数据库")
    except Exception as e:
        print(f">>> 保存telegra.ph账号失败: {e}")
        database.session.rollback()
    return token


def publish_weekly_report(title: str, content: list) -> str:
    """发布文章并返回 telegra.ph 地址"""
    result = _telegraph_post('createPage', {
        'access_token': get_telegraph_access_token(),
        'title': title,
        'author_name': 'Github Trending',
        'author_url': CHANNEL_URL,
        'content': json.dumps(content, ensure_ascii=False),
        'return_content': False,
    })
    return result['url']

def save_report_to_db(title: str, monday: datetime.date, sunday: datetime.date,
                      repo_count: int, telegraph_url: str):
    record = database.WeeklyReport(
        title=title,
        start_date=monday.strftime('%Y-%m-%d'),
        end_date=sunday.strftime('%Y-%m-%d'),
        repo_count=repo_count,
        telegraph_url=telegraph_url,
    )
    try:
        database.session.add(record)
        database.session.commit()
        print(f">>> 周报地址已保存到数据库: {telegraph_url}")
    except Exception as e:
        print(f">>> 保存周报记录失败: {e}")
        database.session.rollback()


async def generate_weekly_report() -> str:
    """
    生成本周周报并推送, 返回 telegra.ph 地址;
    本周没有数据返回空串, 已生成过则直接返回已有地址。
    """
    monday, sunday = get_week_range()
    exists = database.session.query(database.WeeklyReport).filter_by(
        end_date=sunday.strftime('%Y-%m-%d')).first()
    if exists and exists.telegraph_url:
        print(f">>> 本周周报已生成过, 直接复用: {exists.telegraph_url}")
        return exists.telegraph_url

    repos = query_week_trending(monday, sunday)
    if not repos:
        print(">>> 本周没有上榜仓库数据, 跳过周报生成")
        return ''

    title = f'GitHub Trending 周报 {monday} ~ {sunday}'
    content = build_telegraph_content(repos, monday, sunday)
    telegraph_url = publish_weekly_report(title, content)
    print(f">>> 周报已发布: {telegraph_url}")
    save_report_to_db(title, monday, sunday, len(repos), telegraph_url)

    safe_range = escape_markdown_v2(f'{monday} ~ {sunday}')
    message = (f'📰 GitHub Trending 周报 \({safe_range}\)\n'
               f'\n'
               f'本周共有 `{len(repos)}` 个仓库登上热榜, 完整报告请戳:\n'
               f'[📖 点击阅读本周周报]({telegraph_url})\n'
               f'\n'
               f'\#weekly\_report')
    await telegrambot.send_message2bot(message)
    return telegraph_url


# ==================== 固定统计页 ====================

STATS_PAGE_TITLE = '📊 GitHub Trending 数据统计'
TOP_N_PER_LANGUAGE = 30
BAR_WIDTH = 16


def _norm_category(category) -> str:
    """规范历史遗留的转义分类名(如 'c\\#', 'c\\++')"""
    return (category or 'all').replace('\\', '')


def _short_desc(desc, limit: int = 70) -> str:
    """单行短描述: 去换行并截断"""
    if not desc:
        return ''
    text = desc.replace('\r', '').replace('\n', ' ').strip()
    if len(text) > limit:
        text = text[:limit].rstrip() + '…'
    return text


def query_all_trending() -> list:
    """查询数据库全部有效仓库记录"""
    return (
        database.session.query(database.GithubTrending)
        .filter(database.GithubTrending.del_flag.is_(False))
        .all()
    )


def build_stats_content(repos: list, update_date: str) -> list:
    """
    构建固定统计页内容:
    总览(更新日期/总量) -> 语言分布条形图 -> 各语言 Top 榜(star降序,上榜次数次序)
    注: Telegraph 不支持 JS/CSS, 无法实现真正的 tab 切换, 采用分区排版
    """
    total = len(repos)
    lang_map = {}
    for repo in repos:
        lang_map.setdefault(_norm_category(repo.category), []).append(repo)

    def label(category):
        return CATEGORY_TITLE_MAP.get(category, category.capitalize())

    nodes = [
        {'tag': 'p', 'children': [f'🗓 数据更新日期: {update_date}']},
        {'tag': 'p', 'children': [f'📚 收录仓库总数: {total} 个 · 语言分类: {len(lang_map)} 个']},
        {'tag': 'h3', 'children': ['📈 语言分布']},
    ]

    max_count = max(len(items) for items in lang_map.values())
    dist_nodes = []
    for category in sorted(lang_map):
        count = len(lang_map[category])
        bar_len = max(1, round(count / max_count * BAR_WIDTH))
        bar = '█' * bar_len + '░' * (BAR_WIDTH - bar_len)
        pct = f'{count / total * 100:.1f}%'
        dist_nodes.append({
            'tag': 'li',
            'children': [{'tag': 'code', 'children': [bar]}, f' {label(category)}: {count} 个({pct})'],
        })
    nodes.append({'tag': 'ul', 'children': dist_nodes})

    for category in sorted(lang_map):
        items = sorted(lang_map[category],
                       key=lambda r: (r.repo_star or 0, r.trend_count or 0),
                       reverse=True)
        show = items[:TOP_N_PER_LANGUAGE]
        nodes.append({'tag': 'hr'})
        nodes.append({'tag': 'h3', 'children': [f'{label(category)}({len(items)})']})
        nodes.append({
            'tag': 'p',
            'children': [{'tag': 'i',
                          'children': [f'按 ⭐ Star 数与上榜次数排序, 展示前 {len(show)} 名']}],
        })
        repo_nodes = []
        for rank, repo in enumerate(show, start=1):
            children = [
                f'{rank}. ',
                {'tag': 'a', 'attrs': {'href': repo.url}, 'children': [repo.title]},
                f' ⭐{repo.repo_star or 0} · 🔥上榜{repo.trend_count or 0}次',
            ]
            desc = _short_desc(repo.desc)
            if desc:
                children.append({'tag': 'br'})
                children.append(desc)
            repo_nodes.append({'tag': 'li', 'children': children})
        nodes.append({'tag': 'ul', 'children': repo_nodes})

    nodes.append({'tag': 'hr'})
    nodes.append({'tag': 'p', 'children': [{'tag': 'i', 'children': ['🤖 由 GitHub Actions 每周自动更新']}]})
    return nodes


def _publish_stats_page(content: list) -> dict:
    """创建新的统计页, 返回 {'path':..., 'url':...}"""
    result = _telegraph_post('createPage', {
        'access_token': get_telegraph_access_token(),
        'title': STATS_PAGE_TITLE,
        'author_name': 'Github Trending',
        'author_url': CHANNEL_URL,
        'content': json.dumps(content, ensure_ascii=False),
        'return_content': False,
    })
    return {'path': result['path'], 'url': result['url']}


def _update_stats_page(path: str, content: list) -> dict:
    """原地更新已有统计页(editPage), 返回 {'path':..., 'url':...}"""
    result = _telegraph_post('editPage', {
        'access_token': get_telegraph_access_token(),
        'path': path,
        'title': STATS_PAGE_TITLE,
        'author_name': 'Github Trending',
        'author_url': CHANNEL_URL,
        'content': json.dumps(content, ensure_ascii=False),
        'return_content': False,
    })
    return {'path': path, 'url': result['url']}


def _save_stats_page(path: str, url: str, week_start: str, update_date: str, total_repos: int):
    record = database.session.query(database.StatsPage).first()
    if record is None:
        record = database.StatsPage(title=STATS_PAGE_TITLE)
        database.session.add(record)
    record.path = path
    record.url = url
    record.last_update_date = update_date
    record.week_start = week_start
    record.total_repos = total_repos
    try:
        database.session.commit()
        print(f">>> 统计页已更新并保存到数据库: {url}")
    except Exception as e:
        print(f">>> 保存统计页记录失败: {e}")
        database.session.rollback()


README_PATH = './README.md'
STATS_BLOCK_START = '<!-- STATS_PAGE:START -->'
STATS_BLOCK_END = '<!-- STATS_PAGE:END -->'


def write_stats_page_to_readme(telegraph_url: str, update_date: str):
    """
    统计页更新后把地址回写到 README.md。
    使用标记块定位, 已存在则原位刷新(地址/日期), 不存在则插入到 '## 功能' 之前。
    """
    try:
        with open(README_PATH, mode='r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(">>> 未找到 README.md, 跳过统计页地址回写")
        return

    block = (f'{STATS_BLOCK_START}\n'
             f'📊 固定统计页: [{STATS_PAGE_TITLE}]({telegraph_url})\n'
             f'> 语言分布 · 各语言 ⭐Star/🔥上榜次数 Top 榜 · 每周自动更新  \n'
             f'> 最近数据更新: **{update_date}**\n'
             f'{STATS_BLOCK_END}')

    pattern = re.compile(re.escape(STATS_BLOCK_START) + '.*?' + re.escape(STATS_BLOCK_END), re.DOTALL)
    if pattern.search(content):
        new_content = pattern.sub(lambda _: block, content)
    elif '\n## 功能' in content:
        new_content = content.replace('\n## 功能', f'\n{block}\n\n## 功能', 1)
    else:
        new_content = content.rstrip() + f'\n\n{block}\n'

    try:
        with open(README_PATH, mode='w', encoding='utf-8') as f:
            f.write(new_content)
        print(f">>> 统计页地址已回写到 README.md: {telegraph_url}")
    except Exception as e:
        print(f">>> 回写 README.md 失败: {e}")


async def update_weekly_stats_page(force: bool = False) -> str:
    """
    创建或原地更新固定统计页, 每周最多更新一次(同周内跳过), 返回页面地址。
    force=True 时忽略同周判断强制刷新。
    """
    monday, sunday = get_week_range()
    week_start = monday.strftime('%Y-%m-%d')
    update_date = datetime.date.today().strftime('%Y-%m-%d')

    record = database.session.query(database.StatsPage).first()
    if not force and record and record.week_start == week_start:
        print(f">>> 本周统计页已更新过, 跳过: {record.url}")
        return record.url

    repos = query_all_trending()
    if not repos:
        print(">>> 数据库中没有仓库数据, 跳过统计页生成")
        return ''

    content = build_stats_content(repos, update_date)
    if record and record.path:
        try:
            page = _update_stats_page(record.path, content)
        except Exception as e:
            # 页面丢失或账号不匹配时降级为创建新页
            print(f">>> 更新统计页失败({e}), 降级为创建新页面")
            page = _publish_stats_page(content)
    else:
        page = _publish_stats_page(content)

    _save_stats_page(page['path'], page['url'], week_start, update_date, len(repos))
    # 回写统计页地址到 README.md
    write_stats_page_to_readme(page['url'], update_date)
    return page['url']


if __name__ == '__main__':
    asyncio.run(generate_weekly_report())
    asyncio.run(update_weekly_stats_page(force=True))
