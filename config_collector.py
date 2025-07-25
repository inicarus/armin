import json
import re
import base64
import requests
from bs4 import BeautifulSoup

# --- ثابت‌ها ---
# الگو برای پیدا کردن تمام پروتکل‌های رایج (vless, vmess, trojan, ss)
CONFIG_PATTERN = r"(vless|vmess|trojan|ss)://[^\s\"'<]+"
ALL_CONFIGS_FILE = "all_configs.txt"  # نام جدید برای فایل خروجی
BASE64_SUB_FILE = "sub.txt"
SOURCES_FILE = 'sources.json'

# --- توابع کمکی ---
def decode_base64(encoded_content):
    """محتوای Base64 را با مدیریت padding به درستی دیکود می‌کند."""
    try:
        if isinstance(encoded_content, str):
            encoded_content = encoded_content.encode('utf-8')
        padded_content = encoded_content + b'=' * (-len(encoded_content) % 4)
        return base64.b64decode(padded_content).decode('utf-8')
    except Exception:
        return ""

def is_syntactically_valid(config: str) -> bool:
    """
    بررسی می‌کند که آیا یک کانفیگ از نظر ساختاری اولیه معتبر است یا خیر.
    این تابع کانفیگ‌های ناقص، بریده شده یا دارای کاراکترهای نامعتبر را فیلتر می‌کند.
    """
    if not isinstance(config, str):
        return False
    # فیلتر کردن کانفیگ‌های ناقص یا حاوی کاراکترهای HTML
    if config.endswith("…") or "..." in config or "<" in config or ">" in config:
        return False
    # بررسی وجود بخش اصلی کانفیگ
    if "@" not in config:
        # استثنا برای VMess که می‌تواند فقط Base64 باشد
        if "vmess://" in config:
            return True
        return False
    return True

# --- توابع مربوط به جمع‌آوری ---
def fetch_from_sources(sources: dict) -> list:
    """از لینک‌های اشتراک و کانال‌های تلگرام کانفیگ‌ها را استخراج می‌کند."""
    configs = set()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}
    
    # ۱. از لینک‌های اشتراک
    print("Fetching from subscription links...")
    for link in sources.get('subscription_links', []):
        try:
            response = requests.get(link, timeout=15, headers=headers)
            if response.status_code == 200:
                content = response.text
                # ممکن است کل محتوا Base64 باشد، آن را نیز بررسی می‌کنیم
                decoded_content = decode_base64(content)
                found_configs = re.findall(CONFIG_PATTERN, decoded_content or content)
                configs.update(found_configs)
        except requests.RequestException as e:
            print(f"  - ERROR fetching {link}: {e}")

    # ۲. از کانال‌های تلگرام
    print("\nFetching from Telegram web previews...")
    for channel in sources.get('telegram_channels', []):
        try:
            url = f"https://t.me/s/{channel.replace('@', '')}"
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                # در متن پیام و همچنین در بلاک‌های `<code>` جستجو کن
                elements = soup.select('div.tgme_widget_message_text, code')
                for element in elements:
                    found_configs = re.findall(CONFIG_PATTERN, element.get_text(separator="\n"))
                    configs.update(found_configs)
        except requests.RequestException as e:
            print(f"  - ERROR scraping {channel}: {e}")
            
    return list(configs)

# --- تابع اصلی ---
def main():
    """تابع اصلی برای اجرای کل فرآیند."""
    with open(SOURCES_FILE, 'r', encoding='utf-8') as f:
        sources = json.load(f)

    # گام ۱: جمع‌آوری
    print("--- Starting Config Collection ---")
    all_configs = fetch_from_sources(sources)
    print(f"\nCollected {len(all_configs)} unique raw configs.")

    # گام ۲: اعتبارسنجی و فیلتر کردن
    print("\n--- Filtering Syntactically Valid Configs ---")
    valid_configs = list(set([config for config in all_configs if is_syntactically_valid(config)]))
    print(f"Found {len(valid_configs)} syntactically valid configs.")

    # گام ۳: ذخیره‌سازی
    if valid_configs:
        # ذخیره تمام کانفیگ‌های معتبر در فرمت لیست متنی ساده
        with open(ALL_CONFIGS_FILE, 'w', encoding='utf-8') as f:
            for config in valid_configs:
                f.write(config + '\n')
        print(f"\nSaved {len(valid_configs)} valid configs to {ALL_CONFIGS_FILE}.")

        # ایجاد و ذخیره لینک اشتراک Base64
        sub_content = "\n".join(valid_configs)
        encoded_sub = base64.b64encode(sub_content.encode('utf-8')).decode('utf-8')
        with open(BASE64_SUB_FILE, 'w', encoding='utf-8') as f:
            f.write(encoded_sub)
        print(f"Saved Base64 encoded subscription
