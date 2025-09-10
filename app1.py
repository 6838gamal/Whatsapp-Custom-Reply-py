from flask import Flask, request, render_template_string, redirect, url_for
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import json
import os

# ---------------------------
# إعداد Flask و config
# ---------------------------
app = Flask(__name__)
CONFIG_FILE = "config.json"

def ensure_config():
    if not os.path.exists(CONFIG_FILE):
        default = {
            "keywords": [],
            "allowed_groups": [],
            "group_reply_template_ar": "تفضل {user}، سيتم التواصل معك.",
            "group_reply_template_en": "Hi {user}, we will contact you shortly.",
            "twilio_account_sid": "",
            "twilio_auth_token": "",
            "twilio_whatsapp_number": ""
        }
        save_config(default)
        return default
    with open(CONFIG_FILE,"r",encoding="utf-8") as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_FILE,"w",encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

config = ensure_config()
twilio_client = Client(config.get("twilio_account_sid"), config.get("twilio_auth_token"))

# ---------------------------
# Webhook WhatsApp
# ---------------------------
@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    global config
    incoming_msg = request.values.get("Body","").strip()
    sender = request.values.get("From","").strip()  # رقم واتساب
    resp = MessagingResponse()
    msg = resp.message()

    if not incoming_msg:
        return str(resp)

    # تحقق من الكلمات المفتاحية
    matched_kw = None
    for kw in config.get("keywords", []):
        if kw.lower() in incoming_msg.lower():
            matched_kw = kw
            break
    if not matched_kw:
        msg.body("📌 لم أفهم طلبك، حاول مرة أخرى.")
        return str(resp)

    # البحث في allowed_groups
    grp = next((g for g in config.get("allowed_groups", []) if g["id"]==sender), None)

    if grp:
        tpl_kind = grp.get("template","ar")
        if tpl_kind=="custom" and grp.get("custom_reply"):
            tpl = grp.get("custom_reply")
        elif tpl_kind=="en":
            tpl = config.get("group_reply_template_en")
        else:
            tpl = config.get("group_reply_template_ar")

        reply_text = tpl.replace("{user}", sender)

        if grp.get("reply_type")=="private":
            twilio_client.messages.create(
                body=reply_text,
                from_=config["twilio_whatsapp_number"],
                to=sender
            )
            return "", 200
        else:
            msg.body(reply_text)
            return str(resp)
    else:
        # الرد العام إذا لم توجد مجموعة/رقم
        reply_text = config.get("group_reply_template_ar","تفضل {user}").replace("{user}", sender)
        msg.body(reply_text)
        return str(resp)

# ---------------------------
# لوحة التحكم Flask
# ---------------------------
HTML = """<html lang="ar" dir="rtl">
<head><meta charset="utf-8"><title>لوحة تحكم البوت</title></head>
<body>
<h3>⚙️ لوحة تحكم WhatsApp Bot</h3>
<form method="POST" action="/save_all">
<h4>الكلمات المفتاحية</h4>
{% for kw in keywords %}
<input name="kw_{{ loop.index0 }}" value="{{ kw }}"><button name="del_kw" value="{{ kw }}">حذف</button><br>
{% endfor %}
<button name="add_kw" value="1">➕ إضافة كلمة</button><br><br>

<h4>المجموعات / الأشخاص</h4>
{% for g in groups %}
ID: <input name="g_id_{{ loop.index0 }}" value="{{ g['id'] }}">
Name: <input name="g_name_{{ loop.index0 }}" value="{{ g.get('name','') }}">
Type:
<select name="g_type_{{ loop.index0 }}">
<option value="group" {% if g['reply_type']=='group' %}selected{% endif %}>Group</option>
<option value="private" {% if g['reply_type']=='private' %}selected{% endif %}>Private</option>
</select>
Template:
<select name="g_tpl_{{ loop.index0 }}">
<option value="ar" {% if g.get('template','ar')=='ar' %}selected{% endif %}>عربي</option>
<option value="en" {% if g.get('template','ar')=='en' %}selected{% endif %}>English</option>
<option value="custom" {% if g.get('template','ar')=='custom' %}selected{% endif %}>مخصص</option>
</select>
Custom: <input name="g_custom_{{ loop.index0 }}" value="{{ g.get('custom_reply','') }}">
<button name="del_group" value="{{ g['id'] }}">حذف</button><br>
{% endfor %}
<button name="add_group" value="1">➕ إضافة مجموعة</button><br><br>

<h4>قوالب الرد العامة</h4>
العربي:<input name="reply_ar" value="{{ reply_ar }}"><br>
الإنجليزي:<input name="reply_en" value="{{ reply_en }}"><br><br>

<button type="submit">💾 حفظ التعديلات</button>
</form>
</body></html>
"""

@app.route("/", methods=["GET","POST"])
def dashboard():
    global config
    cfg = ensure_config()
    if request.method=="POST":
        # handle keywords
        if 'add_kw' in request.form:
            cfg.setdefault("keywords",[]).append("كلمة جديدة")
        if 'del_kw' in request.form:
            val = request.form.get('del_kw')
            cfg["keywords"] = [k for k in cfg.get("keywords",[]) if k!=val]
        # edit keywords
        new_keywords=[]
        for i in range(len(cfg.get("keywords",[]))):
            v=request.form.get(f"kw_{i}")
            if v and v.strip(): new_keywords.append(v.strip())
        cfg["keywords"]=new_keywords

        # handle groups
        if 'add_group' in request.form:
            cfg.setdefault("allowed_groups",[]).append({"id":"","name":"New Group","reply_type":"group","template":"ar","custom_reply":""})
        if 'del_group' in request.form:
            val=request.form.get('del_group')
            cfg["allowed_groups"]=[g for g in cfg.get("allowed_groups",[]) if g["id"]!=val]

        # edit groups
        new_groups=[]
        for i in range(len(cfg.get("allowed_groups",[]))):
            gid=request.form.get(f"g_id_{i}","").strip()
            name=request.form.get(f"g_name_{i}","").strip()
            rtype=request.form.get(f"g_type_{i}","group")
            tpl=request.form.get(f"g_tpl_{i}","ar")
            custom=request.form.get(f"g_custom_{i}","").strip()
            new_groups.append({"id":gid,"name":name,"reply_type":rtype,"template":tpl,"custom_reply":custom})
        cfg["allowed_groups"]=new_groups

        # replies
        cfg["group_reply_template_ar"]=request.form.get("reply_ar","")
        cfg["group_reply_template_en"]=request.form.get("reply_en","")

        save_config(cfg)
        config = ensure_config()
        return redirect(url_for("dashboard"))

    return render_template_string(HTML, keywords=config.get("keywords",[]), groups=config.get("allowed_groups",[]),
                                  reply_ar=config.get("group_reply_template_ar",""),
                                  reply_en=config.get("group_reply_template_en",""))

# ---------------------------
# Main
# ---------------------------
if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT","5000")))
