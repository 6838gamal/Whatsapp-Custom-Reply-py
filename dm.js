// استدعاء المكتبات
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

// إنشاء عميل واتساب
const client = new Client({
    authStrategy: new LocalAuth(), // يحفظ تسجيل الدخول محلياً
    puppeteer: { headless: true } // تشغيل بدون متصفح ظاهر
});

// إظهار QR لتسجيل الدخول
client.on('qr', (qr) => {
    qrcode.generate(qr, { small: true });
    console.log("📱 امسح الكود من واتساب للربط");
});

// عند نجاح تسجيل الدخول
client.on('ready', () => {
    console.log('✅ البوت شغال الآن!');
});

// الاستماع للرسائل
client.on('message', async msg => {
    // لو كانت الرسالة من مجموعة
    if (msg.from.endsWith('@g.us')) {
        const chat = await msg.getChat();

        // أسماء أو أرقام المجموعات المسموح فيها
        const allowedGroups = [
            "مجموعة الدعم الفني",      // الاسم
            "مجموعة التجربة",          // الاسم
            "123456789-123456789@g.us" // ID المجموعة
        ];

        // تحقق إذا المجموعة ضمن القائمة
        if (allowedGroups.includes(chat.name) || allowedGroups.includes(chat.id._serialized)) {
            const text = msg.body.toLowerCase();

            // الكلمات المفتاحية
            if (text.includes("اريد مساعدة") || text.includes("هل من شخص يعرف")) {
                msg.reply("تعال خاص ✅");
            }
        }
    }
});

// تشغيل البوت
client.initialize();
