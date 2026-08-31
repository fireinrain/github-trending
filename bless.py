# coding:utf-8
"""每日祝福语: 随机文案、日期/星期格式化与当日推送结束消息。"""
import random
from datetime import datetime, timedelta

from telegrambot import escape_markdown_v2

BLESS_WORDS_DATA = './day-bless.data'

# 上标/下标数字, 用于拼装 ⁰⁸/₂₈ 风格的日期
SUPERSCRIPT_DIGITS = ['⁰', '¹', '²', '³', '⁴', '⁵', '⁶', '⁷', '⁸', '⁹']
SUBSCRIPT_DIGITS = ['₀', '₁', '₂', '₃', '₄', '₅', '₆', '₇', '₈', '₉']

WEEKDAY_DISPLAY = {
    'Monday': 'Mᴏɴᴅᴀʏ',
    'Tuesday': 'Tᴜᴇsᴅᴀʏ',
    'Wednesday': 'Wᴇᴅɴᴇsᴅᴀʏ',
    'Thursday': 'Tʜᴜʀsᴅᴀʏ',
    'Friday': 'Fʀɪᴅᴀʏ',
    'Saturday': 'Sᴀᴛᴜʀᴅᴀʏ',
    'Sunday': 'Sᴜɴᴅᴀʏ',
}


def get_safe_week_range() -> str:
    """本周(周一~周日)范围的 MarkdownV2 转义文案, 例如 '2026-08-24 ~ 2026-08-30'。"""
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return escape_markdown_v2(f'{monday} ~ {sunday}')


def generate_date_str() -> str:
    """生成上标月/下标日风格的日期(如 ⁰⁸/₂₈)。"""
    now = datetime.now()
    month_str = ''.join(SUPERSCRIPT_DIGITS[int(digit)] for digit in str(now.month))
    day_str = ''.join(SUBSCRIPT_DIGITS[int(digit)] for digit in now.strftime('%d'))
    return f'{month_str}/{day_str}'


def generate_weekday_str() -> str:
    """生成特殊大小写风格的星期(如 Fʀɪᴅᴀʏ)。"""
    current_day = datetime.now().strftime('%A')
    return WEEKDAY_DISPLAY.get(current_day, 'Unknown Day')


def generate_bless_word() -> str:
    """从语料库随机选取一行祝福语。"""
    with open(BLESS_WORDS_DATA, 'r') as f:
        readlines = f.readlines()
    return random.choice(readlines).strip()


def format_daily_bless_message(bless_words: str, new_trending_count: int,
                               weekly_report_url: str = '') -> str:
    """组装每日推送结束消息; 传入周报地址时附带周报入口与周报话题标签。"""
    year = datetime.now().year
    content = (f'📅 {year} {generate_date_str()} {generate_weekday_str()} • Github Trending\n'
               f'\n'
               f'Github热门仓库已推送完毕,共有:`{new_trending_count}`新入榜,快去看看吧:\\)🎉\n'
               f'🥳每日祝福语: \n'
               f'`{bless_words}`\n')
    if weekly_report_url:
        week_range = get_safe_week_range()
        content += (f'\n'
                    f'📈 本周热榜周报已新鲜出炉\\({week_range}\\):\n'
                    f'[👉 点击查看本周周报]({weekly_report_url})\n')
        hashtags = '\\#trending\\_end \\#weekly\\_report'
    else:
        hashtags = '\\#trending\\_end'
    return content + f'\n{hashtags}'


if __name__ == '__main__':
    print(format_daily_bless_message(generate_bless_word(), 12))
    print(generate_weekday_str())
    print(generate_date_str())