import json
import os
import threading
from flask import Flask, render_template_string, request, redirect, url_for
from pywhatkit.whats import WhatsApp
import pyautogui
import time

# ---------------------------
# تحميل الإعدادات
# ---------------------------
CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default = {
            "keywords": [],
            "allowed_groups": [],
            "group_reply_template_ar": "تفضل {user}، سيتم التواصل معك.",
            "group_reply_template_en": "Hi {user}, we will contact you."
        }
        with open(CONFIG_FILE,"w",encoding="utf-8") as f:
            json.dump(default,f,ensure_ascii=False,indent=2)
        return default
    with open(CONFIG_FILE,"r",encoding="utf-8") as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_FILE,"w",encoding="utf-8") as f:
        json.dump(cfg,f,ensure_ascii=False,indent=2)

config = load_config()

# ---------------------------
# Flask dashboard
# ---------------------------
flask_app = Flask(__name__)
HTML = """
<!doctype html>
<html lang="ar" dir="rtl">
<head><meta charset="utf-8"><title>لوحة تحكم البوت</title></head>
<body>
<h2>لوحة تحكم البوت</h2>
<form method="POST" action="/save_all">
<h3>الكلمات المفتاحية</h3>
{% for kw in keywords %}
<input name="kw_{{loop.index0}}" value="{{kw}}">
<button name="del_kw" value="{{kw}}">حذف</button><br>
{% endfor %}
<button name="add_kw" value="1">إضافة كلمة</button>
<h3>المجموعات/الأرقام المسموحة</h3>
{% for g in groups %}
<input name="g_name_{{loop.index0}}" value="{{g.name}}">
<input name="g_id_{{loop.index0}}" value="{{g.id}}">
<select name="g_type_{{loop.index0}}">
<option value="group" {% if g.reply_type=='group' %}selected{% endif %}>مجموعة</option>
<option value="private" {% if g.reply_type=='private' %}selected{% endif %}>خاص</option>
</select>
<input name="g_custom_{{loop.index0}}" value="{{g.custom_reply}}">
<button name="del_group" value="{{g.id}}">حذف</button><br>
{% endfor %}
<button name="add_group" value="1">إضافة مجموعة/رقم</button>
<h3>قوالب الرد</h3>
<label>عربي:</label><textarea name="reply_ar">{{reply_ar}}</textarea><br>
<label>إنجليزي:</label><textarea name="reply_en">{{reply_en}}</textarea><br>
<button type="submit">حفظ</button>
</form>
</body>
</html>
"""

@flask_app.route("/", methods=["GET","POST"])
def dashboard():
    global config
    if request.method=="POST":
        cfg = config
        # keywords
        if 'add_kw' in request.form:
            cfg.setdefault("keywords",[]).append("كلمة جديدة")
        if 'del_kw' in request.form:
            val = request.form.get('del_kw')
            cfg["keywords"] = [k for k in cfg.get("keywords",[]) if k!=val]
        new_keywords=[]
        for i in range(len(cfg.get("keywords",[]))):
            v = request.form.get(f"kw_{i}")
            if v and v.strip():
                new_keywords.append(v.strip())
        cfg["keywords"]=new_keywords
        # groups
        if 'add_group' in request.form:
            cfg.setdefault("allowed_groups",[]).append({"id":"", "name":"جديد","reply_type":"group","custom_reply":""})
        if 'del_group' in request.form:
            val=request.form.get('del_group')
            cfg["allowed_groups"]=[g for g in cfg.get("allowed_groups",[]) if g["id"]!=val]
        new_groups=[]
        for i,g in enumerate(cfg.get("allowed_groups",[])):
            gid=request.form.get(f"g_id_{i}","")
            name=request.form.get(f"g_name_{i}","")
            rtype=request.form.get(f"g_type_{i}","group")
            custom=request.form.get(f"g_custom_{i}","")
            new_groups.append({"id":gid,"name":name,"reply_type":rtype,"custom_reply":custom})
        cfg["allowed_groups"]=new_groups
        # templates
        cfg["group_reply_template_ar"]=request.form.get("reply_ar","")
        cfg["group_reply_template_en"]=request.form.get("reply_en","")
        save_config(cfg)
        config = load_config()
        return redirect(url_for("dashboard"))
    return render_template_string(HTML, keywords=config.get("keywords",[]),
                                  groups=config.get("allowed_groups",[]),
                                  reply_ar=config.get("group_reply_template_ar",""),
                                  reply_en=config.get("group_reply_template_en",""))

def run_flask():
    flask_app.run(host="0.0.0.0",port=5000)

# ---------------------------
# WhatsApp Bot
# ---------------------------
def start_bot():
    global config
    print("⚡ شغّل البوت، افتح واتساب Web لمسح QR Code...")
    while True:
        # مسح الرسائل (مثال مبسط)
        # هنا يمكنك استخدام أي مكتبة تدعم قراءة الرسائل
        # pywhatsapp أو selenium أو pyautogui
        # كل رسالة جديدة:
        # msg_text = نص الرسالة
        # sender_id = id المرسل
        # chat_id = id المجموعة/الشخص
        # ثم:
        # مطابقة الكلمات المفتاحية
        # إرسال الرد المناسب (خاص أو مجموعة)
        time.sleep(2)

# ---------------------------
# Main
# ---------------------------
if __name__=="__main__":
    threading.Thread(target=run_flask,daemon=True).start()
    start_bot()
