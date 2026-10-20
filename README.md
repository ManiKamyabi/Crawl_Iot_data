# IoT PDF Collector

جمع‌آوری و دانلود خودکار فایل‌های PDF مرتبط با **پروتکل‌های اینترنت اشیا (IoT)** فقط از منابع معتبر و رایگان، با نوار پیشرفت (progress bar) زنده، قابلیت ادامه (resume) و اعتبارسنجی واقعی بودن فایل PDF.

تمرکز موضوعی: MQTT، CoAP، AMQP، 6LoWPAN، RPL، LoRaWAN، NB-IoT، Sigfox، Zigbee، Thread، Matter، BLE، LPWAN، SCHC، امنیت IoT، شبکه‌های حسگر بی‌سیم و ...

---

## منابع پشتیبانی‌شده (همه رایگان و رسمی)

| منبع | نوع محتوا | روش دسترسی |
|---|---|---|
| `arxiv` | پیش‌چاپ‌های علمی (Open Access) | API رسمی export.arxiv.org |
| `rfc_editor` | استانداردهای رسمی IETF (RFC) | پارس rfc-index.txt + PDF رسمی |
| `nist` | نشریات NIST (امنیت IoT و ...) | صفحات CSRC + PDFهای nvlpubs |
| `oasis` | استانداردهای MQTT 5.0، MQTT 3.1.1، AMQP، MQTT-SN، Sparkplug | لینک مستقیم رسمی |
| `lora_alliance` | مشخصات رسمی LoRaWAN L2 1.0.4 و RP002 | توکن دانلود رسمی هاب LoRa Alliance |
| `semantic_scholar` | مقالات Open Access (فقط هاست‌های معتبر) | Graph API رایگان |
| `mdpi` | مقالات ژورنال‌های Sensors، Electronics، IoT، ... | DOAJ + OpenAlex |
| `ietf_datatracker` | اینترنت‌درافت‌های گروه‌های کاری IoT | REST API رسمی Datatracker |

> نکته: سال انتشار مقالات با `--min-year` (پیش‌فرض ۲۰۲۰) فیلتر می‌شود؛ اما استانداردهای مرجع (OASIS، LoRa، NIST) چون سند «مرجعِ» پروتکل هستند و تعدادشان محدود است مستثنی هستند. این مورد در `config.py` قابل تغییر است.

---

## نصب

```bash
# پایتون 3.8+ لازم است
pip install -r requirements.txt
```

## اجرا

```bash
# اجرای کامل (پیش‌فرض: ۶۰ فایل از هر منبع، پوشه pdfs در همین مسیر)
python main.py

# تعداد کمتر برای تست
python main.py --limit 10

# فقط چند منبع خاص
python main.py --sources arxiv rfc_editor nist oasis

# تغییر مسیر خروجی و حداقل سال
python main.py --out D:\iot\pdfs --min-year 2021

# اگر با محدودیت نرخ (429) مواجه شدید، وقفه‌ها را ۲ برابر کنید
python main.py --delay-factor 2.0

# مشاهده منابع موجود
python main.py --list-sources
```

فایل‌ها به‌صورت **یک پوشه‌ی تخت** با پیشوند نام منبع ذخیره می‌شوند:

```
pdfs/
├── arxiv_a_survey_of_mqtt_security_1a2b3c4d.pdf
├── rfc_rfc_9011_schc_over_lorawan_e5f6a7b8.pdf
├── nist_considerations_for_managing_iot_cybersecurity_c9d0e1f2.pdf
├── oasis_mqtt_version_5_0_oasis_standard_3a4b5c6d.pdf
├── lora_ts001_1_0_4_lorawan_l2_1_0_4_specification_7e8f9a0b.pdf
├── mdpi_performance_analysis_of_lorawan_b1c2d3e4.pdf
└── ...
```

---

## ویژگی‌ها

- **نوار پیشرفت دو لایه**: یک نوار کلی برای کل صف دانلود + یک نوار بایتی برای فایل در حال دانلود.
- **Resume خودکار**: اگر برنامه را قطع و دوباره اجرا کنید، فایل‌های سالم قبلی نادیده گرفته می‌شوند و فقط بقیه دانلود می‌شوند (نام فایل‌ها قطعی و بر اساس hash آدرس است).
- **اعتبارسنجی PDF**: فقط فایل‌هایی که امضای `%PDF-` دارند و حداقل ۲۰ کیلوبایت هستند ذخیره می‌شوند؛ صفحات خطای HTML یا چالش‌های Cloudflare خودکار حذف می‌شوند.
- **ادب (Politeness)**: فاصله‌گذاری بین درخواست‌ها به‌ازای هر منبع (مثلاً ۳ ثانیه برای arXiv طبق درخواست رسمی‌شان) + retry خودکار روی خطاهای 429/5xx.
- **عایق‌سازی خطا**: اگر یک منبع مسدود باشد (مثلاً Cloudflare)، بقیه منابع عادی ادامه می‌دهند و در خلاصه پایانی وضعیت هر منبع گزارش می‌شود.
- **بدون فایل جانبی**: هیچ گزارش یا لاگی روی دیسک نوشته نمی‌شود؛ خروجی فقط PDF است (خلاصه آماری در ترمینال چاپ می‌شود).

## عیب‌یابی

| نشانه | دلیل | راه‌حل |
|---|---|---|
| خطای 403 برای MDPI | چالش Cloudflare روی برخی IPها (معمولاً IP سرور/دانشگاه) | از شبکه خانگی اجرا کنید یا بعداً دوباره تلاش کنید |
| خطای 403 برای IETF Datatracker | همان مشکل بالا؛ RFCها از `rfc_editor` کامل پوشش داده می‌شوند | نیازی به اقدام خاص نیست |
| خطاهای 429 (Semantic Scholar) | محدودیت نرخ رایگان | صبر کنید؛ برنامه خودش backoff دارد. برای نرخ بالاتر کلید رایگان از semanticscholar.org بگیرید و در `config.py` مقدار `S2_API_KEY` را بگذارید |
| دانلود کند است | وقفه‌های ادبانه عمدی هستند | `--delay-factor 0.5` را امتحان نکنید (بدون ادب)؛ صبر کنید |
| اجرای دوباره هیچ‌چیز دانلود نمی‌کند | همه فایل‌ها از قبل موجودند (resume) | طبیعی است |

## افزودن منبع جدید

1. پوشه `sources/` را ببینید؛ هر منبع یک کلاس با `discover()` است.
2. کلاس جدید را در `sources/your_source.py` بسازید و در `sources/__init__.py` به `SOURCE_REGISTRY` اضافه کنید.
3. فقط منابعی اضافه کنید که PDFهای رسمی/رایگان ارائه می‌دهند.

## ساختار پروژه

```
iot-pdf-collector/
├── main.py                 # نقطه اجرا: کشف → دانلود → خلاصه
├── config.py               # همه تنظیمات (کلیدواژه‌ها، حد ترافیک، لیست منابع)
├── models.py               # مدل Document و آمار
├── utils.py                # سشن HTTP، نام‌گذاری فایل، اعتبارسنجی PDF
├── downloader.py           # دانلود استریمی با نوارهای پیشرفت tqdm
├── sources/
│   ├── base.py             # کلاس پایه + نوار پیشرفت کشف
│   ├── arxiv.py
│   ├── rfc_editor.py
│   ├── ietf_datatracker.py
│   ├── nist.py
│   ├── mdpi.py
│   ├── semantic_scholar.py
│   ├── oasis.py
│   └── lora_alliance.py
└── requirements.txt
```
