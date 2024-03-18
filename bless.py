from datetime import datetime
import random

import pytz

BLESS_WORDS_DATA = './day-bless.data'
BLESS_WORDS_DATA_SAMPLE = './day-bless.data.sample'


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
    return (f'😄今天是: `{current_date}`,Github热门仓库已推送完毕,快去看看吧:)🎉\n'
            f'🥳每日祝福语: \n'
            f'`{bless_words}`')


if __name__ == '__main__':
    word = generate_bless_word()
    tgchannel = format_bless_for_tgchannel(word)
    print(tgchannel)
