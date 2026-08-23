from telegram import Bot
import os
import asyncio

# Replace 'YOUR_BOT_TOKEN' with the token you received from BotFather
BOT_TOKEN = None
CHAT_ID = None
bot_token = os.getenv('TG_BOT_TOKEN')
chat_id = os.getenv('TG_CHAT_ID')
if bot_token:
    BOT_TOKEN = bot_token
else:
    print(f"you must provide a bot token!")
if chat_id:
    CHAT_ID = chat_id
else:
    print(f"you must provide a chat_id!")


def escape_markdown_v2(text: str) -> str:
    """
    转义 Telegram MarkdownV2 要求的全部特殊字符
    """
    if not text:
        return ''
    special_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join('\\' + ch if ch in special_chars else ch for ch in text)


async def send_message2bot(message: str):
    if not BOT_TOKEN or not CHAT_ID:
        raise RuntimeError("TG_BOT_TOKEN / TG_CHAT_ID 环境变量未配置,无法推送消息")
    bot = Bot(BOT_TOKEN)
    async with bot:
        # print(await bot.get_me())
        print(message)
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="MarkdownV2")


if __name__ == '__main__':
    asyncio.run(send_message2bot("你好"))

