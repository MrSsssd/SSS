
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests
import json
from datetime import datetime
import pandas as pd
import yfinance as yf
import logging
import threading
import time

# تكوين السجلات للتتبع
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# رمز البوت الخاص بك من BotFather
TOKEN = '7787672221:AAHXbufg8K0Ps21A9GRqFeeqd6pszfB5NRA'

# قائمة العملات والأسهم التي نريد تتبعها
CURRENCIES = ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'USDSAR=X']
CRYPTO = ['BTC-USD', 'ETH-USD', 'XRP-USD']
STOCKS = ['^GSPC', '^DJI', '^IXIC']  # S&P 500, Dow Jones, NASDAQ

class TradingBot:
    def __init__(self):
        self.bot = telegram.Bot(token=TOKEN)
        self.updater = Updater(token=TOKEN, use_context=True)
        self.dp = self.updater.dispatcher
        self.subscribed_users = set()
        self.setup_handlers()
        
    def setup_handlers(self):
        """إعداد معالجات الأوامر"""
        self.dp.add_handler(CommandHandler("start", self.start))
        self.dp.add_handler(CommandHandler("help", self.help))
        self.dp.add_handler(CommandHandler("prices", self.get_prices))
        self.dp.add_handler(CommandHandler("crypto", self.get_crypto))
        self.dp.add_handler(CommandHandler("stocks", self.get_stocks))
        self.dp.add_handler(CommandHandler("subscribe", self.subscribe))
        self.dp.add_handler(CommandHandler("unsubscribe", self.unsubscribe))
        self.dp.add_handler(CommandHandler("analysis", self.get_market_analysis))

    async def start(self, update: telegram.Update, context: CallbackContext):
        """رسالة الترحيب"""
        welcome_message = """
🌟 مرحباً بك في بوت التداول المتطور! 

الأوامر المتاحة:
/prices - أسعار العملات الرئيسية
/crypto - أسعار العملات الرقمية
/stocks - مؤشرات الأسهم العالمية
/analysis - تحليل السوق
/subscribe - الاشتراك في التنبيهات
/unsubscribe - إلغاء الاشتراك
/help - المساعدة

⚡️ يتم تحديث الأسعار كل 5 دقائق
📊 تحليلات فنية متقدمة
🔔 تنبيهات فورية للتغيرات المهمة
"""
        await update.message.reply_text(welcome_message)

    async def get_prices(self, update: telegram.Update, context: CallbackContext):
        """جلب أسعار العملات"""
        try:
            message = "💱 أسعار العملات الرئيسية:\n\n"
            for currency in CURRENCIES:
                data = yf.download(currency, period='1d', interval='1m')
                if not data.empty:
                    current_price = data['Close'].iloc[-1]
                    daily_change = ((current_price - data['Open'].iloc[0]) / data['Open'].iloc[0]) * 100
                    message += f"{currency.replace('=X', '')}: {current_price:.4f} ({daily_change:+.2f}%)\n"
            await update.message.reply_text(message)
        except Exception as e:
            await update.message.reply_text(f"عذراً، حدث خطأ: {str(e)}")

    async def get_crypto(self, update: telegram.Update, context: CallbackContext):
        """جلب أسعار العملات الرقمية"""
        try:
            message = "💎 أسعار العملات الرقمية:\n\n"
            for crypto in CRYPTO:
                data = yf.download(crypto, period='1d', interval='1m')
                if not data.empty:
                    current_price = data['Close'].iloc[-1]
                    daily_change = ((current_price - data['Open'].iloc[0]) / data['Open'].iloc[0]) * 100
                    message += f"{crypto.replace('-USD', '')}: ${current_price:,.2f} ({daily_change:+.2f}%)\n"
            await update.message.reply_text(message)
        except Exception as e:
            await update.message.reply_text(f"عذراً، حدث خطأ: {str(e)}")

    async def get_stocks(self, update: telegram.Update, context: CallbackContext):
        """جلب مؤشرات الأسهم"""
        try:
            message = "📈 مؤشرات الأسهم العالمية:\n\n"
            for stock in STOCKS:
                data = yf.download(stock, period='1d', interval='1m')
                if not data.empty:
                    current_price = data['Close'].iloc[-1]
                    daily_change = ((current_price - data['Open'].iloc[0]) / data['Open'].iloc[0]) * 100
                    stock_name = {
                        '^GSPC': 'S&P 500',
                        '^DJI': 'Dow Jones',
                        '^IXIC': 'NASDAQ'
                    }.get(stock, stock)
                    message += f"{stock_name}: {current_price:,.2f} ({daily_change:+.2f}%)\n"
            await update.message.reply_text(message)
        except Exception as e:
            await update.message.reply_text(f"عذراً، حدث خطأ: {str(e)}")

    async def get_market_analysis(self, update: telegram.Update, context: CallbackContext):
        """تحليل السوق"""
        try:
            message = "📊 تحليل السوق:\n\n"
            
            # تحليل مؤشر S&P 500
            sp500 = yf.download('^GSPC', period='5d', interval='1d')
            rsi = self.calculate_rsi(sp500['Close'])
            trend = "صاعد 📈" if sp500['Close'].iloc[-1] > sp500['Close'].iloc[-2] else "هابط 📉"
            
            message += f"🔹 S&P 500:\n"
            message += f"الاتجاه: {trend}\n"
            message += f"مؤشر RSI: {rsi:.2f}\n"
            message += f"المقاومة: {sp500['High'].max():.2f}\n"
            message += f"الدعم: {sp500['Low'].min():.2f}\n\n"
            
            await update.message.reply_text(message)
        except Exception as e:
            await update.message.reply_text(f"عذراً، حدث خطأ في التحليل: {str(e)}")

    def calculate_rsi(self, prices, periods=14):
        """حساب مؤشر RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs)).iloc[-1]

    async def subscribe(self, update: telegram.Update, context: CallbackContext):
        """الاشتراك في التنبيهات"""
        user_id = update.message.from_user.id
        self.subscribed_users.add(user_id)
        await update.message.reply_text("✅ تم الاشتراك في التنبيهات بنجاح!")

    async def unsubscribe(self, update: telegram.Update, context: CallbackContext):
        """إلغاء الاشتراك من التنبيهات"""
        user_id = update.message.from_user.id
        self.subscribed_users.discard(user_id)
        await update.message.reply_text("❌ تم إلغاء الاشتراك من التنبيهات!")

    async def send_alert(self, user_id, message):
        """إرسال تنبيه للمستخدم"""
        try:
            await self.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            logging.error(f"Error sending alert to {user_id}: {str(e)}")

    def check_price_alerts(self):
        """التحقق من تنبيهات الأسعار"""
        while True:
            try:
                for symbol in CURRENCIES + CRYPTO + STOCKS:
                    data = yf.download(symbol, period='5m', interval='1m')
                    if not data.empty:
                        current_price = data['Close'].iloc[-1]
                        price_change = ((current_price - data['Open'].iloc[0]) / data['Open'].iloc[0]) * 100
                        
                        if abs(price_change) >= 1:  # تنبيه عند تغير السعر بنسبة 1% أو أكثر
                            alert_message = f"⚠️ تنبيه مهم!\n{symbol}: تغير السعر بنسبة {price_change:+.2f}%\nالسعر الحالي: {current_price:.4f}"
                            for user_id in self.subscribed_users:
                                self.send_alert(user_id, alert_message)
                
                time.sleep(300)  # التحقق كل 5 دقائق
            except Exception as e:
                logging.error(f"Error in price alerts: {str(e)}")
                time.sleep(60)

    def run(self):
        """تشغيل البوت"""
        # بدء خيط التنبيهات
        alert_thread = threading.Thread(target=self.check_price_alerts)
        alert_thread.daemon = True
        alert_thread.start()
        
        # تشغيل البوت
        self.updater.start_polling()
        self.updater.idle()

if __name__ == '__main__':
    bot = TradingBot()
    print("🚀 بوت التداول قيد التشغيل...")
    bot.run()
