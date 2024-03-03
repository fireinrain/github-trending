# coding:utf-8
import asyncio
import os
import datetime
import requests
import urllib.parse
from pyquery import PyQuery as pq
from datetime import datetime
from database import GithubTrending
import database
import telegrambot


def scrape_url(url):
    ''' Scrape github trending url
    '''
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8'
    }

    print(f"Fetch link: {url}")
    r = requests.get(url, headers=HEADERS)
    assert r.status_code == 200

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
    return {**r1, **r2}


def write_markdown(lang, results, archived_contents):
    """
    Write the results to markdown file
    """
    content = ''
    with open('README.md', mode='r', encoding='utf-8') as f:
        content = f.read()
    content = convert_file_contenet(content, lang, results, archived_contents)
    with open('README.md', mode='w', encoding='utf-8') as f:
        f.write(content)


def is_title_exist(title, content, archived_contents):
    if '[' + title + ']' in content:
        return True
    for archived_content in archived_contents:
        if '[' + title + ']' in archived_content:
            return True
    return False


def convert_file_contenet(content, lang, results, archived_contents):
    """
    Add distinct results to content
    """
    distinct_results = []
    for title, result in results.items():
        if not is_title_exist(title, content, archived_contents):
            distinct_results.append(result)

    if not distinct_results:
        print('There is no distinct results')
        return content

    lang_title = convert_lang_title(lang)
    if lang_title not in content:
        content = content + lang_title + '\n\n'

    return content.replace(lang_title + '\n\n', lang_title + '\n\n' + convert_result_content(distinct_results))


def convert_result_content(results):
    """
    Format all results to a string
    """
    strdate = datetime.now().strftime('%Y-%m-%d')
    content = ''
    for result in results:
        content = content + u"* 【{strdate}】[{title}]({url}) - {description}\n".format(
            strdate=strdate, title=result['title'], url=result['url'],
            description=format_description(result['description']))
    return content


def format_description(description):
    """
    Remove new line characters
    """
    if not description:
        return ''
    return description.replace('\r', '').replace('\n', '')


def convert_lang_title(lang):
    """
    Lang title
    """
    if lang == '':
        return '## All language'
    return '## ' + lang.capitalize()


def get_archived_contents():
    archived_contents = []
    archived_files = os.listdir('./archived')
    for file in archived_files:
        content = ''
        with open('./archived/' + file, mode='r', encoding='utf-8') as f:
            content = f.read()
        archived_contents.append(content)
    return archived_contents


def format_date2_tg_message(message: dict, lang: str) -> str:
    current_date = datetime.now()

    # 格式化日期为"20201112"形式
    formatted_date = current_date.strftime("%Y%m%d")
    if lang == '':
        lang = 'all'
    if lang == 'c++':
        lang = 'C\+\+'
    if lang == 'c#':
        lang = 'Csharp'
    return (f"`{message['title']}`\n"
            f"`{message['description']}`\n"
            f"[Repo URL]({message['url']})\n"
            f"\#D{formatted_date}\_{lang} \#{lang}")


def check_and_store_db(value: dict, lang: str) -> (dict, bool):
    if lang == '':
        lang = 'all'
    result = database.session.query(GithubTrending).filter_by(title=value['title']).first()
    if result:
        # update trend_count data
        trend_count = result.trend_count
        result.trend_count = trend_count + 1
        database.session.commit()

        print(f"Title: {result.title}, URL: {result.url}, Description: {result.desc},当前仓库已经推送过,做跳过处理")
        return value, True
    # insert to db
    # 获取当前日期
    current_date = datetime.now()

    # 格式化日期为"20201112"形式
    formatted_date = current_date.strftime("%Y-%m-%d")
    data = GithubTrending(
        title=value['title'],
        url=value['url'],
        desc=value['description'],
        trend_date=f"{formatted_date}",
        trend_count=1,
        category=f"{lang}"
    )
    try:
        database.session.add(data)
        database.session.commit()
        print(f"Insert new github trending data successfully!")
    except Exception as e:
        print(f"Error creating new record for github trending data: {data}")
        database.session.rollback()
    return value, False


async def job():
    """
    Get archived contents
    """
    archived_contents = get_archived_contents()

    ''' Start the scrape job
    '''
    languages = ['', 'java', 'python', 'go', 'javascript', 'typescript', 'c', 'c++', 'c#', 'rust', 'html', 'unknown']
    for lang in languages:
        results = scrape_lang(lang)
        # push to telegram bot
        for key, value in results.items():
            value, have_push = check_and_store_db(value, lang)
            if not have_push:
                print(f"发现新的github trending记录,正在推送到telegram 频道...")
                format_data = format_date2_tg_message(value, lang)
                await telegrambot.send_message2bot(format_data)
                await asyncio.sleep(2)
        # release db connection
        database.session.close()
        write_markdown(lang, results, archived_contents)


if __name__ == '__main__':
    asyncio.run(job())
