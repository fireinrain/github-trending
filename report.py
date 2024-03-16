# 当运行时检测当前是否是周日，如果是周日，就额外推送每周热门仓库列表
# 当运行检测当前日期是否是月底最后一天 如果是月底最后一天 则额外推送月热门仓库列表
import asyncio
import calendar
import datetime

import aiohttp


def check_day() -> int:
    today = datetime.date.today()
    if today.weekday() == 6:  # 如果是周日
        if today.day == calendar.monthrange(today.year, today.month)[1]:  # 判断是否是月底最后一天
            return 1  # 周日，月底最后一天
        else:
            return 0  # 周日，不是月底最后一天
    else:
        if today.day == calendar.monthrange(today.year, today.month)[1]:  # 判断是否是月底最后一天
            return 2  # 不是周日，月底最后一天
        else:
            return 3  # 不是周日，不是月底最后一天


async def fetch_trending_data(trending_type: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://github.com/trending?since={trending_type}') as response:
            return await response.text()


async def fetch_trending_list(trending_type: str):
    data = await fetch_trending_data(trending_type)
    # 在这里解析 data 并打印列表
    print(data)


def view_report():
    day = check_day()
    if day == 0:
        view_report_week_trending()
    if day == 1:
        view_report_week_trending()
        view_report_month_trending()
    if day == 2:
        view_report_month_trending()
    if day == 3:
        pass


def view_report_week_trending():
    pass


def view_report_month_trending():
    pass


if __name__ == '__main__':
    asyncio.run(fetch_trending_list())
