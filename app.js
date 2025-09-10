// app.js
const fs = require("fs");
const express = require("express");
const { Client, LocalAuth } = require("whatsapp-web.js");
const qrcode = require("qrcode-terminal");
const path = require("path");

// ---------------------------
// Config
// ---------------------------
const CONFIG_FILE = path.join(__dirname, "config.json");

function loadConfig() {
    if (!fs.existsSync(CONFIG_FILE)) {
        const defaultConfig = {
            keywords: ["مرحبا","Hello","مساعدة"],
            allowed_groups: [],
            group_reply_template_ar: "تفضل {user}، سيتم التواصل معك.",
            group_reply_template_en: "Hi {user}, we will contact you shortly."
        };
        fs.writeFileSync(CONFIG_FILE, JSON.stringify(defaultConfig, null, 2), "utf-8");
        return defaultConfig;
    }
    return JSON.parse(fs.readFileSync(CONFIG_FILE, "utf-8"));
}

function saveConfig(cfg) {
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(cfg, null, 2), "utf-8");
}

let config = loadConfig();

// ---------------------------
// WhatsApp Client
// ---------------------------
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: { headless: true }
});

client.on('qr', qr => {
    qrcode.generate(qr, {small: true});
    console.log("QR Code generated, scan it with WhatsApp!");
});

client.on('ready', () => {
    console.log("WhatsApp Client Ready!");
});

client.on('message', async msg => {
    const chatId = msg.from;
    const text = (msg.body || "").toLowerCase();
    const cfg = loadConfig();

    // Check keywords
    if (!cfg.keywords.some(k => text.includes(k.toLowerCase()))) return;

    // Find allowed group/user
    const target = cfg.allowed_groups.find(g => g.id === chatId);
    if (!target) return;

    // Choose template
    let reply = cfg.group_reply_template_ar;
    if (target.template === "en") reply = cfg.group_reply_template_en;
    else if (target.template === "custom" && target.custom_reply) reply = target.custom_reply;

    // Replace {user} placeholder
    const contact = await msg.getContact();
    const userDisplay = contact.pushname || contact.number || "User";
    reply = reply.replace("{user}", userDisplay);

    // Send reply
    if (target.reply_type === "private") {
        const contactId = contact.id._serialized;
        await client.sendMessage(contactId, reply);
        console.log(`Sent private reply to ${contactId}`);
    } else {
        await msg.reply(reply);
        console.log(`Sent group reply in ${chatId}`);
    }
});

client.initialize();

// ---------------------------
// Express Dashboard
// ---------------------------
const app = express();
app.use(express.urlencoded({extended:true}));

const HTML = `
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>لوحة تحكم البوت</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body{background:#f4f6f9;font-family:tahoma;padding:20px}
.card{border-radius:12px;padding:18px}
.table-scroll{max-height:300px;overflow:auto;background:#fff;border-radius:6px}
th.sticky{position:sticky;top:0;background:#0d6efd;color:#fff}
.small-input{width:95%}
</style>
</head>
<body>
<div class="container">
  <h3 class="text-center mb-3">⚙️ لوحة تحكم البوت</h3>

  <form method="POST" action="/save_all">
  <div class="card mb-3">
    <h5>🔑 الكلمات المفتاحية</h5>
    <div class="table-scroll mt-2">
      <table class="table">
        <thead><tr class="sticky"><th>الكلمة</th><th>إجراء</th></tr></thead>
        <tbody>
        <% keywords.forEach(function(kw,i){ %>
          <tr>
            <td><input class="form-control small-input" name="kw_<%=i%>" value="<%=kw%>"></td>
            <td><button class="btn btn-sm btn-danger" name="del_kw" value="<%=kw%>">حذف</button></td>
          </tr>
        <% }); %>
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
        <% allowed_groups.forEach(function(g,i){ %>
          <tr>
            <td><input class="form-control small-input" name="g_name_<%=i%>" value="<%=g.name%>"></td>
            <td><input class="form-control small-input" name="g_id_<%=i%>" value="<%=g.id%>"></td>
            <td>
              <select class="form-select" name="g_type_<%=i%>">
                <option value="group" <%=g.reply_type=='group'?'selected':''%>>Group</option>
                <option value="private" <%=g.reply_type=='private'?'selected':''%>>Private</option>
              </select>
            </td>
            <td>
              <select class="form-select" name="g_tpl_<%=i%>">
                <option value="ar" <%=g.template=='ar'?'selected':''%>>عربي</option>
                <option value="en" <%=g.template=='en'?'selected':''%>>English</option>
                <option value="custom" <%=g.template=='custom'?'selected':''%>>مخصص</option>
              </select>
            </td>
            <td><input class="form-control small-input" name="g_custom_<%=i%>" value="<%=g.custom_reply%>"></td>
            <td><button class="btn btn-sm btn-danger" name="del_group" value="<%=g.id%>">حذف</button></td>
          </tr>
        <% }); %>
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
      <textarea class="form-control" name="reply_ar" rows="3"><%=group_reply_template_ar%></textarea>
    </div>
    <div>
      <label>الرد بالإنجليزي</label>
      <textarea class="form-control" name="reply_en" rows="3"><%=group_reply_template_en%></textarea>
    </div>
  </div>

  <div class="text-end mb-5">
    <button class="btn btn-success" type="submit">💾 حفظ التعديلات</button>
  </div>
  </form>
</div>
</body>
</html>
`;

app.set("view engine","ejs");
app.set("views", __dirname);

app.get("/", (req,res)=>{
    res.render("index", {
        keywords: config.keywords,
        allowed_groups: config.allowed_groups,
        group_reply_template_ar: config.group_reply_template_ar,
        group_reply_template_en: config.group_reply_template_en
    });
});

app.post("/save_all", (req,res)=>{
    const body = req.body;

    // Handle keywords
    if(body.add_kw) config.keywords.push("كلمة جديدة");
    if(body.del_kw) config.keywords = config.keywords.filter(k=>k!==body.del_kw);
    config.keywords = config.keywords.map((k,i)=>body[`kw_${i}`] || k);

    // Handle groups
    if(body.add_group) config.allowed_groups.push({id:"", name:"New Group", reply_type:"group", template:"ar", custom_reply:""});
    if(body.del_group) config.allowed_groups = config.allowed_groups.filter(g=>g.id!==body.del_group);

    config.allowed_groups = config.allowed_groups.map((g,i)=>{
        return {
            id: body[`g_id_${i}`] || g.id,
            name: body[`g_name_${i}`] || g.name,
            reply_type: body[`g_type_${i}`] || g.reply_type,
            template: body[`g_tpl_${i}`] || g.template,
            custom_reply: body[`g_custom_${i}`] || g.custom_reply
        };
    });

    config.group_reply_template_ar = body.reply_ar || config.group_reply_template_ar;
    config.group_reply_template_en = body.reply_en || config.group_reply_template_en;

    saveConfig(config);
    res.redirect("/");
});

app.listen(5000, ()=>console.log("🚀 Dashboard running on http://localhost:5000"));
