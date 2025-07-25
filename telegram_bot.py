import os
import re
import random
import asyncio
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

# اطلاعات از GitHub Secrets خوانده می‌شود
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
CONFIG_FILE = "working_ss_configs.txt"

def rename_config(config_uri):
    """نام کانفیگ را به @proxyfig تغییر می‌دهد."""
    # با استفاده از یک عبارت منظم، هر چیزی بعد از # را حذف و جایگزین می‌کند
    return re.sub(r'#.*', '#@proxyfig', config_uri)

async def main():
    print("--- Starting Telegram Bot Script ---")
    if not all([BOT_TOKEN, CHANNEL_ID]):
        print("🔴 ERROR: Bot token or channel ID not found in environment variables.")
        return

    print(f"✅ Bot Token and Channel ID are present. Channel ID: {CHANNEL_ID}")

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            configs = [line.strip() for line in f if line.strip()]
        print(f"✅ Successfully read {len(configs)} configs from {CONFIG_FILE}.")
    except FileNotFoundError:
        print(f"🔴 ERROR: Config file '{CONFIG_FILE}' not found. No configs to send.")
        return

    if not configs:
        print("🟡 WARNING: No configs found in the file. Nothing to send.")
        return

    bot = Bot(token=BOT_TOKEN)
    random.shuffle(configs)
    selected_configs = configs[:15]

    # ساخت پیام با فرمت جدید
    # هر کانفیگ در یک بلاک کد جداگانه قرار می‌گیرد
    message_parts = ["✅ **چند کانفیگ شدوساکس جدید:**\n"]
    for config in selected_configs:
        renamed_config = rename_config(config)
        # هر کانفیگ را در یک بلاک کد جدا قرار می‌دهیم
        # این فرمت در تلگرام دکمه کپی را نمایش می‌دهد
        message_parts.append(f"```\n{renamed_config}\n```")
    
    # پیام نهایی با استفاده از دو خط جدید برای جداسازی
    message = "\n\n".join(message_parts)

    print("\n--- Preparing to send message ---")
    print(f"Message length: {len(message)}")
    print(f"Message preview: {message[:200]}...")

    try:
        await bot.send_message(
            chat_id=CHANNEL_ID, 
            text=message, 
            parse_mode=ParseMode.MARKDOWN, # <<-- تغییر به Markdown ساده
            disable_web_page_preview=True # برای جلوگیری از پیش‌نمایش لینک
        )
        print(f"✅✅✅ Successfully sent {len(selected_configs)} configs to {CHANNEL_ID}.")
    except TelegramError as e:
        print(f"🔴🔴🔴 FAILED to send message to Telegram!")
        print(f"Error details: {e}")
    except Exception as e:
        print(f"🔴🔴🔴 An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
