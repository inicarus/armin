import os
import re
import random
import asyncio
from telegram import Bot
from telegram.constants import ParseMode

# اطلاعات از GitHub Secrets خوانده می‌شود
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
CONFIG_FILE = "working_ss_configs.txt"

def rename_and_escape(config_uri):
    """نام کانفیگ را تغییر داده و کاراکترهای خاص را برای MarkdownV2 فرار می‌دهد."""
    renamed = re.sub(r'#.*', '#@proxyfig', config_uri)
    # کاراکترهای خاص در MarkdownV2
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return "".join(['\\' + char if char in escape_chars else char for char in renamed])

async def main():
    if not all([BOT_TOKEN, CHANNEL_ID]):
        print("Bot token or channel ID not found in environment variables.")
        return

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            configs = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Config file '{CONFIG_FILE}' not found. No configs to send.")
        return

    if not configs:
        print("No configs in the file to send.")
        return

    bot = Bot(token=BOT_TOKEN)
    random.shuffle(configs)
    selected_configs = configs[:15]

    message_parts = ["✅ *چند کانفیگ سالم Shadowsocks:*\n"]
    for config in selected_configs:
        formatted_config = rename_and_escape(config)
        message_parts.append(f"`{formatted_config}`")
    
    message = "\n\n".join(message_parts)

    try:
        await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode=ParseMode.MARKDOWN_V2)
        print(f"Successfully sent {len(selected_configs)} configs to {CHANNEL_ID}.")
    except Exception as e:
        print(f"Failed to send message to Telegram: {e}")

if __name__ == "__main__":
    asyncio.run(main())
