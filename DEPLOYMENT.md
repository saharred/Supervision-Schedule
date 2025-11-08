# 🚀 دليل النشر على GitHub و Streamlit Cloud
## Deployment Guide

---

## الطريقة 1: النشر على Streamlit Cloud (موصى به) ☁️

### الخطوة 1: رفع المشروع على GitHub

```bash
# إنشاء مستودع جديد على GitHub
# اذهب إلى github.com وأنشئ مستودع جديد باسم "supervision-schedule"

# في مجلد المشروع
cd supervision-schedule
git init
git add .
git commit -m "Initial commit: Exam supervision schedule app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/supervision-schedule.git
git push -u origin main
```

### الخطوة 2: النشر على Streamlit Cloud

1. اذهب إلى [share.streamlit.io](https://share.streamlit.io)
2. سجّل الدخول بحساب GitHub
3. اضغط "New app"
4. اختر:
   - **Repository**: `YOUR_USERNAME/supervision-schedule`
   - **Branch**: `main`
   - **Main file path**: `app.py`
5. اضغط "Deploy!"

### الخطوة 3: الانتظار

- سيستغرق النشر 2-5 دقائق
- ستحصل على رابط عام مثل: `https://supervision-schedule.streamlit.app`

---

## الطريقة 2: التشغيل المحلي 💻

### على Windows

```bash
# فتح Command Prompt أو PowerShell
cd path\to\supervision-schedule
pip install -r requirements.txt
streamlit run app.py
```

### على Mac/Linux

```bash
# فتح Terminal
cd /path/to/supervision-schedule
pip3 install -r requirements.txt
streamlit run app.py
```

---

## الطريقة 3: النشر على خادم خاص 🖥️

### استخدام Docker (اختياري)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
# بناء وتشغيل
docker build -t supervision-schedule .
docker run -p 8501:8501 supervision-schedule
```

---

## ⚙️ إعدادات Streamlit Cloud

### ملف .streamlit/config.toml (اختياري)

```toml
[theme]
primaryColor = "#8B0000"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
headless = true
port = 8501
```

### ملف .streamlit/secrets.toml (للبيانات الحساسة)

```toml
# إذا كنت تحتاج إلى مفاتيح API أو كلمات مرور
# لا ترفع هذا الملف على GitHub!

[passwords]
admin_password = "your_password_here"
```

---

## 🔒 الأمان

### ملف .gitignore

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Streamlit
.streamlit/secrets.toml

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Data
*.xlsx
*.xls
*.pdf
!data_samples/*.xlsx
```

---

## 📊 المراقبة والصيانة

### على Streamlit Cloud

1. **عرض السجلات (Logs)**:
   - اذهب إلى لوحة التحكم
   - اضغط على التطبيق
   - اضغط "Manage app" → "Logs"

2. **إعادة التشغيل**:
   - اضغط "Reboot app" من القائمة

3. **التحديثات**:
   - أي push جديد على GitHub سيُحدّث التطبيق تلقائياً

---

## 🔄 التحديثات المستقبلية

### إضافة ميزات جديدة

```bash
# تعديل الكود محلياً
# اختبار التعديلات
streamlit run app.py

# رفع التحديثات
git add .
git commit -m "Add new feature: ..."
git push origin main

# سيتم التحديث تلقائياً على Streamlit Cloud
```

---

## 🌐 الوصول العام

بعد النشر على Streamlit Cloud:

### مشاركة الرابط

```
https://supervision-schedule.streamlit.app
```

### تضمين في موقع

```html
<iframe 
  src="https://supervision-schedule.streamlit.app/?embedded=true" 
  width="100%" 
  height="800px"
  frameborder="0">
</iframe>
```

---

## 📱 الوصول من الهاتف

التطبيق يعمل على:
- ✅ الكمبيوتر
- ✅ التابلت
- ✅ الهاتف المحمول

الواجهة متجاوبة وتدعم جميع الأحجام.

---

## 🆘 حل مشاكل النشر

### المشكلة: "Module not found"
```bash
# تأكد من وجود جميع المكتبات في requirements.txt
pip freeze > requirements.txt
```

### المشكلة: "Port already in use"
```bash
# استخدم منفذ مختلف
streamlit run app.py --server.port=8502
```

### المشكلة: "Permission denied"
```bash
# على Linux/Mac
chmod +x app.py
```

---

## 📞 الدعم

للمساعدة في النشر:
- 📧 Sahar.Osman@education.qa
- 📚 [Streamlit Documentation](https://docs.streamlit.io)
- 🐙 [GitHub Guides](https://guides.github.com)

---

## ✅ قائمة التحقق قبل النشر

- [ ] اختبار التطبيق محلياً
- [ ] التأكد من عمل جميع الميزات
- [ ] مراجعة ملف requirements.txt
- [ ] إضافة .gitignore
- [ ] كتابة README واضح
- [ ] إزالة البيانات الحساسة
- [ ] اختبار على أجهزة مختلفة

---

**جاهز للنشر؟ انطلق! 🚀**

