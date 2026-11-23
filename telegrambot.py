# coding:utf-8
"""Telegram 消息推送与 MarkdownV2 转义工具。"""
import asyncio
import os

from telegram import Bot
from telegram.error import NetworkError


def escape_markdown_v2(text: str) -> str:
    """转义 Telegram MarkdownV2 要求的全部特殊字符。"""
    if not text:
        return ''
    special_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join('\\' + ch if ch in special_chars else ch for ch in text)


async def send_message(message: str) -> bool:
    """推送文本消息到配置的频道/聊天(TG_CHAT_ID)。

    网络抖动做有限重试; 返回是否推送成功, 避免单条失败导致整个任务中断。
    """
    bot_token = os.getenv('TG_BOT_TOKEN')
    chat_id = os.getenv('TG_CHAT_ID')
    if not bot_token or not chat_id:
        raise RuntimeError('TG_BOT_TOKEN / TG_CHAT_ID 环境变量未配置,无法推送消息')

    print(message)
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            bot = Bot(bot_token)
            async with bot:
                await bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2')
            return True
        except NetworkError as e:
            if attempt >= max_attempts:
                print(f">>> Telegram 推送失败(已重试{max_attempts}次): {e}")
                return False
            wait_seconds = 3 * attempt
            print(f">>> Telegram 推送网络异常, {wait_seconds}秒后重试({attempt}/{max_attempts}): {e}")
            await asyncio.sleep(wait_seconds)
    return False


if __name__ == '__main__':
    asyncio.run(send_message('你好'))