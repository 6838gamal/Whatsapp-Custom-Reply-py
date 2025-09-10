#!/bin/bash

# تثبيت pm2
npm install -g pm2

# تثبيت dependencies للبوت
npm install

# تشغيل البوت عبر pm2
pm2 start app.js --name whatsapp-bot

# حفظ الحالة
pm2 save

# تشغيل pm2 startup (Render بيهتم بالريستارت)
pm2 logs
