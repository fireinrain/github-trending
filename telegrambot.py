from telegram import Bot
import os

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


def send_message2bot(message: str):
    bot = Bot(BOT_TOKEN)
    bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="MarkdownV2")


if __name__ == '__main__':
    send_message2bot("你好")
