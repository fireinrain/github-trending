# coding:utf-8
"""Telegram 消息推送与 MarkdownV2 转义工具。"""
import asyncio
import os

from telegram import Bot


def escape_markdown_v2(text: str) -> str:
    """转义 Telegram MarkdownV2 要求的全部特殊字符。"""
    if not text:
        return ''
    special_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join('\\' + ch if ch in special_chars else ch for ch in text)


async def send_message(message: str):
    """推送文本消息到配置的频道/聊天(TG_CHAT_ID)。"""
    bot_token = os.getenv('TG_BOT_TOKEN')
    chat_id = os.getenv('TG_CHAT_ID')
    if not bot_token or not chat_id:
        raise RuntimeError('TG_BOT_TOKEN / TG_CHAT_ID 环境变量未配置,无法推送消息')
    bot = Bot(bot_token)
    async with bot:
        print(message)
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2')


if __name__ == '__main__':
    asyncio.run(send_message('你好'))