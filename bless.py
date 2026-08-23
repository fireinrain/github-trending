from datetime import datetime
import random

import pytz

BLESS_WORDS_DATA = './day-bless.data'
BLESS_WORDS_DATA_SAMPLE = './day-bless.data.sample'


# 生成格式  ¹¹/₂₂的日期
def generate_date_str() -> str:
    now = datetime.now()

    # Format the month and day as strings
    month = now.month  # Full month name as a string
    day = now.strftime('%d')

    superscript_digits = ['⁰', '¹', '²', '³', '⁴', '⁵', '⁶', '⁷', '⁸', '⁹']

    lowerscript_digits = ['₀', '₁', '₂', '₃', '₄', '₅', '₆', '₇', '₈', '₉']

    month_str = ''.join(superscript_digits[int(digit)] for digit in str(month))
    day_str = ''.join(lowerscript_digits[int(digit)] for digit in str(day))
    return f"{month_str}/{day_str}"


def generate_weekday_str() -> str:
    # Define a mapping from normal case to the desired case
    case_mapping = {
        'Monday': 'Mᴏɴᴅᴀʏ',
        'Tuesday': 'Tᴜᴇsᴅᴀʏ',
        'Wednesday': 'Wᴇᴅɴᴇsᴅᴀʏ',
        'Thursday': 'Tʜᴜʀsᴅᴀʏ',
        'Friday': 'Fʀɪᴅᴀʏ',
        'Saturday': 'Sᴀᴛᴜʀᴅᴀʏ',
        'Sunday': 'Sᴜɴᴅᴀʏ'
    }
    current_day = datetime.now().strftime('%A')
    # Return the formatted weekday
    return case_mapping.get(current_day, "Unknown Day")


def add_more_bless_words(words):
    with open(BLESS_WORDS_DATA_SAMPLE, 'r') as f:
        readlines = f.readlines()
        new_lines = []
        for i in readlines:
            if i.strip() == '':
                print(f"发现空行,已做去除处理")
                continue
            else:
                new_lines.append(i.strip() + "\n")
        with open(BLESS_WORDS_DATA, 'w+') as ff:
            ff.writelines(new_lines)


def generate_bless_word() -> str:
    with open(BLESS_WORDS_DATA, 'r') as f:
        readlines = f.readlines()
        choice = random.choice(readlines)
        return choice.strip()


def format_bless_for_tgchannel(bless_words: str) -> str:
    tz = pytz.timezone('Asia/Shanghai')
    # 获取当前时间，并将其转换为北京时间
    beijing_time = datetime.now(tz)

    # 格式化输出北京时间
    formatted_time = beijing_time.strftime("%Y年%m月%d日")
    current_date = formatted_time
    return (f'😄今天是: `{current_date}`,Github热门仓库已推送完毕,快去看看吧:\)🎉\n'
            f'🥳每日祝福语: \n'
            f'`{bless_words}`\n'
            f'\#trending\_end')


def format_bless_for_tgchannel2(bless_words: str, new_trending_count: int, weekly_report_url: str = '') -> str:
    year = datetime.now().year
    date = generate_date_str()
    week = generate_weekday_str()
    content = (f'📅 {year} {date} {week} • Github Trending\n'
               f'\n'
               f'Github热门仓库已推送完毕,共有:`{new_trending_count}`新入榜,快去看看吧:\)🎉\n'
               f'🥳每日祝福语: \n'
               f'`{bless_words}`\n')
    if weekly_report_url:
        content += (f'\n'
                    f'📈 本周热榜周报已新鲜出炉:\n'
                    f'[👉 点击查看本周周报]({weekly_report_url})\n')
        hashtags = '\#trending\_end \#weekly\_report'
    else:
        hashtags = '\#trending\_end'
    return content + f'\n{hashtags}'


if __name__ == '__main__':
    word = generate_bless_word()
    tgchannel = format_bless_for_tgchannel(word)
    print(tgchannel)
    print(generate_weekday_str())
    print(generate_date_str())
    print(format_bless_for_tgchannel2("你好呀",12))
