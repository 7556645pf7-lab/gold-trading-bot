import MetaTrader5 as mt5
import pandas as pd
import requests
import time
from datetime import datetime
import pytz

MT5_LOGIN = 460243314
MT5_PASSWORD = "Kk@97134774"
MT5_SERVER = "Exness-MT5Real51"
TELEGRAM_TOKEN = "8940976067:AAGo5rkVTr5bg_y8NdcE-0ASoORResLECDg"
TELEGRAM_CHAT_ID = "8581872878"
SYMBOL = "GOLD"

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"خطأ تيليجرام: {e}")

def rsi(s, p=14):
    d = s.diff()
    g = d.where(d > 0, 0).ewm(alpha=1/p, adjust=False).mean()
    l = -d.where(d < 0, 0).ewm(alpha=1/p, adjust=False).mean()
    return 100 - (100 / (1 + g/l))

def get_fib(df, lb=50):
    r = df.tail(lb)
    hi, lo = r['high'].max(), r['low'].min()
    d = hi - lo
    return {"0": lo, "0.25": lo+d*0.25, "0.5": lo+d*0.5, "1": hi, "hi": hi, "lo": lo}

def detect_ob(df):
    c = df.iloc[-3:]
    if c['close'].iloc[-1] > c['open'].iloc[-1] and c['close'].iloc[-2] < c['open'].iloc[-2]:
        return f"✅ Order Block شرائي عند {c['low'].iloc[-2]:.2f}"
    if c['close'].iloc[-1] < c['open'].iloc[-1] and c['close'].iloc[-2] > c['open'].iloc[-2]:
        return f"✅ Order Block بيعي عند {c['high'].iloc[-2]:.2f}"
    return "لا يوجد Order Block واضح"

def detect_trend(df):
    l = df.iloc[-1]
    if l['close'] > l['MA20'] > l['MA50'] > l['MA100'] > l['MA200']: return "📈 ترند صاعد قوي"
    if l['close'] < l['MA20'] < l['MA50'] < l['MA100'] < l['MA200']: return "📉 ترند هابط قوي"
    if l['close'] > l['MA20'] and l['close'] > l['MA50']: return "📈 ترند صاعد قصير"
    if l['close'] < l['MA20'] and l['close'] < l['MA50']: return "📉 ترند هابط قصير"
    return "↔️ عرضي"

if not mt5.initialize(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
    print(f"فشل الاتصال بـ MT5: {mt5.last_error()}")
    quit()

send("✅ بوت GOLD M1 اشتغل - تحليل متقدم (فيبو + موفنجات + RSI + Order Block)")

last_hour = None

while True:
    try:
        now = datetime.now(pytz.timezone('Asia/Muscat'))
        ch = now.strftime("%Y-%m-%d %H:00")

        # يتفعل فور بداية كل ساعة جديدة بدون الحاجة لانتظار الدقيقة صفر بدقة
        if ch != last_hour:
            tick = mt5.symbol_info_tick(SYMBOL)
            price = tick.ask if tick else 0
            
            rates = mt5.copy_rates(SYMBOL, mt5.TIMEFRAME_M1, 0, 250)
            if rates is not None and len(rates) > 0:
                df = pd.DataFrame(rates)
                df['RSI'] = rsi(df['close'])
                df['MA20'] = df['close'].rolling(20).mean()
                df['MA50'] = df['close'].rolling(50).mean()
                df['MA100'] = df['close'].rolling(100).mean()
                df['MA200'] = df['close'].rolling(200).mean()
                
                fib = get_fib(df)
                rsi_v = df['RSI'].iloc[-1]
                trend = detect_trend(df)
                ob = detect_ob(df)

                # 1. تقرير الحالة الساعي
                send(f"""⏰ *تقرير الذهب الساعي (M1)*
📅 {now.strftime('%Y-%m-%d %H:%M')} مسقط
💰 *GOLD: {price:.2f}*

*المؤشرات الفنية:*
RSI: {rsi_v:.1f}
MA20: {df['MA20'].iloc[-1]:.2f} | MA50: {df['MA50'].iloc[-1]:.2f}
MA100: {df['MA100'].iloc[-1]:.2f} | MA200: {df['MA200'].iloc[-1]:.2f}

مستويات فيبو (50 شمعة):
0%: {fib['0']:.2f} | 25%: {fib['0.25']:.2f}
50%: {fib['0.5']:.2f} | 100%: {fib['1']:.2f}

{trend}
{ob}""")

                # 2. فحص صفقات الشراء
                if rsi_v <= 30 and price <= fib['0.25']:
                    send(f"""🟢 *فرصة شراء GOLD M1*
الدخول: {price:.2f}
RSI: {rsi_v:.1f} تشبع بيع
فيبو: عند 0.25 ({fib['0.25']:.2f})
{trend}

🎯 هدف1: {price+5:.2f}
🎯 هدف2: {price+10:.2f}
🛑 ستوب: {price-4:.2f}
{ob}""")

                # 3. فحص صفقات البيع
                elif rsi_v >= 70 and price >= fib['0.5']:
                    send(f"""🔴 *فرصة بيع GOLD M1*
الدخول: {price:.2f}
RSI: {rsi_v:.1f} تشبع شراء
فيبو: عند 0.5 ({fib['0.5']:.2f})
{trend}

🎯 هدف1: {price-5:.2f}
🎯 هدف2: {price-10:.2f}
🛑 ستوب: {price+4:.2f}
{ob}""")

                last_hour = ch

    except Exception as e:
        print(f"حدث خطأ أثناء التنفيذ: {e}")

    time.sleep(30)
