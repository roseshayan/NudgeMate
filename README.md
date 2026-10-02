# 🤖 NudgeMate

> **AI-Powered Voice Reminder & Second Brain Telegram Bot**  
> *دستیار صوتی هوشمند مدیریت تسک، ریمایندر پیگیر و مغز دوم با هوش مصنوعی*

<div align="center">

[![Website](https://img.shields.io/badge/Website-NudgeMate%20Landing-6366f1?style=for-the-badge&logo=googlechrome&logoColor=white)](https://roseshayan.github.io/NudgeMate/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04%20LTS-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)](https://ubuntu.com/)
[![Telegram](https://img.shields.io/badge/Telegram-aiogram%203.x-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://docs.aiogram.dev/)
[![LLM](https://img.shields.io/badge/AI%20Engine-Dahl%20Global-10b981?style=for-the-badge)](https://inference.dahl.global/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

**[🇬🇧 English](#-english) • [🇮🇷 فارسی](#-فارسی)**

</div>

---

<a name="english"></a>
## 🇬🇧 English

### 💡 Why NudgeMate?
For busy people, forgetful minds, or individuals with ADHD, traditional task managers fail because:
1. **High friction input:** Opening an app, typing titles, and tapping date/time pickers takes too long and gets abandoned.
2. **Ignored notifications:** A silent banner notification arrives, you dismiss it, and forget it two minutes later.

**NudgeMate eliminates both problems:**
- **Zero-Friction Voice Notes:** Driving or walking? Send a 5-second voice note (*"Dentist appointment tomorrow at 4 PM"*).
- **Multi-Engine Speech-to-Text:** Instant, highly accurate voice recognition using Google Speech (0% CPU load, free), Groq Cloud Whisper Large V3, or Local Faster-Whisper.
- **AI Task Reasoning:** Powered by **Dahl Global** (`MiniMax M2.7` / `DeepSeek`), understanding relative dates, Jalali & Gregorian calendars, and priority levels.
- **SMS Alerts via MeliPayamak:** If your internet disconnects or Telegram is blocked, NudgeMate sends an instant SMS reminder to your phone!
- **Persistent Nagging Loop:** If you don't mark a task completed or snooze it, NudgeMate follows up every 15 minutes with interactive inline buttons!
- **Mandatory Channel Membership:** Built-in force-join channel middleware to grow your Telegram community.
- **Second Brain Memory:** Tell it *"Remember the safe code is 98765"*. Later ask *"What is my safe code?"* and it instantly recalls it.

### 🎁 Recommended Cloud & SMS Providers

| Service | Provider & Offer | Link |
| :--- | :--- | :--- |
| 🚀 **High-Speed Cloud VPS** | Deploy NudgeMate on Doprax Cloud | [Get VPS on Doprax](https://www.doprax.com/r/sudoshayan/) |
| 📱 **SMS Reminder Panel** | **MeliPayamak** (10% Discount Coupon: `MPDBMRN`) | [Buy Panel on MeliPayamak](https://melipayamak.com/?aff=DBMRN) |

<div align="center">
  <a target="_blank" href="https://melipayamak.com/?aff=DBMRN" title="عضویت در سیستم پیامکی ملی پیامک">
    <img width="728" height="90" src="https://affiliate.melipayamak.com/storage/banners/P4cYEjkHLTPPVkLnn6elgKF20ywr2T0I5OUOKkgq.gif" alt="MeliPayamak Banner">
  </a>
</div>

### 🚀 Quick Interactive Installer (Ubuntu 24.04)

Run either of these commands on your server:

```bash
# Option 1: Fast One-Liner (Recommended)
bash <(curl -sSL https://raw.githubusercontent.com/roseshayan/NudgeMate/main/install.sh)

# Option 2: Download & Run
curl -sSLO https://raw.githubusercontent.com/roseshayan/NudgeMate/main/install.sh && sudo bash install.sh
```

#### What makes this installer special?
- **Zero-friction Dahl AI setup:** Enter your email, and the script automatically registers your account, claims **100 Million Free Gift Tokens**, and allocates them to your API key. (Manual key entry is also supported).
- **Input Validation Loops:** Tests your Telegram Bot token directly with Telegram's API. If anything is mistyped, it alerts you in red and prompts again without crashing the installer!
- **Production-Ready Systemd:** Deploys a background service that auto-restarts on reboot or failure.

---

### 🔄 In-App One-Click Auto Updates

1. **Telegram In-App Update:** Whenever an update is pushed to GitHub, the bot alerts the admin with an inline button: `[ 🚀 Update to vX.X.X ]`. Clicking it downloads the latest code, installs requirements, and reboots the service.
2. **Terminal Shortcut:** Update at any time by running:
   ```bash
   nudgemate-update
   ```

---

### 🛠️ Server CLI Management

```bash
nudgemate status    # Check systemd service status
nudgemate logs      # View live streaming logs
nudgemate restart   # Restart the bot
nudgemate stop      # Stop the service
nudgemate-update    # Pull latest GitHub release
```

---

### 📱 Telegram Bot Commands

| Command | Description |
| :--- | :--- |
| `/start` | Welcome message & register user profile |
| `/lang` | Switch language between English and Persian (فارسی / English) |
| `/tasks` | View pending tasks with action buttons |
| `/notes` | View Second Brain stored memories |
| `/sms` | Configure MeliPayamak SMS reminder alerts |
| `/phone` | Set mobile number for SMS notifications (`/phone 09123456789`) |
| `/admin` | Admin panel to manage tokens, channel & balance (Admin only) |
| `/set_sms_token` | Change MeliPayamak API token directly (`/set_sms_token <token>`) |
| `/set_channel` | Set mandatory channel join (`/set_channel @channel` or `off`) |
| `/sms_credit` | Live inquiry of MeliPayamak SMS wallet balance |
| `/briefing` | Trigger today's daily morning briefing |
| `/stats` | View completion rate and productivity statistics |
| `/update` | Check for updates and trigger remote self-upgrade (Admin only) |
| `/help` | Detailed instructions on voice notes & reminders |

---

<br />

---

<a name="persian"></a>
## 🇮🇷 فارسی

### 💡 چرا NudgeMate؟
آدم‌های پرمشغله یا حواس‌پرت همیشه با دو مشکل اساسی روبرو هستند:
1. **اصطکاک بالا در ثبت کارها:** باز کردن یک اپلیکیشن، تایپ کردن عنوان و انتخاب تاریخ/ساعت وقت‌گیر است و فراموش می‌شود.
2. **بی‌خاصیت بودن نوتیفیکیشن‌های معمولی:** یک آلارم ساده می‌آید، آن را می‌بندید و ۲ دقیقه بعد کار را دوباره از یاد می‌برید!

**NudgeMate این دو مشکل را برای همیشه حل کرده است:**
- **ورودی با ویس (Zero Friction):** فقط یک ویس ۵ ثانیه‌ای به ربات بفرستید: *«فردا ساعت ۴ عصر با دکتر قرار دارم»*.
- **موتور تبدیل صوت چندگانه (Multi-Engine STT):** پشتیبانی از Google Speech (دقت ۱۰۰٪ محاوره فارسی، مصرف صفر درصد CPU)، موتور ابری Groq Whisper Large V3 و ویسپر آفلاین.
- **هوش مصنوعی Dahl Global:** استخراج دقیق موعد، اولویت و دسته‌بندی با مدل‌های پیشرفته MiniMax و DeepSeek و درک تقویم شمسی و اصطلاحات عامیانه.
- **هشدار پیامکی با ملی‌پیامک:** اگر اینترنت قطع بود یا تلگرام فیلتر شد، پیامک هشدار برای گوشی شما ارسال می‌شود!
- **سیستم پیگیری سمج (Nagging):** اگر کار را انجام ندهید یا به تعویق نیندازید، ربات هر ۱۵ دقیقه یک‌بار با دکمه‌های شیشه‌ای مجدداً به شما تلنگر می‌زند!
- **عضویت اجباری در کانال (Force Join):** امکان الزام کاربران به عضویت در کانال تلگرام برای رشد کامیونیتی شما.
- **مغز دوم (Second Brain):** به ربات بگویید *«یادم باشه ماشین رو تو کوچه پنجم پارک کردم»*. هر زمان بعداً بپرسید *«ماشینم کجاست؟»*، هوش مصنوعی پاسخ شما را می‌دهد.

### 🎁 ارائه‌دهندگان سرور و پنل پیامک با تخفیف ویژه

| سرویس | توضیحات و آفر | لینک خرید |
| :--- | :--- | :--- |
| 🚀 **سرور ابری پرسرعت Doprax** | استقرار آسان و سریع NudgeMate | [خرید سرور ابری Doprax](https://www.doprax.com/r/sudoshayan/) |
| 📱 **پنل پیامکی ملی‌پیامک** | ۱۰٪ تخفیف خرید با کوپن اختصاصی: `MPDBMRN` | [خرید پنل ملی‌پیامک](https://melipayamak.com/?aff=DBMRN) |

<div align="center">
  <a target="_blank" href="https://melipayamak.com/?aff=DBMRN" title="عضویت در سیستم پیامکی ملی پیامک">
    <img width="728" height="90" src="https://affiliate.melipayamak.com/storage/banners/P4cYEjkHLTPPVkLnn6elgKF20ywr2T0I5OUOKkgq.gif" alt="بنر ملی‌پیامک">
  </a>
</div>

---

### 🚀 نصب آسان روی اوبونتو 24

می‌توانید از هر یک از دو روش زیر در ترمینال سرور استفاده کنید:

```bash
# روش اول: اجرای تک‌خطی مستقیم (پیشنهادی)
bash <(curl -sSL https://raw.githubusercontent.com/roseshayan/NudgeMate/main/install.sh)

# روش دوم: دانلود و اجرا
curl -sSLO https://raw.githubusercontent.com/roseshayan/NudgeMate/main/install.sh && sudo bash install.sh
```

#### ویژگی‌های نصاب هوشمند:
- **ساخت خودکار اکانت هوش مصنوعی با ایمیل:** نیازی به ثبت‌نام دستی در سایت نیست؛ فقط با وارد کردن یک ایمیل، اکانت شما ساخته شده و **۱۰۰ میلیون توکن رایگان هدیه** به کلید اختصاص می‌یابد! (امکان وارد کردن دستی کلید نیز وجود دارد).
- **حلقه اعتبارسنجی (Validation Loops):** توکن ربات تلگرام در لحظه تست می‌شود و در صورت اشتباه بودن، از قطع شدن نصب جلوگیری کرده و مجدداً سوال می‌پرسد.
- **اجرا به عنوان سرویس پایدار systemd:** پایداری همیشگی و بالا آمدن خودکار پس از ری‌استارت سرور.

---

### 🔄 سیستم آپدیت اتوماتیک

1. **بروزرسانی مستقیم از تلگرام:** با انتشار هر نسخه جدید در گیت‌هاب، ادمین اعلان دریافت کرده و با زدن دکمه `[ 🚀 بروزرسانی به نسخه جدید ]` ربات خود را آپدیت می‌کند.
2. **بروزرسانی از ترمینال سرور:**
   ```bash
   nudgemate-update
   ```

---

### 🛠️ دستورات مدیریت در سرور

```bash
nudgemate status    # بررسی وضعیت سرویس
nudgemate logs      # مشاهده زنده لاگ‌ها
nudgemate config    # ویرایش توکن‌ها و تنظیمات در نانو (.env)
nudgemate restart   # راه‌اندازی مجدد ربات
nudgemate-update    # دانلود و نصب آخرین نسخه گیت‌هاب
```

> 💡 **نکته:** برای تغییر توکن پیامک یا کانال اجباری حتی نیازی به لاگین در سرور ندارید! کافیست در تلگرام به عنوان ادمین دستور `/admin` یا `/set_sms_token` را ارسال کنید.

---

## 📄 لایسنس (License)

این پروژه تحت لایسنس [MIT](LICENSE) به صورت متن‌باز منتشر شده است.  
توسعه‌دهنده: [Shayan (roseshayan)](https://github.com/roseshayan)
