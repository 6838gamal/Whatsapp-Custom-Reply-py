import json
import os
import time
import threading
from flask import Flask, render_template_string, request, redirect
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

CONFIG_FILE = "config.json"
COOKIES_FILE = "cookies.json"
driver = None
config = {}

# ------------------- إعداد -------------------

def load_config():
    global config
    if not os.path.exists(CONFIG_FILE):
        config = {
            "bot_number": "",
            "keywords": ["مساعدة", "Hello"],
            "allowed_groups": [],
            "reply_private_ar": "مرحباً {user}، كيف أقدر أساعدك؟",
            "reply_private_en": "Hi {user}, how can I help you?",
            "reply_group_ar": "تفضل {user}، سيتم التواصل معك قريباً.",
            "reply_group_en": "Hi {user}, we will contact you shortly.",
            "enable_private": True,
            "enable_groups": True
        }
        save_config()
    else:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)

def save_config():
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def save_cookies():
    cookies = driver.get_cookies()
    with open(COOKIES_FILE, "w", encoding="utf-8") as f:
        json.dump(cookies, f)

def load_cookies():
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        for cookie in cookies:
            driver.add_cookie(cookie)

def start_driver():
    global driver
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get("https://web.whatsapp.com")

    if os.path.exists(COOKIES_FILE):
        driver.delete_all_cookies()
        load_cookies()
        driver.refresh()
        time.sleep(10)
    else:
        print("🔑 امسح QR Code في أول مرة (30 ثانية)...")
        time.sleep(30)
        save_cookies()
        print("✅ تم حفظ الجلسة.")

# ------------------- تشغيل البوت -------------------

def run_bot():
    load_config()
    start_driver()
    print("🚀 البوت شغال...")

    while True:
        try:
            messages = driver.find_elements(By.CSS_SELECTOR, "span.selectable-text")
            if messages:
                last_msg = messages[-1].text.strip()
                print("📩 آخر رسالة:", last_msg)

                # الرد حسب نوع الرسالة
                for kw in config.get("keywords", []):
                    if kw.lower() in last_msg.lower():
                        box = driver.find_element(By.CSS_SELECTOR, "div[title='Type a message']")
                        
                        # خاص أو مجموعة
                        if config.get("enable_groups", True):
                            reply = config.get("reply_group_ar", "تفضل {user}")
                        else:
                            reply = config.get("reply_private_ar", "مرحباً {user}")
                        
                        box.send_keys(reply)
                        send_btn = driver.find_element(By.CSS_SELECTOR, "span[data-icon='send']")
                        send_btn.click()
                        print("✅ تم إرسال الرد:", reply)
                        time.sleep(5)
            time.sleep(3)
        except Exception as e:
            print("⚠️ خطأ:", e)
            time.sleep(5)

# ------------------- لوحة التحكم Flask -------------------

app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html lang="ar">
<head>
  <meta charset="UTF-8">
  <title>لوحة التحكم للبوت</title>
  <style>
    body { font-family: Tahoma; background: #f2f2f2; padding:20px; }
    .card { background:white; padding:20px; border-radius:12px; margin-bottom:20px; box-shadow:0 0 5px #ccc; }
    input, textarea { width:100%; padding:8px; margin:5px 0; }
    button { padding:10px 20px; border:none; background:#2e86de; color:white; border-radius:8px; cursor:pointer; }
    label { font-weight: bold; display:block; margin-top:10px; }
  </style>
</head>
<body>
  <h2>لوحة التحكم للبوت</h2>
  <form method="POST">
    <div class="card">
      <h3>إعداد الرقم</h3>
      <label>رقم البوت</label>
      <input type="text" name="bot_number" value="{{ bot_number }}">
    </div>
    <div class="card">
      <h3>الكلمات المفتاحية</h3>
      <textarea name="keywords">{{ keywords }}</textarea>
    </div>
    <div class="card">
      <h3>المجموعات المسموح بها</h3>
      <textarea name="groups">{{ groups }}</textarea>
    </div>
    <div class="card">
      <h3>قوالب الرد (خاص)</h3>
      <label>عربي</label>
      <input type="text" name="reply_private_ar" value="{{ reply_private_ar }}">
      <label>English</label>
      <input type="text" name="reply_private_en" value="{{ reply_private_en }}">
    </div>
    <div class="card">
      <h3>قوالب الرد (مجموعات)</h3>
      <label>عربي</label>
      <input type="text" name="reply_group_ar" value="{{ reply_group_ar }}">
      <label>English</label>
      <input type="text" name="reply_group_en" value="{{ reply_group_en }}">
    </div>
    <div class="card">
      <h3>خيارات التفعيل</h3>
      <label><input type="checkbox" name="enable_private" {% if enable_private %}checked{% endif %}> الرد على الخاص</label>
      <label><input type="checkbox" name="enable_groups" {% if enable_groups %}checked{% endif %}> الرد على المجموعات</label>
    </div>
    <button type="submit">💾 حفظ</button>
  </form>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def dashboard():
    if request.method == "POST":
        config["bot_number"] = request.form["bot_number"]
        config["keywords"] = [k.strip() for k in request.form["keywords"].split(",")]
        config["allowed_groups"] = [g.strip() for g in request.form["groups"].split(",")]
        config["reply_private_ar"] = request.form["reply_private_ar"]
        config["reply_private_en"] = request.form["reply_private_en"]
        config["reply_group_ar"] = request.form["reply_group_ar"]
        config["reply_group_en"] = request.form["reply_group_en"]
        config["enable_private"] = "enable_private" in request.form
        config["enable_groups"] = "enable_groups" in request.form
        save_config()
        return redirect("/")
    return render_template_string(
        TEMPLATE,
        bot_number=config.get("bot_number", ""),
        keywords=", ".join(config.get("keywords", [])),
        groups=", ".join(config.get("allowed_groups", [])),
        reply_private_ar=config.get("reply_private_ar", ""),
        reply_private_en=config.get("reply_private_en", ""),
        reply_group_ar=config.get("reply_group_ar", ""),
        reply_group_en=config.get("reply_group_en", ""),
        enable_private=config.get("enable_private", True),
        enable_groups=config.get("enable_groups", True),
    )

def run_dashboard():
    app.run(port=5000, debug=False)

# ------------------- تشغيل متوازي -------------------

if __name__ == "__main__":
    load_config()
    threading.Thread(target=run_bot, daemon=True).start()
    run_dashboard()
