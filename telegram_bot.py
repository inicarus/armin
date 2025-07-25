import os
import re
import random
import asyncio
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

# --- ثابت‌ها ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
CONFIG_FILE = "all_configs.txt"  # <<-- نام فایل به روز شد

def escape_markdown_v2(text):
    """کاراکترهای خاص را برای MarkdownV2 فرار می‌دهد."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def process_config(config_uri):
    """نام کانفیگ را تغییر داده و آن را برای ارسال در تلگرام آماده می‌کند."""
    # ۱. تغییر نام کانفیگ
    renamed_config = re.sub(r'#.*', '#@proxyfig', config_uri)
    # ۲. فرار دادن کاراکترهای خاص
    return escape_markdown_v2(renamed_config)

async def main():
    print("--- Starting Telegram Bot Script ---")
    if not all([BOT_TOKEN, CHANNEL_ID]):
        print("🔴 ERROR: Bot token or channel ID not found.")
        return

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            configs = [line.strip() for line in f if line.strip()]
        print(f"✅ Successfully read {len(configs)} configs from {CONFIG_FILE}.")
    except FileNotFoundError:
        print(f"🔴 ERROR: Config file '{CONFIG_FILE}' not found.")
        return

    if not configs:
        print("🟡 WARNING: No configs found in the file. Nothing to send.")
        return

    bot = Bot(token=BOT_TOKEN)
    random.shuffle(configs)
    selected_configs = configs[:15]

    # ساخت پیام با فرمت کد بلاک و آماده برای MarkdownV2
    message_parts = [escape_markdown_v2("✅ چند کانفیگ جدید برای شما:\n")]
    for config in selected_configs:
        processed_config = process_config(config)
        # فرمت صحیح برای کد بلاک در MarkdownV2
        message_parts.append(f"```{processed_config}```")
    
    message = "\n\n".join(message_parts)

    print("\n--- Preparing to send message ---")
    try:
        await bot.send_message(
            chat_id=CHANNEL_ID, 
            text=message, 
            parse_mode=ParseMode.MARKDOWN_V2, # <<-- تغییر به MarkdownV2
            disable_web_page_preview=True
        )
        print(f"✅✅✅ Successfully sent {len(selected_configs)} configs to {CHANNEL_ID}.")
    except TelegramError as e:
        print(f"🔴🔴🔴 FAILED to send message to Telegram! Error: {e}")
    except Exception as e:
        print(f"🔴🔴🔴 An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
