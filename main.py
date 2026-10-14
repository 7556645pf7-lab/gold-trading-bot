import MetaTrader5 as mt5
import pandas as pd
import requests
import time

# ===== بياناتك النهائية - جاهزة =====
MT5_LOGIN = 460243314
MT5_PASSWORD = "Kk@97134774"
MT5_SERVER = "Exness-MT5Real51"
TELEGRAM_TOKEN = "8940976067:AAGo5rkVTr5bg_y8NdcE-0ASoORResLECDg"
TELEGRAM_CHAT_ID = "8581872878"
SYMBOL = "GOLD"
# =====================================

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"خطأ تيليجرام: {e}")

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

if not mt5.initialize(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
    print(f"فشل MT5: {mt5.last_error()}")
    quit()

send("✅ بوت الذهب @gold_460243314_bot اشتغل - يرسل توصيات فقط")
last_processed_time = None

while True:
    try:
        rates = mt5.copy_rates(SYMBOL, mt5.TIMEFRAME_M15, 0, 300)
        if rates is None or len(rates) == 0:
            time.sleep(60)
            continue
        df = pd.DataFrame(rates)
        df['MA50'] = df['close'].rolling(50).mean()
        df['MA200'] = df['close'].rolling(200).mean()
        df['RSI'] = rsi(df['close'])
        last = df.iloc[-1]
        prev = df.iloc[-2]
        price = last['close']
        current_bar_time = last['time']

        if current_bar_time != last_processed_time:
            if prev['MA50'] < prev['MA200'] and last['MA50'] > last['MA200'] and 50 < last['RSI'] < 70:
                send(f"🟢 *شراء GOLD*\nالسعر: {price:.2f}\nRSI: {last['RSI']:.1f}\nتقاطع صاعد - فريم 15 دقيقة")
                last_processed_time = current_bar_time
            elif prev['MA50'] > prev['MA200'] and last['MA50'] < last['MA200'] and 30 < last['RSI'] < 50:
                send(f"🔴 *بيع GOLD*\nالسعر: {price:.2f}\nRSI: {last['RSI']:.1f}\nتقاطع هابط - فريم 15 دقيقة")
                last_processed_time = current_bar_time
    except Exception as e:
        print(f"خطأ: {e}")
    time.sleep(300)
