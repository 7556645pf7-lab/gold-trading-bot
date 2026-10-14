import MetaTrader5 as mt5
import pandas as pd
import requests
import time

# ===== عدل هنا فقط =====
MT5_LOGIN = 12345678
MT5_PASSWORD = "باسوردك"
MT5_SERVER = "Exness-MT5Real"
TELEGRAM_TOKEN = "حط توكن البوت"
TELEGRAM_CHAT_ID = "حط الايدي مالك"
SYMBOL = "GOLD"  # في اكسنس احيانا اسمه GOLD مو XAUUSD
# =======================

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        response = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        if response.status_code != 200:
            print(f"فشل إرسال التيليجرام: {response.text}")
    except Exception as e:
        print(f"خطأ في الاتصال بالتيليجرام: {e}")

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# الاتصال بمنصة MT5 مع التحقق
if not mt5.initialize(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
    print(f"فشل الاتصال بـ MT5، رمز الخطأ: {mt5.last_error()}")
    quit()

send("✅ بوت الذهب شغال - يرسل توصيات فقط")
last_processed_time = None

while True:
    try:
        rates = mt5.copy_rates(SYMBOL, mt5.TIMEFRAME_M15, 0, 300)
        
        if rates is None or len(rates) == 0:
            print("فشل في جلب البيانات، جاري إعادة المحاولة...")
            time.sleep(60)
            continue

        df = pd.DataFrame(rates)
        df['MA50'] = df['close'].rolling(50).mean()
        df['MA200'] = df['close'].rolling(200).mean()
        df['RSI'] = rsi(df['close'])

        last = df.iloc[-1]
        prev = df.iloc[-2]
        price = last['close']
        current_bar_time = last['time']  # وقت الشمعة لمنع التكرار

        # التأكد من أن الشمعة جديدة ولم يتم إرسال تنبيه لها مسبقاً
        if current_bar_time != last_processed_time:
            # شراء
            if prev['MA50'] < prev['MA200'] and last['MA50'] > last['MA200'] and 50 < last['RSI'] < 70:
                send(f"🟢 *شراء GOLD*\nالسعر: {price:.2f}\nRSI: {last['RSI']:.1f}\nMA: تقاطع صاعد\nالهدف: +150 نقطة\nالستوب: -80 نقطة")
                last_processed_time = current_bar_time

            # بيع
            elif prev['MA50'] > prev['MA200'] and last['MA50'] < last['MA200'] and 30 < last['RSI'] < 50:
                send(f"🔴 *بيع GOLD*\nالسعر: {price:.2f}\nRSI: {last['RSI']:.1f}\nMA: تقاطع هابط\nالهدف: -150 نقطة\nالستوب: +80 نقطة")
                last_processed_time = current_bar_time

    except Exception as e:
        print(f"حدث خطأ أثناء التنفيذ: {e}")

    time.sleep(300)  # يفحص كل 5 دقايق
