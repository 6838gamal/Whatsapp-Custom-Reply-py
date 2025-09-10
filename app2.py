import os, json
from flask import Flask, request, render_template_string, redirect, url_for
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

# إعداد المفاتيح من البيئة
account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
whatsapp_number = os.environ.get("TWILIO_WHATSAPP_NUMBER")
twilio_client = Client(account_sid, auth_token)

CONFIG_FILE = "config.json"

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

app = Flask(__name__)

# -----------------------------
# Webhook للواتساب
# -----------------------------
@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    config = load_config()
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From", "").strip()
    resp = MessagingResponse()

    if not incoming_msg:
        return str(resp)

    matched_kw = next((kw for kw in config["keywords"] if kw.lower() in incoming_msg.lower()), None)
    if not matched_kw:
        return str(resp)

    grp = next((g for g in config["allowed_groups"] if g["id"] == sender), None)
    if grp:
        tpl_kind = grp.get("template", "ar")
        tpl = (grp.get("custom_reply") if tpl_kind == "custom" and grp.get("custom_reply")
               else config["group_reply_template_en"] if tpl_kind == "en"
               else config["group_reply_template_ar"])
        reply_text = tpl.replace("{user}", sender)

        if grp.get("reply_type") == "private":
            twilio_client.messages.create(body=reply_text, from_=whatsapp_number, to=sender)
            return "", 200
        else:
            resp.message(reply_text)
            return str(resp)
    else:
        reply_text = config["group_reply_template_ar"].replace("{user}", sender)
        resp.message(reply_text)
        return str(resp)

# -----------------------------
# لوحة التحكم
# -----------------------------
HTML = """
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>لوحة تحكم البوت</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body {background:#f4f6f9;font-family:tahoma;padding:20px}
.card {border-radius:12px;padding:18px}
.table-scroll {max-height:300px;overflow:auto;background:#fff;border-radius:6px}
th.sticky{position:sticky;top:0;background:#0d6efd;color:#fff}
.small-input{width:95%}
</style>
</head>
<body>
<div class="container">
  <h3 class="text-center mb-3">⚙️ لوحة تحكم البوت</h3>

  <form method="POST" action="/">
  <div class="card mb-3">
    <h5>🔑 الكلمات المفتاحية</h5>
    <div class="table-scroll mt-2">
      <table class="table">
        <thead><tr class="sticky"><th>الكلمة</th><th>إجراء</th></tr></thead>
        <tbody>
        {% for kw in keywords %}
          <tr>
            <td><input class="form-control small-input" name="kw_{{ loop.index0 }}" value="{{ kw }}"></td>
            <td><button class="btn btn-sm btn-danger" name="del_kw" value="{{ kw }}">حذف</button></td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
    <div class="mt-2">
      <button class="btn btn-info" name="add_kw" value="1">➕ إضافة كلمة</button>
    </div>
  </div>

  <div class="card mb-3">
    <h5>📌 المجموعات المسموحة</h5>
    <div class="table-scroll mt-2">
      <table class="table">
        <thead><tr class="sticky"><th>الاسم</th><th>ID</th><th>نوع</th><th>قالب</th><th>رد مخصص</th><th>إجراء</th></tr></thead>
        <tbody>
        {% for g in groups %}
          <tr>
            <td><input class="form-control small-input" name="g_name_{{ loop.index0 }}" value="{{ g.get('name','') }}"></td>
            <td><input class="form-control small-input" name="g_id_{{ loop.index0 }}" value="{{ g['id'] }}"></td>
            <td>
              <select class="form-select" name="g_type_{{ loop.index0 }}">
                <option value="group" {% if g['reply_type']=='group' %}selected{% endif %}>Group</option>
                <option value="private" {% if g['reply_type']=='private' %}selected{% endif %}>Private</option>
              </select>
            </td>
            <td>
              <select class="form-select" name="g_tpl_{{ loop.index0 }}">
                <option value="ar" {% if g.get('template','ar')=='ar' %}selected{% endif %}>عربي</option>
                <option value="en" {% if g.get('template')=='en' %}selected{% endif %}>English</option>
                <option value="custom" {% if g.get('template')=='custom' %}selected{% endif %}>مخصص</option>
              </select>
            </td>
            <td><input class="form-control small-input" name="g_custom_{{ loop.index0 }}" value="{{ g.get('custom_reply','') }}"></td>
            <td><button class="btn btn-sm btn-danger" name="del_group" value="{{ g['id'] }}">حذف</button></td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
    <div class="mt-2">
      <button class="btn btn-info" name="add_group" value="1">➕ إضافة مجموعة</button>
    </div>
  </div>

  <div class="card mb-3">
    <h5>💬 قوالب الرد العامة</h5>
    <div class="mb-2">
      <label>الرد بالعربي</label>
      <textarea class="form-control" name="reply_ar" rows="3">{{ reply_ar }}</textarea>
    </div>
    <div>
      <label>الرد بالإنجليزي</label>
      <textarea class="form-control" name="reply_en" rows="3">{{ reply_en }}</textarea>
    </div>
  </div>

  <div class="text-end mb-5">
    <button class="btn btn-success" type="submit">💾 حفظ التعديلات</button>
  </div>
  </form>

  <div class="text-center text-muted"><small>تم التطوير بواسطة Gamal Almaqtary</small></div>
</div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def dashboard():
    cfg = load_config()
    if request.method == "POST":
        if 'add_kw' in request.form:
            cfg["keywords"].append("كلمة جديدة")
        if 'del_kw' in request.form:
            val = request.form.get('del_kw')
            cfg["keywords"] = [k for k in cfg["keywords"] if k != val]
        new_keywords = []
        for i in range(len(cfg["keywords"])):
            v = request.form.get(f"kw_{i}")
            if v and v.strip():
                new_keywords.append(v.strip())
        cfg["keywords"] = new_keywords

        if 'add_group' in request.form:
            cfg["allowed_groups"].append({"id": "0", "name": "New Group", "reply_type": "group", "template": "ar", "custom_reply": ""})
        if 'del_group' in request.form:
            gid_del = request.form.get('del_group')
            cfg["allowed_groups"] = [g for g in cfg["allowed_groups"] if g["id"] != gid_del]

        new_groups = []
        for i in range(len(cfg["allowed_groups"])):
            gid_raw = request.form.get(f"g_id_{i}","").strip()
            name = request.form.get(f"g_name_{i}","").strip()
            rtype = request.form.get(f"g_type_{i}","group")
            tpl = request.form.get(f"g_tpl_{i}","ar")
            custom = request.form.get(f"g_custom_{i}","").strip()
            new_groups.append({"id": gid_raw, "name": name, "reply_type": rtype, "template": tpl, "custom_reply": custom})
        cfg["allowed_groups"] = new_groups

        cfg["group_reply_template_ar"] = request.form.get("reply_ar","").strip()
        cfg["group_reply_template_en"] = request.form.get("reply_en","").strip()
        save_config(cfg)
        return redirect(url_for("dashboard"))

    return render_template_string(HTML,
        keywords=cfg.get("keywords", []),
        groups=cfg.get("allowed_groups", []),
        reply_ar=cfg.get("group_reply_template_ar",""),
        reply_en=cfg.get("group_reply_template_en","")
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
