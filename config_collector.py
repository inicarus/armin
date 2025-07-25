import json
import re
import base64
import requests
from bs4 import BeautifulSoup

# --- ثابت‌ها ---
SS_PATTERN = r"ss://[^\s\"'<]+"
VALID_OUTPUT_FILE = "working_ss_configs.txt" # برای لیست متنی ساده
BASE64_SUB_FILE = "sub.txt" # برای لینک اشتراک کد شده با Base64
SOURCES_FILE = 'sources.json'

# --- توابع کمکی ---
def decode_base64(encoded_content):
    """محتوای Base64 را با تلاش برای رمزگشایی‌های مختلف، دیکود می‌کند."""
    try:
        if isinstance(encoded_content, str):
            encoded_content = encoded_content.encode('utf-8')
        # اضافه کردن padding در صورت نیاز
        padded_content = encoded_content + b'=' * (-len(encoded_content) % 4)
        return base64.b64decode(padded_content).decode('utf-8')
    except Exception:
        return ""

def is_syntactically_valid(config):
    """
    بررسی می‌کند که آیا یک کانفیگ از نظر ساختاری معتبر است یا خیر.
    این تابع کانفیگ‌های ناقص، بریده شده یا بدشکل را فیلتر می‌کند.
    """
    if not isinstance(config, str) or not config.startswith("ss://"):
        return False
    # فیلتر کردن کانفیگ‌های ناقص که با ... تمام می‌شوند
    if config.endswith("…") or config.endswith("..."):
        return False
    
    content_part = config.split('//')[1]
    
    # بررسی فرمت Base64
    try:
        # حذف نام کانفیگ قبل از دیکود کردن
        if '#' in content_part:
            content_part = content_part.split('#')[0]
            
        decoded_str = decode_base64(content_part)
        if decoded_str:
            # اگر محتوای دیکود شده JSON باشد (برای کانفیگ‌های با پلاگین)
            try:
                json.loads(decoded_str)
                return True
            except json.JSONDecodeError:
                # اگر فرمت user:pass@host:port باشد
                if '@' in decoded_str and ':' in decoded_str.split('@')[0]:
                    return True
        # اگر دیکود نشد، ممکن است فرمت غیر Base64 باشد
        elif '@' in content_part and ':' in content_part.split('@')[0]:
            return True
            
    except Exception:
        return False
        
    return False

# --- توابع مربوط به جمع‌آوری ---
def fetch_from_subscription_links(links):
    """از لینک‌های اشتراک کانفیگ‌های شادوساکس را استخراج می‌کند."""
    configs = set()
    print("Fetching from subscription links...")
    for link in links:
        try:
            response = requests.get(link, timeout=10)
            if response.status_code == 200:
                # ابتدا تلاش برای دیکود کل محتوا به عنوان Base64
                decoded_content = decode_base64(response.content)
                found = re.findall(SS_PATTERN, decoded_content)
                if found:
                    configs.update(found)
                else:
                    # اگر محتوا Base64 نبود، آن را به عنوان لیست متنی ساده در نظر بگیر
                    plain_content = response.text
                    found = re.findall(SS_PATTERN, plain_content)
                    configs.update(found)
        except requests.RequestException as e:
            print(f"  - ERROR fetching {link}: {e}")
    return list(configs)

def scrape_telegram_web_previews(channels):
    """از پیش‌نمایش وب کانال‌های تلگرام کانفیگ‌ها را استخراج می‌کند."""
    configs = set()
    print("Fetching from Telegram web previews...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    for channel in channels:
        try:
            channel_name = channel.replace('@', '')
            url = f"https://t.me/s/{channel_name}"
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                messages = soup.find_all("div", class_="tgme_widget_message_text")
                code_blocks = soup.find_all("code")
                for element in messages + code_blocks:
                    found = re.findall(SS_PATTERN, element.get_text())
                    configs.update(found)
        except requests.RequestException as e:
            print(f"  - ERROR scraping {channel}: {e}")
    return list(configs)

# --- تابع اصلی ---
def main():
    with open(SOURCES_FILE, 'r') as f:
        sources = json.load(f)

    # گام ۱: جمع‌آوری
    print("--- Starting Config Collection ---")
    telegram_configs = scrape_telegram_web_previews(sources['telegram_channels'])
    subscription_configs = fetch_from_subscription_links(sources['subscription_links'])
    
    # ادغام و حذف موارد تکراری
    all_configs = list(set(telegram_configs + subscription_configs))
    print(f"\nCollected {len(all_configs)} unique raw configs.")

    # گام ۲: اعتبارسنجی و فیلتر کردن
    print("\n--- Filtering Syntactically Valid Configs ---")
    valid_configs = [config for config in all_configs if is_syntactically_valid(config)]
    print(f"Found {len(valid_configs)} syntactically valid configs.")

    # گام ۳: ذخیره‌سازی
    if valid_configs:
        # ذخیره کانفیگ‌های معتبر در فرمت لیست متنی ساده
        with open(VALID_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            for config in valid_configs:
                f.write(config + '\n')
        print(f"\nSaved {len(valid_configs)} valid configs to {VALID_OUTPUT_FILE} (plain text).")

        # ایجاد و ذخیره لینک اشتراک Base64
        sub_content = "\n".join(valid_configs)
        encoded_sub = base64.b64encode(sub_content.encode('utf-8')).decode('utf-8')
        with open(BASE64_SUB_FILE, 'w', encoding='utf-8') as f:
            f.write(encoded_sub)
        print(f"Saved Base64 encoded subscription to {BASE64_SUB_FILE}.")
    else:
        print("\nNo valid configs found. Output files will not be updated.")

if __name__ == "__main__":
    main()
