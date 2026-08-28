# coding:utf-8
import asyncio
import os
import urllib.parse

import requests
from datetime import datetime
from fake_useragent import UserAgent
from pyquery import PyQuery as pq

import database
import telegrambot
from bless import generate_bless_word, format_daily_bless_message
from database import GithubTrending, EveryDayBless
from telegrambot import escape_markdown_v2
from tgph_report import generate_weekly_report, is_weekend, update_daily_stats_page

ua = UserAgent()

gh_token_info = {'code': os.environ.get('GH_TOKEN'), 'valid': True}


def check_github_token_validity(github_token) -> dict:
    """校验 GitHub Token; 未配置或校验失败时把 valid 标记为 False。"""
    if not github_token:
        print('未配置 GH_TOKEN, 将使用匿名请求。')
        gh_token_info['valid'] = False
        return gh_token_info

    url = 'https://api.github.com/user'
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    try:
        response = requests.get(url, headers=headers)
    except Exception as e:
        print(f">>> 校验 GitHub Token 失败: {e}")
        gh_token_info['valid'] = False
        return gh_token_info

    if response.status_code == 200:
        print('The GitHub token is valid.')
    else:
        print('The GitHub token is not valid.')
        gh_token_info['valid'] = False
    return gh_token_info


def scrape_url(url):
    ''' Scrape github trending url
    '''
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8'
    }

    print(f">>> Fetch link: {url}")
    r = None
    try:
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
    except Exception as e:
        print(f"Error for fetch url: {url},error:{e}")
        return None

    d = pq(r.content)
    items = d('div.Box article.Box-row')

    results = {}
    # codecs to solve the problem utf-8 codec like chinese
    for item in items:
        i = pq(item)
        title = i(".lh-condensed a").text()
        description = i("p.col-9").text()
        url = i(".lh-condensed a").attr("href")
        url = "https://github.com" + url
        results[title] = {'title': title, 'url': url, 'description': description}
    return results


def scrape_lang(language):
    """
    Scrape github trending with lang parameters
    """
    url = 'https://github.com/trending/{language}'.format(language=urllib.parse.quote_plus(language))
    r1 = scrape_url(url)
    url = 'https://github.com/trending/{language}?spoken_language_code=zh'.format(
        language=urllib.parse.quote_plus(language))
    r2 = scrape_url(url)
    result = {}
    if r1 is not None:
        result.update(r1)
    if r2 is not None:
        result.update(r2)
    return result


def format_trending_tg_message(message: dict, lang: str, repo_stats: tuple) -> str:
    current_date = datetime.now()
    # 'java', 'python', 'go', 'javascript', 'typescript', 'c', 'c++', 'c#', 'rust', 'html', 'unknown'
    format_lang_map = {
        '': 'All',
        'java': 'Java',
        'python': 'Python',
        'javascript': 'Javascript',
        'typescript': 'Typescript',
        'go': 'Go',
        'c': 'C',
        'c++': 'Cplusplus',
        'c#': 'Csharp',
        'rust': 'Rust',
        'html': 'Html',
        'unknown': 'Unknown'
    }
    temp_lang = lang
    # 格式化日期为"20201112"形式
    formatted_date = current_date.strftime("%Y%m%d")
    lang = format_lang_map[temp_lang.strip()]
    # 使用副本做转义,避免污染原始数据(归档markdown会用到原始title)
    escaped_title = escape_markdown_v2(message['title'])
    escaped_description = escape_markdown_v2(message['description'])

    return (f"`{escaped_title}`\n"
            f"`{escaped_description}`\n"
            f"[Repo URL]({message['url']}) \| `👀{repo_stats[0]}` `🍴{repo_stats[1]}` `⭐{repo_stats[2]}`\n"
            f"\#D{formatted_date} \#D{formatted_date}\_{lang} \#{lang}")


def check_and_store_db(value: dict, lang: str) -> (dict, bool, tuple):
    repo_stats = None
    if lang == '':
        lang = 'all'
    result = database.session.query(GithubTrending).filter_by(title=value['title']).first()
    if result:
        # update trend_count data
        trend_count = result.trend_count
        result.trend_count = trend_count + 1
        repo_stats = []
        repo_stats.append(result.repo_see)
        repo_stats.append(result.repo_folk)
        repo_stats.append(result.repo_star)
        repo_stats.append(True)
        result.repo_status = 1
        # 仓库被删除了 404

        try:
            database.session.commit()
        except Exception as e:
            print(f">>> 更新Github trending记录失败: {e}")
            database.session.rollback()

        print(f">>> Title: {result.title}, URL: {result.url}, Description: {result.desc},当前仓库已经推送过,做跳过处理")
        return value, True, repo_stats
    # insert to db
    # 获取当前日期
    repo_stats = fetch_repo_stats(value['title'])
    if repo_stats is None:
        print(f">>> 获取仓库信息失败,使用默认数据入库: {value['title']}")
        repo_stats = (0, 0, 0, False)
    print(f">>> 当前仓库信息: {repo_stats}")
    current_date = datetime.now()

    # 格式化日期为"20201112"形式
    formatted_date = current_date.strftime("%Y-%m-%d")
    data = GithubTrending(
        title=value['title'],
        url=value['url'],
        desc=value['description'],
        trend_date=f"{formatted_date}",
        trend_count=1,
        category=f"{lang}",
        repo_see=repo_stats[0],
        repo_folk=repo_stats[1],
        repo_star=repo_stats[2],
        repo_status=1,
    )
    try:
        database.session.add(data)
        database.session.commit()
        print(f">>> Insert new github trending data successfully!")
    except Exception as e:
        print(f">>> Error creating new record for github trending data: {data}")
        database.session.rollback()
    return value, False, repo_stats


def fetch_repo_stats(repo_title: str) -> ():
    """
    获取仓库的watch fork star数据
    :param repo_title:
    :return:
    """
    title_split = repo_title.split('/')
    username = title_split[0].strip()
    repo_name = title_split[1].strip()
    api_url = f'https://api.github.com/repos/{username}/{repo_name}'
    # 使用github token 请求github api rate limit 1000/H
    headers = None
    if gh_token_info['valid']:
        headers = {
            'Authorization': f'token {gh_token_info["code"]}',
            'User-Agent': ua.random,
            'Accept': 'application/vnd.github.v3+json',
        }
    else:
        headers = {
            'User-Agent': ua.random,
            'Accept': 'application/vnd.github.v3+json',
        }
    # print(f"current token: {GITHUB_TOKEN}")
    try:
        response = requests.get(api_url, headers=headers)
        # response.raise_for_status()  # Check for errors
        if response.status_code == 404:
            print(f">>> 当前仓库404状态，已被删除: {username}/{repo_name}")
            return 0, 0, 0, False
        if response.status_code != 200:
            print(f">>> 当前请求可能触发Github api limit限制.")
            print(f">>> {response.text}")
            return 0, 0, 0, False
        repo_data = response.json()

        watch_count = repo_data.get('subscribers_count', 0)
        forks_count = repo_data.get('forks_count', 0)
        stars_count = repo_data.get('stargazers_count', 0)

        # watch,folk,star,is_exist
        return watch_count, forks_count, stars_count, True

    except requests.exceptions.RequestException as e:
        print(f">>> Error fetching data: {e}")

    return None


async def push_daily_bless_message(new_trending_count: int, weekly_report_url: str = ''):
    today = datetime.now().strftime("%Y-%m-%d")
    bless_query = database.session.query(EveryDayBless).filter(EveryDayBless.push_date == today).all()
    if not bless_query:
        # 今天还没推送过,新插入一条今天记录并推送
        word = generate_bless_word()
        message = format_daily_bless_message(word, new_trending_count, weekly_report_url)
        await telegrambot.send_message(message)
        bless = EveryDayBless(push_date=today, push_flag=True)
        try:
            database.session.add(bless)
            database.session.commit()
        except Exception as e:
            print(f"创建记录失败: {e}")
            database.session.rollback()


async def fetch_and_push_trending() -> int:
    """
    Start the scrape job
    """
    languages = ['', 'java', 'python', 'go', 'javascript', 'typescript', 'c', 'c++', 'c#', 'rust', 'html', 'unknown']
    new_trending_count = 0
    for lang in languages:
        results = scrape_lang(lang)
        if not results:
            continue
        # push to telegram bot
        for value in results.values():
            value, have_push, repo_stats = check_and_store_db(value, lang)
            if not have_push:
                print(f">>> 发现新的github trending记录,正在推送到telegram 频道...")
                new_trending_count += 1
                message = format_trending_tg_message(value, lang, repo_stats)
                await telegrambot.send_message(message)
                await asyncio.sleep(2)
            await asyncio.sleep(5)
    return new_trending_count


async def main():
    check_github_token_validity(gh_token_info['code'])
    new_trending_count = await fetch_and_push_trending()
    # 周末触发生成 telegra.ph 每周热榜周报(已生成过则复用地址)
    weekly_report_url = ''
    if is_weekend():
        try:
            weekly_report_url = await generate_weekly_report()
        except Exception as e:
            print(f">>> 生成本周周报失败: {e}")
    # 每天更新固定统计页(语言分布 + 各语言 Top), 并把地址回写到 README.md
    try:
        await update_daily_stats_page()
    except Exception as e:
        print(f">>> 更新统计页失败: {e}")
    # 推送每日推送结束问候语(周末生成周报时附带周报地址)
    await push_daily_bless_message(new_trending_count, weekly_report_url)
    # release db connection
    database.session.close()


if __name__ == '__main__':
    asyncio.run(main())
