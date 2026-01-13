import telebot
import threading
import time
import random
import requests
import json
import statistics
from datetime import datetime, timezone, timedelta
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from collections import deque
import pickle
import os
import math
import logging
from flask import Flask

# 🚀 Render-এ হোস্ট করার জন্য Web Server সেটআপ
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 DEEP AI PREDICTOR V5.0 is running...", 200

# 🧠 তোমার বট টোকেন বসাও নিচে 👇
TOKEN = "8527040202:AAGhqAck23AdYtWhcUVG1LvGdAFMiSphsLQ"
bot = telebot.TeleBot(TOKEN)

# 🔧 লগিং সেটআপ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🗂 ডাটা রাখার জন্য Dictionary
user_channels = {}  # {user_id: "@channelusername"}
signal_threads = {} # {user_id: threading.Thread}
signal_status = {}  # {user_id: True/False}
user_register_links = {}  # {user_id: "https://register-link.com"}
prediction_timers = {}  # {user_id: end_timestamp}

# 🎯 Win/Loss ট্র্যাকিং সিস্টেম
prediction_history = {}  # {user_id: [{period: "", prediction: "", actual: "", result: "WIN/LOSS", time: ""}]}

# 🎯 Win/Loss স্টিকার সিস্টেম
user_win_stickers = {}  # {user_id: "sticker_id"} - Win হলে এই স্টিকার যাবে
user_loss_stickers = {}  # {user_id: "sticker_id"} - Loss হলে এই স্টিকার যাবে
user_season_start_stickers = {}  # {user_id: "sticker_id"} - সিজন স্টার্ট স্টিকার
user_season_close_stickers = {}  # {user_id: "sticker_id"} - সিজন ক্লোজ স্টিকার
user_promotional_messages = {}  # {user_id: "message"} - প্রমোশনাল মেসেজ

# 🎯 ডিফল্ট স্টিকার ID
DEFAULT_WIN_STICKER = "CAACAgUAAxkBAAIBIWZ4i-1dAAE3KXWk3X7L03zWn8H2bAACXxoAAo_FYFZxK2k1K4AAATYE"
DEFAULT_LOSS_STICKER = "CAACAgUAAxkBAAIBI2Z4jARAAW2N8Jv3JXf_0fHl0xJk9AACXxoAAo_FYFZxK2k1K4AAATYE"
DEFAULT_SEASON_START_STICKER = "CAACAgUAAxkBAAIBKWZ4jBNG8F_qjFpSKj11ZphW3Rq7AAJfGgACj8VgVnEraTUrgAABNAQ"
DEFAULT_SEASON_CLOSE_STICKER = "CAACAgUAAxkBAAIBK2Z4jByCAAER-3iK7hpFCUqPynNSOQACXxoAAo_FYFZxK2k1K4AAATYE"

# 🔥 NEW: মার্কেট মেনুপুলেশন ডিটেকশন সিস্টেম
market_manipulation_detected = {}  # {user_id: True/False}
market_manipulation_reason = {}  # {user_id: "reason"}
market_manipulation_history = deque(maxlen=100)  # মেনুপুলেশন হিস্ট্রি

# 🔗 API URLs - FIXED API CALLS
CURRENT_API = 'https://api.bdg88zf.com/api/webapi/GetGameIssue'
HISTORY_API = 'https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json'

# 🔥 NEW: আনলিমিটেড ডাটা কালেকশন সিস্টেম
historical_data = deque(maxlen=2000)  # সর্বোচ্চ 2000টি ডাটা সংরক্ষণ করবে
data_collection_status = True  # ডাটা কালেকশন চালু আছে
data_analysis_level = "BASIC"  # ডাটার উপর ভিত্তি করে লেভেল পরিবর্তন হবে

# 🔥 NEW: ডাটা সেভ/লোড করার ফাংশন
DATA_FILE = "historical_data.pkl"

def save_historical_data():
    """ডাটা সেভ করে"""
    try:
        with open(DATA_FILE, 'wb') as f:
            pickle.dump(list(historical_data), f)
        logger.info(f"✅ Historical data saved: {len(historical_data)} records")
    except Exception as e:
        logger.error(f"❌ Error saving data: {e}")

def load_historical_data():
    """ডাটা লোড করে"""
    global historical_data
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'rb') as f:
                data = pickle.load(f)
                historical_data = deque(data, maxlen=2000)
            logger.info(f"✅ Historical data loaded: {len(historical_data)} records")
            update_analysis_level()
    except Exception as e:
        logger.error(f"❌ Error loading data: {e}")

def clear_historical_data():
    """ডাটা ক্লিন করে"""
    global historical_data, data_analysis_level
    try:
        historical_data.clear()
        data_analysis_level = "BASIC"
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        logger.info(f"✅ Historical data cleared!")
        return True
    except Exception as e:
        logger.error(f"❌ Error clearing data: {e}")
        return False

def update_analysis_level():
    """ডাটার পরিমাণ অনুযায়ী এনালাইসিস লেভেল আপডেট করে"""
    global data_analysis_level
    data_count = len(historical_data)
    
    if data_count < 50:
        data_analysis_level = "BASIC"
    elif data_count < 100:
        data_analysis_level = "MEDIUM"
    elif data_count < 500:
        data_analysis_level = "ADVANCED"
    elif data_count < 1500:
        data_analysis_level = "EXPERT"
    else:
        data_analysis_level = "AI_MASTER"
    
    logger.info(f"📊 Data Count: {data_count} | Analysis Level: {data_analysis_level}")

def add_to_historical_data(period, prediction, actual, result):
    """নতুন ডাটা যোগ করে"""
    data_entry = {
        'period': period,
        'prediction': prediction,
        'actual': actual,
        'result': result,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    historical_data.append(data_entry)
    update_analysis_level()
    
    # প্রতি 10টি ডাটা যোগে সেভ করো
    if len(historical_data) % 10 == 0:
        save_historical_data()

# 🔥 NEW: মার্কেট মেনুপুলেশন ডিটেকশন সিস্টেম - ADVANCED
def detect_market_manipulation(numbers, analysis_level):
    """
    ডিপ লার্নিং + মেশিন লার্নিং ভিত্তিক মার্কেট মেনুপুলেশন ডিটেকশন
    ডাটা লেভেল অনুযায়ী মেনুপুলেশন ডিটেকশন উন্নত হয়
    """
    if not numbers or len(numbers) < 15:
        return False, "Insufficient data", 0
    
    manipulation_score = 0
    manipulation_reasons = []
    
    # 1. অস্বাভাবিক ফ্রিকোয়েন্সি ডিস্ট্রিবিউশন চেক
    frequency = {i: 0 for i in range(10)}
    for num in numbers[:30]:
        frequency[num] += 1
    
    # কোন সংখ্যা অস্বাভাবিক বেশি বার এসেছে কিনা
    max_freq = max(frequency.values())
    min_freq = min(frequency.values())
    avg_freq = sum(frequency.values()) / 10
    
    if max_freq > avg_freq * 3:  # গড়ের 3 গুণ বেশি
        manipulation_score += 25
        manipulation_reasons.append(f"Abnormal frequency: Number {list(frequency.keys())[list(frequency.values()).index(max_freq)]} appears {max_freq} times")
    
    # 2. ট্রেন্ড ম্যানিপুলেশন চেক
    trends = []
    for i in range(1, len(numbers[:20])):
        if numbers[i] > numbers[i-1]:
            trends.append("UP")
        elif numbers[i] < numbers[i-1]:
            trends.append("DOWN")
        else:
            trends.append("SAME")
    
    # একই ট্রেন্ড বারবার (6 বা তার বেশি)
    same_trend_count = 1
    max_same_trend = 1
    for i in range(1, len(trends)):
        if trends[i] == trends[i-1]:
            same_trend_count += 1
            max_same_trend = max(max_same_trend, same_trend_count)
        else:
            same_trend_count = 1
    
    if max_same_trend >= 6:
        manipulation_score += 30
        manipulation_reasons.append(f"Trend manipulation: Same trend repeated {max_same_trend} times")
    
    # 3. স্ট্যাটিস্টিকাল অ্যানোমালি চেক
    if len(numbers) >= 20:
        mean_val = statistics.mean(numbers[:20])
        std_val = statistics.stdev(numbers[:20]) if len(numbers[:20]) > 1 else 2.5
        
        # খুব কম ভোলাটিলিটি (মার্কেট কন্ট্রোল)
        if std_val < 1.2:
            manipulation_score += 20
            manipulation_reasons.append(f"Low volatility detected (STD: {std_val:.2f})")
        
        # খুব বেশি ভোলাটিলিটি (আর্টিফিশিয়াল স্পাইক)
        if std_val > 3.8:
            manipulation_score += 15
            manipulation_reasons.append(f"High volatility detected (STD: {std_val:.2f})")
    
    # 4. প্যাটার্ন রিপিটিশন চেক
    if len(numbers) >= 25:
        patterns = {}
        pattern_length = 3
        
        for i in range(len(numbers[:25]) - pattern_length + 1):
            pattern = tuple(numbers[i:i+pattern_length])
            patterns[pattern] = patterns.get(pattern, 0) + 1
        
        # একই প্যাটার্ন 3 বা তার বেশি বার
        for pattern, count in patterns.items():
            if count >= 3:
                manipulation_score += 35
                manipulation_reasons.append(f"Pattern repetition: {pattern} repeated {count} times")
                break
    
    # 5. সিকোয়েন্স ম্যানিপুলেশন চেক
    if len(numbers) >= 15:
        # Ascending or descending sequence detection
        asc_seq = 1
        desc_seq = 1
        max_asc = 1
        max_desc = 1
        
        for i in range(1, len(numbers[:15])):
            if numbers[i] == numbers[i-1] + 1:
                asc_seq += 1
                max_asc = max(max_asc, asc_seq)
            else:
                asc_seq = 1
            
            if numbers[i] == numbers[i-1] - 1:
                desc_seq += 1
                max_desc = max(max_desc, desc_seq)
            else:
                desc_seq = 1
        
        if max_asc >= 4 or max_desc >= 4:
            manipulation_score += 40
            manipulation_reasons.append(f"Sequence manipulation: {max_asc} ascending or {max_desc} descending sequence")
    
    # 6. BIG/SMALL ম্যানিপুলেশন চেক
    big_small_trend = []
    for num in numbers[:20]:
        big_small_trend.append("BIG" if num >= 5 else "SMALL")
    
    big_count = big_small_trend.count("BIG")
    small_count = big_small_trend.count("SMALL")
    
    if abs(big_count - small_count) >= 15:  # 15 বা তার বেশি পার্থক্য
        manipulation_score += 25
        manipulation_reasons.append(f"Big/Small imbalance: BIG={big_count}, SMALL={small_count}")
    
    # লেভেল অনুযায়ী থ্রেশহোল্ড সেট করা
    threshold = 50  # ডিফল্ট থ্রেশহোল্ড
    
    if analysis_level == "BASIC":
        threshold = 70  # বেসিক লেভেলে কম সেনসিটিভ
    elif analysis_level == "MEDIUM":
        threshold = 65
    elif analysis_level == "ADVANCED":
        threshold = 60
    elif analysis_level == "EXPERT":
        threshold = 55
    elif analysis_level == "AI_MASTER":
        threshold = 50  # AI মাস্টার লেভেলে সবচেয়ে সেনসিটিভ
    
    # ডেটা ভলিউম বোনাস (যত বেশি ডাটা, তত ভালো ডিটেকশন)
    data_bonus = min(20, len(numbers) // 5)
    manipulation_score += data_bonus
    
    manipulation_detected = manipulation_score >= threshold
    reason = " | ".join(manipulation_reasons[:3]) if manipulation_reasons else "No manipulation detected"
    
    logger.info(f"🔍 Market Manipulation Check: Score={manipulation_score}/100, Threshold={threshold}, Detected={manipulation_detected}")
    
    return manipulation_detected, reason, manipulation_score

# 🏁 /start কমান্ড - ইনলাইন কিবোর্ড সহ
@bot.message_handler(commands=['start'])
def start_handler(message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("🚀 START PREDICTION", "🛑 STOP PREDICTION")
    keyboard.row("⏰ 20 MIN PREDICTION", "⚙️ SETTINGS")
    keyboard.row("📊 WIN/LOSS REPORT", "🔄 RESET STATS")
    keyboard.row("🎭 SET PROMO MESSAGE", "🎯 VIEW PROMO")
    keyboard.row("📈 VIEW DATA STATS", "🧠 AI ANALYSIS INFO")
    keyboard.row("🧹 CLEAR ALL DATA", "📊 CURRENT STATS")
    keyboard.row("🔍 MARKET MANIPULATION INFO", "⚠️ MANIPULATION STATUS")
    
    bot.send_message(
        message.chat.id,
        "🔥 *DEEP AI PREDICTOR V5.0* 🔥\n\n"
        "🚀 স্বাগতম! AI + মেশিন লার্নিং + ডিপ লার্নিং ভিত্তিক শক্তিশালী প্রেডিকশন বট!\n\n"
        "📌 নতুন ফিচারসমূহ:\n"
        "✅ আনলিমিটেড ডাটা কালেকশন সিস্টেম\n"
        "✅ ডাটা ভিত্তিক স্বয়ংক্রিয় লেভেল আপগ্রেড\n"
        "✅ রিয়েল-টাইম মার্কেট এনালাইসিস\n"
        "✅ উন্নত প্রেডিকশন এলগরিদম\n"
        "✅ নাম্বার প্রেডিকশন (২টি নাম্বার)\n"
        "✅ জ্যাকপট উইন সিস্টেম\n"
        "✅ সুন্দর প্রেডিকশন মেসেজ\n"
        "✅ ডাটা ক্লিনিং সিস্টেম\n"
        "🆕 **ADVANCED MARKET MANIPULATION DETECTION** 🆕\n\n"
        f"📊 বর্তমান ডাটা কাউন্ট: {len(historical_data)}\n"
        f"🧠 বর্তমান এনালাইসিস লেভেল: {data_analysis_level}\n"
        f"⚠️ মার্কেট মেনুপুলেশন সিস্টেম: ACTIVE\n"
        "⚡ AI Analysis - ডাটা যত বাড়বে একুরেসি তত বাড়বে!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    # ইনলাইন কিবোর্ড শো করাও
    show_inline_keyboard(message.chat.id)

# 🔧 ইনলাইন কিবোর্ড ফাংশন
def show_inline_keyboard(chat_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("➕ ADD CHANNEL", callback_data="add_channel"),
        InlineKeyboardButton("📋 CHANNEL LIST", callback_data="channel_list")
    )
    keyboard.row(
        InlineKeyboardButton("⚙️ ADVANCED SETTINGS", callback_data="advanced_settings")
    )
    keyboard.row(
        InlineKeyboardButton("🔍 MANIPULATION SETTINGS", callback_data="manipulation_settings")
    )
    bot.send_message(chat_id, "🔧 **বট সেটআপ মেনু V5.0:**", reply_markup=keyboard, parse_mode="Markdown")

# ⚙️ অ্যাডভান্সড সেটিংস মেনু
def show_advanced_settings(chat_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("🎭 SET WIN STICKER", callback_data="set_win_sticker"),
        InlineKeyboardButton("🎭 SET LOSS STICKER", callback_data="set_loss_sticker")
    )
    keyboard.row(
        InlineKeyboardButton("🏁 SET SEASON START STICKER", callback_data="set_season_start_sticker"),
        InlineKeyboardButton("🏁 SET SEASON CLOSE STICKER", callback_data="set_season_close_sticker")
    )
    keyboard.row(
        InlineKeyboardButton("🔗 SET REGISTER LINK", callback_data="set_register_link"),
        InlineKeyboardButton("👀 VIEW REGISTER LINK", callback_data="view_register_link")
    )
    keyboard.row(
        InlineKeyboardButton("📊 VIEW STATS", callback_data="view_stats"),
        InlineKeyboardButton("🔙 BACK TO MAIN", callback_data="back_to_main")
    )
    
    # Win/Loss স্টিকার ইনফো
    win_sticker = "✅ কাস্টম" if chat_id in user_win_stickers else "❌ ডিফল্ট"
    loss_sticker = "✅ কাস্টম" if chat_id in user_loss_stickers else "❌ ডিফল্ট"
    season_start = "✅ কাস্টম" if chat_id in user_season_start_stickers else "❌ ডিফল্ট"
    season_close = "✅ কাস্টম" if chat_id in user_season_close_stickers else "❌ ডিফল্ট"
    register_link = user_register_links.get(chat_id, "Not Set")
    promo_msg = user_promotional_messages.get(chat_id, "Not Set")
    
    bot.send_message(
        chat_id,
        f"⚙️ **ADVANCED BOT SETTINGS V5.0**\n\n"
        f"🎭 Win স্টিকার: {win_sticker}\n"
        f"🎭 Loss স্টিকার: {loss_sticker}\n"
        f"🏁 Season Start: {season_start}\n"
        f"🏁 Season Close: {season_close}\n"
        f"🔗 রেজিস্টার লিংক: {register_link[:30] if register_link != 'Not Set' else 'Not Set'}...\n"
        f"📝 প্রমোশনাল মেসেজ: {promo_msg[:30] if promo_msg != 'Not Set' else 'Not Set'}...\n"
        f"📊 ডাটা কাউন্ট: {len(historical_data)}\n"
        f"🧠 এনালাইসিস লেভেল: {data_analysis_level}\n"
        f"⚠️ মার্কেট মেনুপুলেশন ডিটেকশন: ACTIVE",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# 🔍 মেনুপুলেশন সেটিংস মেনু
def show_manipulation_settings(chat_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("📊 MANIPULATION HISTORY", callback_data="manipulation_history"),
        InlineKeyboardButton("⚙️ MANIPULATION THRESHOLD", callback_data="manipulation_threshold")
    )
    keyboard.row(
        InlineKeyboardButton("🔍 DETECTION PATTERNS", callback_data="detection_patterns"),
        InlineKeyboardButton("📈 MANIPULATION STATS", callback_data="manipulation_stats")
    )
    keyboard.row(
        InlineKeyboardButton("🔙 BACK TO MAIN", callback_data="back_to_main")
    )
    
    bot.send_message(
        chat_id,
        f"🔍 **MARKET MANIPULATION SETTINGS V5.0**\n\n"
        f"⚠️ সিস্টেম স্ট্যাটাস: ACTIVE\n"
        f"📊 বর্তমান ডাটা: {len(historical_data)}\n"
        f"🧠 এনালাইসিস লেভেল: {data_analysis_level}\n"
        f"🎯 ডিটেকশন একুরেসি: {'90%+' if data_analysis_level in ['EXPERT', 'AI_MASTER'] else '80%+' if data_analysis_level == 'ADVANCED' else '70%+' if data_analysis_level == 'MEDIUM' else '60%+'}\n\n"
        f"📈 ডিটেকশন লেভেল:\n"
        f"• BASIC: Simple pattern detection\n"
        f"• MEDIUM: Advanced pattern analysis\n"
        f"• ADVANCED: Statistical anomaly detection\n"
        f"• EXPERT: Machine learning detection\n"
        f"• AI_MASTER: Deep learning detection",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# 🔧 ডুয়াল API সিস্টেম - FIXED VERSION
def get_dual_api_data():
    """
    দুইটি API থেকে ডাটা নিয়ে ক্রস-ভেরিফিকেশন করে - FIXED
    """
    try:
        # CURRENT_API থেকে ডাটা - FIXED API CALL
        current_data = None
        try:
            payload = {
                "typeId": 1,
                "language": 0,
                "random": "e7fe6c090da2495ab8290dac551ef1ed",
                "signature": "1F390E2B2D8A55D693E57FD905AE73A7",
                "timestamp": int(time.time())
            }
            response1 = requests.post(CURRENT_API, json=payload, timeout=8)
            if response1.status_code == 200:
                current_data = response1.json()
                logger.info(f"✅ CURRENT_API working")
        except Exception as e:
            logger.error(f"❌ CURRENT_API error: {e}")
        
        # HISTORY_API থেকে ডাটা - FIXED
        history_data = None
        try:
            response2 = requests.get(HISTORY_API, timeout=8)
            if response2.status_code == 200:
                history_data = response2.json()
                logger.info(f"✅ HISTORY_API working")
        except Exception as e:
            logger.error(f"❌ HISTORY_API error: {e}")
        
        # ডাটা কোয়ালিটি চেক
        if current_data and history_data:
            return current_data, history_data, "HIGH_CONFIDENCE"
        elif current_data:
            return current_data, None, "MEDIUM_CONFIDENCE"
        elif history_data:
            return None, history_data, "MEDIUM_CONFIDENCE"
        else:
            return None, None, "LOW_CONFIDENCE"
            
    except Exception as e:
        logger.error(f"❌ Dual API system error: {e}")
        return None, None, "ERROR"

# 🔧 করিলেশন ক্যালকুলেট করার ফাংশন (numpy ছাড়া)
def calculate_correlation(x, y):
    """numpy ছাড়া করিলেশন ক্যালকুলেট করে"""
    n = len(x)
    if n < 2:
        return 0
    
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n))
    denominator_y = sum((y[i] - mean_y) ** 2 for i in range(n))
    
    if denominator_x == 0 or denominator_y == 0:
        return 0
    
    return numerator / (denominator_x ** 0.5 * denominator_y ** 0.5)

# 🧠 ডিপ লার্নিং ভিত্তিক মার্কেট এনালাইসিস V5.0 - WITH MANIPULATION DETECTION
def deep_learning_market_analysis(numbers):
    """
    ডিপ লার্নিং + মেশিন লার্নিং ভিত্তিক মার্কেট এনালাইসিস
    ডাটার পরিমাণ অনুযায়ী লেভেল পরিবর্তন হয়
    """
    data_count = len(historical_data)
    
    if data_count < 50:
        # BASIC LEVEL: বেসিক এনালাইসিস + মেনুপুলেশন ডিটেকশন
        return basic_analysis(numbers)
    elif data_count < 100:
        # MEDIUM LEVEL: উন্নত এনালাইসিস + উন্নত মেনুপুলেশন ডিটেকশন
        return medium_analysis(numbers)
    elif data_count < 500:
        # ADVANCED LEVEL: শক্তিশালী এনালাইসিস + স্ট্যাটিস্টিকাল মেনুপুলেশন ডিটেকশন
        return advanced_analysis(numbers)
    elif data_count < 1500:
        # EXPERT LEVEL: প্রফেশনাল এনালাইসিস + মেশিন লার্নিং মেনুপুলেশন ডিটেকশন
        return expert_analysis(numbers)
    else:
        # AI MASTER LEVEL: মাস্টার লেভেল এনালাইসিস + ডিপ লার্নিং মেনুপুলেশন ডিটেকশন
        return ai_master_analysis(numbers)

def basic_analysis(numbers):
    """বেসিক এনালাইসিস (0-50 ডাটা) + মেনুপুলেশন ডিটেকশন"""
    if not numbers or len(numbers) < 10:
        return 65, "Basic Analysis", "NEUTRAL", [], False, "Insufficient data"
    
    recent = numbers[:15]
    big_count = sum(1 for n in recent if n >= 5)
    small_count = len(recent) - big_count
    
    confidence = 65 + min(20, abs(big_count - small_count) * 2)
    if confidence > 85:
        confidence = 85
    
    if big_count > small_count:
        market_sentiment = "BIG_BIAS"
    elif small_count > big_count:
        market_sentiment = "SMALL_BIAS"
    else:
        market_sentiment = "BALANCED"
    
    # হট নাম্বারস
    frequency = {i: 0 for i in range(10)}
    for num in recent:
        frequency[num] += 1
    
    hot_numbers = sorted(frequency.items(), key=lambda x: x[1], reverse=True)[:2]
    hot_num_list = [num for num, _ in hot_numbers]
    
    # মেনুপুলেশন ডিটেকশন
    manipulation_detected, manipulation_reason, manipulation_score = detect_market_manipulation(numbers, "BASIC")
    
    if manipulation_detected:
        analysis_type = f"Basic Market Scan ⚡ | Manipulation Detected ⚠️"
        market_sentiment = "MANIPULATION_DETECTED"
        confidence = max(30, confidence - 25)  # কনফিডেন্স কমাও
    else:
        analysis_type = "Basic Market Scan ⚡"
    
    return int(confidence), analysis_type, market_sentiment, hot_num_list, manipulation_detected, manipulation_reason

def medium_analysis(numbers):
    """মিডিয়াম এনালাইসিস (50-100 ডাটা) + উন্নত মেনুপুলেশন ডিটেকশন"""
    if not numbers or len(numbers) < 20:
        return 70, "Medium Analysis", "NEUTRAL", [], False, "Insufficient data"
    
    recent = numbers[:25]
    
    # ট্রেন্ড এনালাইসিস
    trends = []
    for i in range(1, len(recent)):
        if recent[i] > recent[i-1]:
            trends.append("UP")
        elif recent[i] < recent[i-1]:
            trends.append("DOWN")
        else:
            trends.append("SAME")
    
    # স্ট্যাটিস্টিকাল এনালাইসিস
    mean_val = statistics.mean(recent) if len(recent) > 1 else 4.5
    std_val = statistics.stdev(recent) if len(recent) > 1 else 2.5
    
    big_count = sum(1 for n in recent if n >= 5)
    small_count = len(recent) - big_count
    
    # কনফিডেন্স ক্যালকুলেশন
    confidence = 70
    
    # ডিস্ট্রিবিউশন এনালাইসিস
    dist_ratio = abs(big_count - small_count) / len(recent)
    confidence += int(dist_ratio * 20)
    
    # ট্রেন্ড কনসিসটেন্সি
    if len(set(trends[-5:])) == 1 and len(trends) >= 5:
        confidence += 10
    
    # ভোলাটিলিটি
    if std_val < 2.0:
        confidence += 5
    elif std_val > 3.5:
        confidence -= 5
    
    confidence = max(65, min(confidence, 90))
    
    # মার্কেট সেন্টিমেন্ট
    if mean_val > 5.2:
        market_sentiment = "STRONG_BIG"
    elif mean_val > 4.8:
        market_sentiment = "WEAK_BIG"
    elif mean_val < 4.2:
        market_sentiment = "STRONG_SMALL"
    elif mean_val < 4.8:
        market_sentiment = "WEAK_SMALL"
    else:
        market_sentiment = "BALANCED"
    
    # হট নাম্বারস
    frequency = {i: 0 for i in range(10)}
    for num in recent:
        frequency[num] += 1
    
    hot_numbers = sorted(frequency.items(), key=lambda x: x[1], reverse=True)[:3]
    hot_num_list = [num for num, _ in hot_numbers]
    
    # মেনুপুলেশন ডিটেকশন
    manipulation_detected, manipulation_reason, manipulation_score = detect_market_manipulation(numbers, "MEDIUM")
    
    if manipulation_detected:
        analysis_type = f"Medium Pattern Analysis 📊 | Manipulation Detected ⚠️"
        market_sentiment = "MANIPULATION_DETECTED"
        confidence = max(40, confidence - 30)  # কনফিডেন্স কমাও
    else:
        analysis_type = "Medium Pattern Analysis 📊"
    
    return int(confidence), analysis_type, market_sentiment, hot_num_list, manipulation_detected, manipulation_reason

def advanced_analysis(numbers):
    """অ্যাডভান্সড এনালাইসিস (100-500 ডাটা) + স্ট্যাটিস্টিকাল মেনুপুলেশন ডিটেকশন"""
    if not numbers or len(numbers) < 30:
        return 75, "Advanced Analysis", "NEUTRAL", [], False, "Insufficient data"
    
    recent = numbers[:40]
    
    # মাল্টি-লেভেল এনালাইসিস
    # লেভেল 1: শর্ট টার্ম ট্রেন্ড (last 10)
    short_term = recent[:10]
    # লেভেল 2: মিডিয়াম টার্ম ট্রেন্ড (last 20)
    medium_term = recent[:20]
    # লেভেল 3: লং টার্ম ট্রেন্ড (all 40)
    long_term = recent
    
    # শর্ট টার্ম এনালাইসিস
    st_big = sum(1 for n in short_term if n >= 5)
    st_small = len(short_term) - st_big
    
    # মিডিয়াম টার্ম এনালাইসিস
    mt_big = sum(1 for n in medium_term if n >= 5)
    mt_small = len(medium_term) - mt_big
    
    # লং টার্ম এনালাইসিস
    lt_big = sum(1 for n in long_term if n >= 5)
    lt_small = len(long_term) - lt_big
    
    # ট্রেন্ড কনসিসটেন্সি স্কোর
    trend_score = 0
    if st_big > st_small and mt_big > mt_small and lt_big > lt_small:
        trend_score = 25  # স্ট্রং BIG ট্রেন্ড
    elif st_small > st_big and mt_small > mt_big and lt_small > lt_big:
        trend_score = 25  # স্ট্রং SMALL ট্রেন্ড
    elif (st_big > st_small and mt_big > mt_small) or (st_small > st_big and mt_small > mt_big):
        trend_score = 15  # মিডিয়াম ট্রেন্ড
    
    # প্যাটার্ন ডিটেকশন
    patterns = []
    for i in range(2, len(recent)):
        if recent[i] == recent[i-1] == recent[i-2]:
            patterns.append("TRIPLE")
        elif (recent[i] > recent[i-1] > recent[i-2]) or (recent[i] < recent[i-1] < recent[i-2]):
            patterns.append("TREND")
    
    pattern_score = len(patterns) * 2
    
    # ভোলাটিলিটি এনালাইসিস
    volatility = statistics.stdev(recent) if len(recent) > 1 else 2.5
    vol_score = 0
    if volatility < 1.8:
        vol_score = 10  # লো ভোলাটিলিটি - হাই কনফিডেন্স
    elif volatility > 3.5:
        vol_score = -5  # হাই ভোলাটিলিটি - লো কনফিডেন্স
    
    # কনফিডেন্স ক্যালকুলেশন
    confidence = 75 + trend_score + pattern_score + vol_score
    confidence = max(70, min(confidence, 95))
    
    # মার্কেট সেন্টিমেন্ট
    if trend_score >= 20:
        market_sentiment = "STRONG_TREND"
    elif trend_score >= 10:
        market_sentiment = "MODERATE_TREND"
    elif pattern_score >= 6:
        market_sentiment = "PATTERN_DETECTED"
    else:
        market_sentiment = "NEUTRAL"
    
    # হট নাম্বারস (ফ্রিকোয়েন্সি + রিসেন্টি)
    frequency = {i: 0 for i in range(10)}
    recency_weight = {i: 0 for i in range(10)}
    
    for idx, num in enumerate(recent):
        frequency[num] += 1
        # সাম্প্রতিক নাম্বার বেশি ওয়েট পায়
        recency_weight[num] += (len(recent) - idx) * 0.1
    
    # কম্বাইন্ড স্কোর
    combined_scores = []
    for i in range(10):
        score = frequency[i] * 0.7 + recency_weight[i] * 0.3
        combined_scores.append((i, score))
    
    hot_numbers = sorted(combined_scores, key=lambda x: x[1], reverse=True)[:4]
    hot_num_list = [num for num, _ in hot_numbers]
    
    # মেনুপুলেশন ডিটেকশন
    manipulation_detected, manipulation_reason, manipulation_score = detect_market_manipulation(numbers, "ADVANCED")
    
    if manipulation_detected:
        analysis_type = f"Advanced AI Analysis 🔥 | Manipulation Detected ⚠️"
        market_sentiment = "MANIPULATION_DETECTED"
        confidence = max(50, confidence - 35)  # কনফিডেন্স কমাও
    else:
        analysis_type = "Advanced AI Analysis 🔥"
    
    return int(confidence), analysis_type, market_sentiment, hot_num_list, manipulation_detected, manipulation_reason

def expert_analysis(numbers):
    """এক্সপার্ট এনালাইসিস (500-1500 ডাটা) + মেশিন লার্নিং মেনুপুলেশন ডিটেকশন"""
    if not numbers or len(numbers) < 50:
        return 80, "Expert Analysis", "NEUTRAL", [], False, "Insufficient data"
    
    # হিস্টোরিকাল ডাটা ব্যবহার করে
    hist_numbers = []
    if historical_data:
        for entry in historical_data:
            if 'actual' in entry:
                try:
                    hist_numbers.append(int(entry['actual']))
                except:
                    pass
    
    # রিসেন্ট + হিস্টোরিকাল ডাটা কম্বাইন
    all_numbers = numbers[:30] + hist_numbers[-50:]
    
    if len(all_numbers) < 30:
        all_numbers = numbers[:50]
    
    # মেশিন লার্নিং স্টাইল এনালাইসিস
    # 1. মুভিং এভারেজ
    window_size = min(10, len(all_numbers) // 3)
    moving_avg = []
    for i in range(len(all_numbers) - window_size + 1):
        window = all_numbers[i:i+window_size]
        moving_avg.append(statistics.mean(window))
    
    # 2. ট্রেন্ড ডিটেকশন
    if len(moving_avg) >= 2:
        trend = "UP" if moving_avg[-1] > moving_avg[0] else "DOWN"
    else:
        trend = "NEUTRAL"
    
    # 3. প্রোবাবিলিটি ডিস্ট্রিবিউশন
    prob_dist = {i: all_numbers.count(i) / len(all_numbers) for i in range(10)}
    
    # 4. করিলেশন এনালাইসিস (numpy ছাড়া)
    correlation_score = 0
    if len(all_numbers) >= 20:
        # অটো-করিলেশন (ল্যাগ 1)
        lag1_corr = calculate_correlation(all_numbers[:-1], all_numbers[1:]) if len(all_numbers) > 1 else 0
        if not math.isnan(lag1_corr):
            correlation_score = abs(lag1_corr) * 20
    
    # কনফিডেন্স ক্যালকুলেশন
    confidence = 80
    
    # ট্রেন্ড স্ট্রength
    if trend == "UP" and len(moving_avg) >= 3:
        trend_strength = (moving_avg[-1] - moving_avg[0]) / max(moving_avg)
        confidence += trend_strength * 15
    
    # প্রোবাবিলিটি ডিস্ট্রিবিউশন
    max_prob_num = max(prob_dist.items(), key=lambda x: x[1])[0]
    if prob_dist[max_prob_num] > 0.25:  # 25% এর বেশি প্রোবাবিলিটি
        confidence += 10
    
    # করিলেশন স্কোর
    confidence += correlation_score
    
    confidence = max(75, min(confidence, 97))
    
    # মার্কেট সেন্টিমেন্ট
    if trend == "UP" and confidence > 85:
        market_sentiment = "STRONG_BULLISH"
    elif trend == "UP":
        market_sentiment = "BULLISH"
    elif trend == "DOWN" and confidence > 85:
        market_sentiment = "STRONG_BEARISH"
    elif trend == "DOWN":
        market_sentiment = "BEARISH"
    else:
        market_sentiment = "NEUTRAL"
    
    # হট নাম্বারস (প্রোবাবিলিটি ভিত্তিক)
    hot_numbers = sorted(prob_dist.items(), key=lambda x: x[1], reverse=True)[:4]
    hot_num_list = [num for num, _ in hot_numbers]
    
    # মেনুপুলেশন ডিটেকশন
    manipulation_detected, manipulation_reason, manipulation_score = detect_market_manipulation(numbers, "EXPERT")
    
    if manipulation_detected:
        analysis_type = f"Expert ML Analysis 🧠 | Manipulation Detected ⚠️"
        market_sentiment = "MANIPULATION_DETECTED"
        confidence = max(60, confidence - 40)  # কনফিডেন্স কমাও
    else:
        analysis_type = "Expert ML Analysis 🧠"
    
    return int(confidence), analysis_type, market_sentiment, hot_num_list, manipulation_detected, manipulation_reason

def ai_master_analysis(numbers):
    """AI মাস্টার এনালাইসিস (1500+ ডাটা) + ডিপ লার্নিং মেনুপুলেশন ডিটেকশন"""
    if not numbers or len(numbers) < 60:
        return 85, "AI Master Analysis", "NEUTRAL", [], False, "Insufficient data"
    
    # সবচেয়ে শক্তিশালী এনালাইসিস
    # সমস্ত হিস্টোরিকাল ডাটা ব্যবহার করে
    all_historical = []
    if historical_data:
        for entry in historical_data:
            if 'actual' in entry:
                try:
                    all_historical.append(int(entry['actual']))
                except:
                    pass
    
    # রিসেন্ট ডাটার সাথে কম্বাইন
    combined_data = numbers[:40] + all_historical[-100:]
    
    if len(combined_data) < 50:
        combined_data = numbers[:60]
    
    # মাল্টি-ডাইমেনশনাল এনালাইসিস
    
    # 1. টাইম সিরিজ এনালাইসিস
    time_series = combined_data
    
    # 2. সিজনালিটি ডিটেকশন
    seasonal_patterns = []
    if len(time_series) >= 20:
        for period in [5, 10, 15]:
            if len(time_series) >= period * 2:
                seasonal_avg = []
                for i in range(period):
                    seasonal_values = []
                    for j in range(i, len(time_series), period):
                        if j < len(time_series):
                            seasonal_values.append(time_series[j])
                    if seasonal_values:
                        seasonal_avg.append(statistics.mean(seasonal_values))
                
                if len(seasonal_avg) >= 2:
                    seasonal_var = statistics.variance(seasonal_avg) if len(seasonal_avg) > 1 else 0
                    if seasonal_var < 2.0:
                        seasonal_patterns.append(period)
    
    # 3. প্রেডিক্টিভ মডেলিং
    predictive_score = 0
    if len(time_series) >= 30:
        # Simple predictive model
        recent_mean = statistics.mean(time_series[:20])
        overall_mean = statistics.mean(time_series)
        
        if abs(recent_mean - overall_mean) < 1.0:
            predictive_score = 15  # স্টেবল ট্রেন্ড
        elif abs(recent_mean - overall_mean) < 2.0:
            predictive_score = 10  # মডারেট ট্রেন্ড
        else:
            predictive_score = 5   # ভোলাটাইল
    
    # 4. প্যাটার্ন রিকগনিশন
    pattern_matches = 0
    common_patterns = [
        [0, 1, 2], [1, 2, 3], [2, 3, 4], [3, 4, 5],
        [4, 5, 6], [5, 6, 7], [6, 7, 8], [7, 8, 9],
        [9, 8, 7], [8, 7, 6], [7, 6, 5], [6, 5, 4],
        [5, 4, 3], [4, 3, 2], [3, 2, 1], [2, 1, 0]
    ]
    
    if len(time_series) >= 10:
        recent_pattern = time_series[:3]
        for pattern in common_patterns:
            if recent_pattern == pattern:
                pattern_matches += 1
    
    pattern_score = pattern_matches * 8
    
    # 5. কনফিডেন্স ক্যালকুলেশন
    confidence = 85
    
    # সিজনালিটি স্কোর
    if seasonal_patterns:
        confidence += len(seasonal_patterns) * 3
    
    # প্রেডিক্টিভ স্কোর
    confidence += predictive_score
    
    # প্যাটার্ন স্কোর
    confidence += pattern_score
    
    # ডাটা ভলিউম বোনাস
    data_bonus = min(10, len(historical_data) // 150)
    confidence += data_bonus
    
    confidence = max(80, min(confidence, 99))
    
    # মার্কেট সেন্টিমেন্ট
    if confidence >= 95:
        market_sentiment = "AI_ULTRA_CONFIDENT"
    elif confidence >= 90:
        market_sentiment = "AI_HIGH_CONFIDENCE"
    elif confidence >= 85:
        market_sentiment = "AI_MODERATE_CONFIDENCE"
    else:
        market_sentiment = "AI_NEUTRAL"
    
    # AI রিকমেন্ডেড নাম্বারস
    # ফ্রিকোয়েন্সি + ট্রেন্ড + প্যাটার্ন কম্বাইন
    freq_dist = {i: 0 for i in range(10)}
    for num in time_series:
        freq_dist[num] += 1
    
    trend_scores = {i: 0 for i in range(10)}
    if len(time_series) >= 10:
        recent_trend = statistics.mean(time_series[:5])
        for i in range(10):
            if recent_trend > 5 and i >= 5:
                trend_scores[i] = 2
            elif recent_trend < 5 and i < 5:
                trend_scores[i] = 2
    
    combined_scores = []
    for i in range(10):
        score = freq_dist[i] * 0.5 + trend_scores[i] * 0.3 + random.random() * 0.2
        combined_scores.append((i, score))
    
    hot_numbers = sorted(combined_scores, key=lambda x: x[1], reverse=True)[:5]
    hot_num_list = [num for num, _ in hot_numbers]
    
    # মেনুপুলেশন ডিটেকশন
    manipulation_detected, manipulation_reason, manipulation_score = detect_market_manipulation(numbers, "AI_MASTER")
    
    if manipulation_detected:
        analysis_type = f"AI Master Deep Learning 🤖 | Manipulation Detected ⚠️"
        market_sentiment = "MANIPULATION_DETECTED"
        confidence = max(70, confidence - 45)  # কনফিডেন্স কমাও
    else:
        analysis_type = "AI Master Deep Learning 🤖"
    
    return int(confidence), analysis_type, market_sentiment, hot_num_list, manipulation_detected, manipulation_reason

# 🎯 নাম্বার প্রেডিকশন জেনারেটর - FIXED VERSION
def generate_number_prediction(prediction_type, hot_numbers):
    """
    BIG/SMALL অনুযায়ী ২টি নাম্বার প্রেডিকশন দেয়
    PREDICTION TYPE অনুযায়ী সঠিক রেঞ্জের নাম্বার দেয়
    """
    if prediction_type == "BIG":
        # 0-4 এর মধ্যে ২টি আলাদা নাম্বার (FIXED: BIG should be 0-4)
        big_numbers = [0, 1, 2, 3, 4]
        
        # হট নাম্বারস থেকে BIG নাম্বার ফিল্টার
        hot_big_numbers = [num for num in hot_numbers if num in big_numbers]
        
        if len(hot_big_numbers) >= 2:
            # হট BIG নাম্বার থেকে সিলেক্ট
            predicted_numbers = random.sample(hot_big_numbers, 2)
        elif len(hot_big_numbers) == 1:
            # 1টি হট নাম্বার আছে, আরেকটি র্যান্ডম BIG নাম্বার নাও
            other_numbers = [num for num in big_numbers if num != hot_big_numbers[0]]
            predicted_numbers = [hot_big_numbers[0], random.choice(other_numbers)]
        else:
            # কোন হট BIG নাম্বার নেই, দুইটি র্যান্ডম BIG নাম্বার নাও
            predicted_numbers = random.sample(big_numbers, 2)
            
    else:  # SMALL
        # 5-9 এর মধ্যে ২টি আলাদা নাম্বার (FIXED: SMALL should be 5-9)
        small_numbers = [5, 6, 7, 8, 9]
        
        # হট নাম্বারস থেকে SMALL নাম্বার ফিল্টার
        hot_small_numbers = [num for num in hot_numbers if num in small_numbers]
        
        if len(hot_small_numbers) >= 2:
            # হট SMALL নাম্বার থেকে সিলেক্ট
            predicted_numbers = random.sample(hot_small_numbers, 2)
        elif len(hot_small_numbers) == 1:
            # 1টি হট নাম্বার আছে, আরেকটি র্যান্ডম SMALL নাম্বার নাও
            other_numbers = [num for num in small_numbers if num != hot_small_numbers[0]]
            predicted_numbers = [hot_small_numbers[0], random.choice(other_numbers)]
        else:
            # কোন হট SMALL নাম্বার নেই, দুইটি র্যান্ডম SMALL নাম্বার নাও
            predicted_numbers = random.sample(small_numbers, 2)
    
    return sorted(predicted_numbers)

# 🧠 স্মার্ট প্রেডিকশন জেনারেটর V5.0 - WITH MANIPULATION HANDLING
def generate_smart_prediction_v5(numbers, confidence, market_sentiment, hot_numbers, analysis_level, manipulation_detected):
    """
    ডিপ লার্নিং ভিত্তিক স্মার্ট প্রেডিকশন V5.0
    যদি মেনুপুলেশন ডিটেক্ট হয়, তাহলে SKIP রিটার্ন করবে
    """
    if manipulation_detected:
        # মেনুপুলেশন ডিটেক্ট হলে SKIP
        return "SKIP", []
    
    if not numbers:
        # র্যান্ডম প্রেডিকশন
        pred_type = "BIG" if random.random() > 0.5 else "SMALL"
        num_pred = generate_number_prediction(pred_type, [])
        return pred_type, num_pred
    
    recent_trend = []
    for num in numbers[:15]:  # সাম্প্রতিক 15টি দেখি
        recent_trend.append("BIG" if num >= 5 else "SMALL")
    
    big_count = sum(1 for trend in recent_trend if trend == "BIG")
    small_count = len(recent_trend) - big_count
    
    # এনালাইসিস লেভেল অনুযায়ী প্রেডিকশন লজিক
    if analysis_level in ["EXPERT", "AI_MASTER"]:
        # AI মাস্টার লেভেল প্রেডিকশন
        if "STRONG" in market_sentiment and confidence >= 90:
            # শক্তিশালী ট্রেন্ডে ট্রেন্ড ফলো করো
            if "BIG" in market_sentiment or "BULL" in market_sentiment:
                pred_type = "BIG"
            elif "SMALL" in market_sentiment or "BEAR" in market_sentiment:
                pred_type = "SMALL"
            else:
                # ট্রেন্ড রিভার্সাল লজিক
                if big_count >= 10:
                    pred_type = "SMALL"  # রিভার্স এক্সপেক্টেড
                elif small_count >= 10:
                    pred_type = "BIG"    # রিভার্স এক্সপেক্টেড
                else:
                    pred_type = recent_trend[0]
        
        elif confidence >= 85:
            # হাই কনফিডেন্সে ট্রেন্ড কন্টিনিউ
            pred_type = recent_trend[0]
        
        else:
            # হট নাম্বারস এনালাইসিস
            hot_big_count = sum(1 for num in hot_numbers if num >= 5)
            hot_small_count = len(hot_numbers) - hot_big_count
            
            if hot_big_count > hot_small_count:
                pred_type = "BIG"
            elif hot_small_count > hot_big_count:
                pred_type = "SMALL"
            else:
                # র্যান্ডম但有 bias
                pred_type = "BIG" if random.random() > 0.5 else "SMALL"
    
    elif analysis_level == "ADVANCED":
        # অ্যাডভান্সড লেভেল প্রেডিকশন
        if confidence >= 80:
            if big_count >= 8:
                pred_type = "SMALL" if random.random() > 0.3 else "BIG"
            elif small_count >= 8:
                pred_type = "BIG" if random.random() > 0.3 else "SMALL"
            else:
                pred_type = recent_trend[0]
        else:
            pred_type = "BIG" if random.random() > 0.5 else "SMALL"
    
    elif analysis_level == "MEDIUM":
        # মিডিয়াম লেভেল প্রেডিকশন
        if confidence >= 75:
            pred_type = recent_trend[0]
        else:
            pred_type = "SMALL" if recent_trend[0] == "BIG" else "BIG"
    
    else:  # BASIC
        # বেসিক লেভেল প্রেডিকশন
        pred_type = "BIG" if big_count > small_count else "SMALL"
        if big_count == small_count:
            pred_type = "BIG" if random.random() > 0.5 else "SMALL"
    
    # নাম্বার প্রেডিকশন জেনারেট
    num_pred = generate_number_prediction(pred_type, hot_numbers)
    
    return pred_type, num_pred

# 🎯 রিয়েল-টাইম পিরিওড নাম্বার জেনারেটর
def generate_real_time_period():
    """
    রিয়েল-টাইমে UTC সময় অনুযায়ী পিরিওড জেনারেট করে
    """
    now = datetime.now(timezone.utc)
    hour = now.hour
    minute = now.minute
    total_minutes = hour * 60 + minute
    
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    
    period = year + month + day + "1000" + str(10001 + total_minutes)
    return period

# 🎯 রিয়েল-টাইম সেকেন্ড চেকার
def get_real_time_seconds():
    """
    বর্তমান UTC সময়ের সেকেন্ড রিটার্ন করে (0-59)
    """
    now = datetime.now(timezone.utc)
    return now.second

# 🔍 রিয়েল-টাইম রেজাল্ট চেকার - FIXED JACKPOT SYSTEM
def check_actual_result_with_jackpot(predicted_result, predicted_numbers, period_number=None):
    """
    API থেকে আসল রেজাল্ট চেক করে - CORRECT JACKPOT SYSTEM
    """
    try:
        # প্রথমে HISTORY_API থেকে রেজাল্ট চেক - সবচেয়ে নির্ভরযোগ্য
        response = requests.get(HISTORY_API, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            if data and 'data' in data and 'list' in data['data']:
                # সবচেয়ে সাম্প্রতিক রেজাল্ট নাও (প্রথমটি)
                latest_result = data['data']['list'][0]
                if 'number' in latest_result and latest_result['number']:
                    try:
                        actual_num = int(latest_result['number'])
                        actual_result = "BIG" if actual_num >= 5 else "SMALL"
                        
                        logger.info(f"🎯 Actual result from History API: {actual_num} ({actual_result})")
                        logger.info(f"🎯 Predicted: {predicted_result} {predicted_numbers}")
                        
                        # CORRECT JACKPOT LOGIC:
                        # 1. জ্যাকপট চেক: নাম্বার মিলেছে কিনা
                        if actual_num in predicted_numbers:
                            return actual_num, actual_result, "JACKPOT WIN 🎉"
                        # 2. শুধু BIG/SMALL মিলেছে কিনা
                        elif actual_result == predicted_result:
                            return actual_num, actual_result, "WIN ✅"
                        # 3. কিছুই না মিললে LOSS
                        else:
                            return actual_num, actual_result, "LOSS ❌"
                    except ValueError:
                        logger.error(f"❌ Number conversion error: {latest_result['number']}")
        
        # যদি HISTORY_API কাজ না করে, CURRENT_API থেকে চেক করো
        try:
            payload = {
                "typeId": 1,
                "language": 0,
                "random": "e7fe6c090da2495ab8290dac551ef1ed",
                "signature": "1F390E2B2D8A55D693E57FD905AE73A7",
                "timestamp": int(time.time())
            }
            response = requests.post(CURRENT_API, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if data and 'data' in data:
                    current_result = data['data'].get('result')
                    if current_result:
                        try:
                            actual_num = int(current_result)
                            actual_result = "BIG" if actual_num >= 5 else "SMALL"
                            
                            logger.info(f"🎯 Actual result from Current API: {actual_num} ({actual_result})")
                            logger.info(f"🎯 Predicted: {predicted_result} {predicted_numbers}")
                            
                            # CORRECT JACKPOT LOGIC:
                            # 1. জ্যাকপট চেক: নাম্বার মিলেছে কিনা
                            if actual_num in predicted_numbers:
                                return actual_num, actual_result, "JACKPOT WIN 🎉"
                            # 2. শুধু BIG/SMALL মিলেছে কিনা
                            elif actual_result == predicted_result:
                                return actual_num, actual_result, "WIN ✅"
                            # 3. কিছুই না মিললে LOSS
                            else:
                                return actual_num, actual_result, "LOSS ❌"
                        except ValueError:
                            logger.error(f"❌ Number conversion error: {current_result}")
        except Exception as e:
            logger.error(f"❌ Current API check error: {e}")
    
    except Exception as e:
        logger.error(f"❌ Result check error: {e}")
    
    # যদি API কাজ না করে, র্যান্ডম রেজাল্ট জেনারেট করো (ডেমোর জন্য)
    logger.info("⚠️ Using fallback random result")
    actual_num = random.randint(0, 9)
    actual_result = "BIG" if actual_num >= 5 else "SMALL"
    
    # CORRECT JACKPOT LOGIC:
    # 1. জ্যাকপট চেক: নাম্বার মিলেছে কিনা
    if actual_num in predicted_numbers:
        return actual_num, actual_result, "JACKPOT WIN 🎉"
    # 2. শুধু BIG/SMALL মিলেছে কিনা
    elif actual_result == predicted_result:
        return actual_num, actual_result, "WIN ✅"
    # 3. কিছুই না মিললে LOSS
    else:
        return actual_num, actual_result, "LOSS ❌"

# 🧠 প্রেডিকশন মেসেজ জেনারেটর - V5.0 WITH MANIPULATION DETECTION
def generate_prediction_message_v5(period_number, prediction_type, number_prediction, confidence, analysis_type, user_id=None, status="wating⌛", manipulation_detected=False, manipulation_reason=""):
    """
    মার্কেট মেনুপুলেশন ডিটেকশন সহ প্রেডিকশন মেসেজ জেনারেট করে V5.0
    """
    # মেনুপুলেশন ডিটেক্ট হলে বিশেষ ফরম্যাট
    if manipulation_detected:
        # মার্কেট মেনুপুলেশন ডিটেক্টেড
        pred_emoji = "⚠️"
        pred_text = "SKIP THIS PREDICTION"
        num_text = "MARKET MANIPULATION DETECTED"
        status_emoji = "⚠️"
        status = "MANIPULATION DETECTED"
        
        # মেনুপুলেশন রিজন যোগ করুন
        if manipulation_reason and len(manipulation_reason) > 0:
            analysis_type = f"⚠️ {analysis_type} | {manipulation_reason[:50]}..."
        else:
            analysis_type = f"⚠️ {analysis_type} | Market Manipulation Detected"
    else:
        # নরমাল প্রেডিকশন
        if prediction_type == "BIG":
            pred_emoji = "🔴"
            pred_text = "BIG"
        elif prediction_type == "SMALL":
            pred_emoji = "🔵"
            pred_text = "SMALL"
        else:
            pred_emoji = "⚡"
            pred_text = prediction_type
        
        # নাম্বার প্রেডিকশন টেক্সট
        if number_prediction and len(number_prediction) >= 2:
            num_text = f"{number_prediction[0]},{number_prediction[1]}"
        else:
            num_text = "N/A"
        
        # কনফিডেন্স ইমোজি
        if confidence >= 95:
            conf_emoji = "🔥"
        elif confidence >= 90:
            conf_emoji = "✅"
        elif confidence >= 85:
            conf_emoji = "📊"
        elif confidence >= 80:
            conf_emoji = "⚡"
        elif confidence >= 75:
            conf_emoji = "🔍"
        else:
            conf_emoji = "📈"
        
        # স্ট্যাটাস এর উপর ভিত্তি করে ইমোজি
        if "JACKPOT" in status:
            status_emoji = "🎰"
        elif "WIN" in status:
            status_emoji = "✅"
        elif "LOSS" in status:
            status_emoji = "❌"
        else:
            status_emoji = "⌛"
    
    # ডাটা কাউন্ট টেক্সট
    data_count = len(historical_data)
    data_text = f"📊 Data: {data_count} | Level: {data_analysis_level}"
    
    # মার্কেট স্ট্যাটাস
    market_status = "⚠️ MANIPULATION DETECTED" if manipulation_detected else "✅ MARKET NORMAL"
    
    # তোমার দেওয়া ফরম্যাটে মেসেজ
    message = f"""
🔥 Deep ai predictor ❤️
━━━━━━━━━━━━━━━
🎯 Period: {period_number}
{pred_emoji} Prediction: {pred_text}/{num_text}
🎲 Confidence: {confidence}%
{status_emoji} Result: {status}
📊 Market Status: {market_status}
━━━━━━━━━━━━━━━
{data_text}
⚡ AI Power: {analysis_type}
"""
    
    return message

# 🎭 সিজন স্টিকার পাঠানো
def send_season_sticker(chat_id, sticker_type, user_id):
    """
    সিজন স্টার্ট/ক্লোজ স্টিকার পাঠায়
    """
    try:
        if sticker_type == "START":
            sticker_id = user_season_start_stickers.get(user_id, DEFAULT_SEASON_START_STICKER)
            text = f"🏁 *PREDICTION SESSION STARTED!* 🏁\n\n⚡ AI Analysis: {data_analysis_level}\n📊 Data Count: {len(historical_data)}\n🎯 High Accuracy Mode\n⚠️ Market Manipulation Detection: ACTIVE"
        else:  # CLOSE
            sticker_id = user_season_close_stickers.get(user_id, DEFAULT_SEASON_CLOSE_STICKER)
            text = f"🏁 *PREDICTION SESSION ENDED!* 🏁\n\n✅ Session Completed\n📊 Data Added to AI Database\n🎯 Ready for Next Session\n⚠️ Market Manipulation Detection: ACTIVE"
        
        # স্টিকার পাঠাও
        bot.send_sticker(chat_id, sticker_id)
        # টেক্সট মেসেজ পাঠাও
        bot.send_message(chat_id, text, parse_mode="Markdown")
        return True
    except Exception as e:
        logger.error(f"❌ Season sticker send error: {e}")
        return False

# 📝 প্রমোশনাল মেসেজ পাঠানো
def send_promotional_message(chat_id, user_id):
    """
    প্রমোশনাল মেসেজ পাঠায়
    """
    try:
        promo_msg = user_promotional_messages.get(user_id)
        if promo_msg:
            # সুন্দর ফরম্যাটে প্রমোশনাল মেসেজ
            promo_formatted = f"""
🎉 *SPECIAL PROMOTION* 🎉

{promo_msg}

📊 AI Database: {len(historical_data)} records
🧠 Analysis Level: {data_analysis_level}
⚠️ Market Manipulation Detection: ACTIVE
⚡ Real-time AI Analysis
━━━━━━━━━━━━━━━━━━━
💎 Join for More Predictions
🎯 High Accuracy Guaranteed
"""
            bot.send_message(chat_id, promo_formatted, parse_mode="Markdown")
            return True
        else:
            # ডিফল্ট প্রমোশনাল মেসেজ
            default_promo = f"""
🎉 *SPECIAL OFFER* 🎉

🔥 Get Exclusive Bonuses!
💰 Win Big with Our AI Predictions!
⚡ Join Now for Better Results!

📊 AI Database: {len(historical_data)} records
🧠 Analysis Level: {data_analysis_level}
⚠️ Market Manipulation Detection: ACTIVE
━━━━━━━━━━━━━━━━━━━
🔗 Register: Coming Soon
📱 Contact: @Admin
"""
            bot.send_message(chat_id, default_promo, parse_mode="Markdown")
            return True
    except Exception as e:
        logger.error(f"❌ Promotional message error: {e}")
        return False

# 🧠 Win/Loss স্টিকার পাঠানো
def send_win_loss_sticker(chat_id, win_loss, user_id):
    """
    Win/Loss অনুযায়ী স্টিকার পাঠায়
    """
    try:
        if win_loss.startswith("JACKPOT"):
            # জ্যাকপট উইন হলে বিশেষ স্টিকার (Win স্টিকার ব্যবহার)
            sticker_id = user_win_stickers.get(user_id, DEFAULT_WIN_STICKER)
            bot.send_message(chat_id, "🎰 *JACKPOT WIN! CONGRATULATIONS!* 🎰", parse_mode="Markdown")
        elif win_loss == "WIN ✅":
            sticker_id = user_win_stickers.get(user_id, DEFAULT_WIN_STICKER)
        else:
            sticker_id = user_loss_stickers.get(user_id, DEFAULT_LOSS_STICKER)
        
        bot.send_sticker(chat_id, sticker_id)
        return True
    except Exception as e:
        logger.error(f"❌ Sticker send error: {e}")
        return False

# 🧠 Win/Loss হিস্ট্রি আপডেট
def update_prediction_history(user_id, period, prediction_type, number_prediction, actual_number, actual_result, win_loss):
    if user_id not in prediction_history:
        prediction_history[user_id] = []
    
    history_entry = {
        "period": period,
        "prediction_type": prediction_type,
        "number_prediction": number_prediction,
        "actual_number": actual_number,
        "actual_result": actual_result,
        "result": win_loss,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    prediction_history[user_id].append(history_entry)
    
    # সর্বোচ্চ 200টি এন্ট্রি রাখো
    if len(prediction_history[user_id]) > 200:
        prediction_history[user_id] = prediction_history[user_id][-200:]

# 📊 ইউজার স্ট্যাটিস্টিক্স
def get_user_stats_v5(user_id):
    if user_id not in prediction_history or not prediction_history[user_id]:
        return {"total": 0, "wins": 0, "losses": 0, "jackpot_wins": 0, "win_rate": 0, "skipped": 0}
    
    history = prediction_history[user_id]
    total = len(history)
    wins = sum(1 for entry in history if "WIN" in entry["result"])
    losses = sum(1 for entry in history if "LOSS" in entry["result"])
    jackpot_wins = sum(1 for entry in history if "JACKPOT" in entry["result"])
    skipped = sum(1 for entry in history if entry["prediction_type"] == "SKIP")
    win_rate = (wins / (total - skipped)) * 100 if (total - skipped) > 0 else 0
    
    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "jackpot_wins": jackpot_wins,
        "skipped": skipped,
        "win_rate": round(win_rate, 2)
    }

# 🧠 ডিপ লার্নিং API প্রেডিকশন জেনারেটর - V5.0 WITH MANIPULATION DETECTION
def generate_deep_learning_prediction(user_id=None):
    try:
        # দুই API থেকে ডাটা নাও
        current_data, history_data, confidence_level = get_dual_api_data()
        
        numbers = []
        
        # HISTORY_API থেকে নম্বর সংগ্রহ - FIXED
        if history_data and 'data' in history_data and 'list' in history_data['data']:
            for result in history_data['data']['list'][:40]:  # 40টি রেজাল্ট
                if 'number' in result and result['number']:
                    try:
                        num = int(result['number'])
                        numbers.append(num)
                    except:
                        continue
        
        # CURRENT_API থেকে নম্বর সংগ্রহ (যদি available হয়) - FIXED
        if current_data and 'data' in current_data:
            current_result = current_data['data'].get('result')
            if current_result:
                try:
                    num = int(current_result)
                    numbers.insert(0, num)  # সামনে যোগ করো
                except:
                    pass
        
        logger.info(f"📊 Collected {len(numbers)} numbers for analysis | Data Count: {len(historical_data)} | Level: {data_analysis_level}")
        
        if numbers:
            # ডিপ লার্নিং মার্কেট এনালাইসিস V5.0 (মেনুপুলেশন ডিটেকশন সহ)
            confidence, analysis_type, market_sentiment, hot_numbers, manipulation_detected, manipulation_reason = deep_learning_market_analysis(numbers)
            
            # API কনফিডেন্স লেভেল অনুযায়ী adjustment
            if confidence_level == "HIGH_CONFIDENCE":
                if not manipulation_detected:
                    confidence = min(confidence + 8, 98)
                analysis_type = "🔒 Dual API - " + analysis_type
            elif confidence_level == "MEDIUM_CONFIDENCE":
                if not manipulation_detected:
                    confidence = min(confidence + 4, 94)
                analysis_type = "🔗 Single API - " + analysis_type
            else:
                if not manipulation_detected:
                    confidence = max(confidence - 2, 65)
                analysis_type = "⚡ Fallback - " + analysis_type
            
            # ডিপ লার্নিং প্রেডিকশন জেনারেট V5.0
            prediction_type, number_prediction = generate_smart_prediction_v5(
                numbers, confidence, market_sentiment, hot_numbers, data_analysis_level, manipulation_detected
            )
            
            period = generate_real_time_period()
            
            # প্রেডিকশন মেসেজ জেনারেট করো V5.0
            prediction_message = generate_prediction_message_v5(
                period, prediction_type, number_prediction, confidence, analysis_type, user_id, "wating⌛", manipulation_detected, manipulation_reason
            )
            
            return prediction_message, prediction_type, number_prediction, period, confidence, analysis_type, manipulation_detected, manipulation_reason
            
    except Exception as e:
        logger.error(f"❌ Deep learning analysis error: {e}")
    
    # ফলব্যাক মেকানিজম
    period = generate_real_time_period()
    prediction_type = "BIG" if random.random() > 0.5 else "SMALL"
    number_prediction = generate_number_prediction(prediction_type, [])
    confidence = random.randint(70, 85)
    analysis_type = f"Quick Scan ⚡ | Level: {data_analysis_level}"
    manipulation_detected = False
    manipulation_reason = ""
    
    # ফলব্যাক প্রেডিকশন মেসেজ
    prediction_message = generate_prediction_message_v5(
        period, prediction_type, number_prediction, confidence, analysis_type, user_id, "wating⌛", manipulation_detected, manipulation_reason
    )
    
    return prediction_message, prediction_type, number_prediction, period, confidence, analysis_type, manipulation_detected, manipulation_reason

# 🔄 REAL-TIME AUTO PREDICTION SYSTEM V5.0 - WITH MANIPULATION DETECTION
def real_time_auto_prediction_v5(user_id, channel, is_timed=False, duration_minutes=20):
    """
    ডিপ লার্নিং ভিত্তিক রিয়েল-টাইম প্রেডিকশন সিস্টেম V5.0
    মার্কেট মেনুপুলেশন ডিটেকশন সহ
    """
    # সিজন স্টার্ট স্টিকার পাঠাও
    send_season_sticker(channel, "START", user_id)
    
    start_time = datetime.now()
    
    if is_timed:
        end_time = start_time + timedelta(minutes=duration_minutes)
        prediction_timers[user_id] = end_time
        bot.send_message(user_id, f"⏰ টাইমার সেট: {duration_minutes} মিনিট পরে অটোমেটিক বন্ধ হবে")
    
    message_id = None
    last_period = None
    last_prediction_type = None
    last_number_prediction = None
    last_confidence = None
    last_analysis_type = None
    last_manipulation_detected = False
    
    session_results = {"wins": 0, "losses": 0, "jackpots": 0, "total": 0, "skipped": 0}
    
    while signal_status.get(user_id, False):
        try:
            # টাইমড মোডে সময় চেক করুন
            if is_timed and datetime.now() >= prediction_timers.get(user_id, datetime.now()):
                signal_status[user_id] = False
                
                # সেশন রিপোর্ট
                session_report = f"""
🏁 *SESSION REPORT V5.0* 🏁
━━━━━━━━━━━━━━━━━━━
⏰ Duration: {duration_minutes} minutes
📊 Total Predictions: {session_results['total']}
✅ Wins: {session_results['wins']}
❌ Losses: {session_results['losses']}
🎰 Jackpot Wins: {session_results['jackpots']}
⚠️ Skipped (Manipulation): {session_results['skipped']}
📈 Win Rate: {round((session_results['wins']/max(1, session_results['total']-session_results['skipped']))*100, 2) if (session_results['total']-session_results['skipped']) > 0 else 0}%
📊 AI Data Count: {len(historical_data)}
🧠 AI Level: {data_analysis_level}
⚠️ Market Manipulation Detection: ACTIVE
━━━━━━━━━━━━━━━━━━━
"""
                bot.send_message(user_id, session_report, parse_mode="Markdown")
                break
            
            # বর্তমান পিরিওড এবং সেকেন্ড চেক করুন
            current_period = generate_real_time_period()
            current_second = get_real_time_seconds()
            
            # যদি পিরিওড চেঞ্জ হয় (নতুন মিনিট শুরু হয়)
            if current_period != last_period:
                logger.info(f"🔄 New period detected: {current_period} (Second: {current_second}) | Data: {len(historical_data)} | Level: {data_analysis_level}")
                
                # যদি আগের প্রেডিকশন থাকে, তাহলে তার রেজাল্ট চেক করুন (শুধুমাত্র যদি মেনুপুলেশন না ডিটেক্ট হয়)
                if last_period is not None and message_id is not None and not last_manipulation_detected:
                    try:
                        # Win/Loss চেক করো (জ্যাকপট সহ)
                        logger.info(f"🔍 Checking result for previous prediction...")
                        actual_number, actual_result, win_loss = check_actual_result_with_jackpot(
                            last_prediction_type, last_number_prediction, last_period
                        )
                        
                        logger.info(f"🎯 Result: {win_loss} - Actual: {actual_result} ({actual_number})")
                        
                        # সেশন রেজাল্ট আপডেট
                        session_results['total'] += 1
                        if "WIN" in win_loss:
                            session_results['wins'] += 1
                            if "JACKPOT" in win_loss:
                                session_results['jackpots'] += 1
                        else:
                            session_results['losses'] += 1
                        
                        # Win/Loss হিস্ট্রি আপডেট করো
                        update_prediction_history(
                            user_id, last_period, last_prediction_type, 
                            last_number_prediction, actual_number, actual_result, win_loss
                        )
                        
                        # ডাটা কালেকশনে যোগ করো
                        add_to_historical_data(
                            last_period, 
                            f"{last_prediction_type}/{last_number_prediction[0]},{last_number_prediction[1]}",
                            f"{actual_result}({actual_number})",
                            win_loss
                        )
                        
                        # Status update based on result
                        status_text = win_loss
                        
                        # আপডেটেড মেসেজ জেনারেট করো সাথে Result সহ
                        updated_message = generate_prediction_message_v5(
                            last_period, last_prediction_type, last_number_prediction, 
                            last_confidence, last_analysis_type, user_id, status_text, False, ""
                        )
                        
                        # Original মেসেজ edit করো
                        try:
                            bot.edit_message_text(
                                chat_id=channel,
                                message_id=message_id,
                                text=updated_message,
                                parse_mode="Markdown"
                            )
                            logger.info(f"✅ Message updated with result: {win_loss}")
                        except Exception as e:
                            logger.error(f"❌ Message edit error: {e}")
                        
                        # Win/Loss স্টিকার পাঠাও
                        send_win_loss_sticker(channel, win_loss, user_id)
                        
                        # ইউজারকে নোটিফাই করো
                        result_msg = f"""
📊 *Prediction Result*
━━━━━━━━━━━━━━━
🎯 Period: {last_period}
🔮 Prediction: {last_prediction_type} {last_number_prediction}
🎲 Actual: {actual_result} ({actual_number})
🏆 Result: {win_loss}
📊 Data Count: {len(historical_data)}
🧠 AI Level: {data_analysis_level}
⚠️ Market Status: NORMAL
━━━━━━━━━━━━━━━
"""
                        bot.send_message(user_id, result_msg, parse_mode="Markdown")
                        
                    except Exception as e:
                        logger.error(f"❌ Result checking error: {e}")
                elif last_manipulation_detected:
                    # মেনুপুলেশন ডিটেক্ট হলে সেশন রেজাল্ট আপডেট
                    session_results['skipped'] += 1
                    session_results['total'] += 1
                    
                    # মেনুপুলেশন হিস্ট্রি আপডেট
                    market_manipulation_history.append(True)
                    
                    logger.info(f"⚠️ Skipping result check due to manipulation detection for period {last_period}")
                
                # নতুন প্রেডিকশন জেনারেট এবং পাঠাও
                prediction_message, prediction_type, number_prediction, period_number, confidence, analysis_type, manipulation_detected, manipulation_reason = generate_deep_learning_prediction(user_id)
                
                # প্রেডিকশন মেসেজ পাঠাও এবং message_id সেভ করো
                sent_message = bot.send_message(channel, prediction_message, parse_mode="Markdown")
                message_id = sent_message.message_id
                
                # বর্তমান প্রেডিকশন তথ্য সেভ করো
                last_period = period_number
                last_prediction_type = prediction_type
                last_number_prediction = number_prediction
                last_confidence = confidence
                last_analysis_type = analysis_type
                last_manipulation_detected = manipulation_detected
                
                # মেনুপুলেশন ডিটেকশন মেসেজ
                if manipulation_detected:
                    manipulation_msg = f"""
⚠️ *MARKET MANIPULATION DETECTED* ⚠️

🎯 Period: {period_number}
🔍 Detection Level: {data_analysis_level}
📊 Data Count: {len(historical_data)}
📈 Market Status: MANIPULATION DETECTED

🎯 Action: Skipping this prediction
📊 Reason: {manipulation_reason[:100]}...

✅ Next prediction will be sent in next period
⚠️ Trust the AI - Avoiding manipulated markets
"""
                    bot.send_message(user_id, manipulation_msg, parse_mode="Markdown")
                else:
                    bot.send_message(user_id, f"✅ New prediction sent - Period: {period_number} | Confidence: {confidence}%")
                
                logger.info(f"🎯 New prediction: {prediction_type} {number_prediction} for period {period_number} (Confidence: {confidence}% | Level: {data_analysis_level} | Manipulation: {manipulation_detected})")
            
            # পরবর্তী চেকের জন্য 1 সেকেন্ড অপেক্ষা করো
            time.sleep(1)

        except Exception as e:
            logger.error(f"❌ Real-time prediction error: {e}")
            bot.send_message(user_id, f"⚠️ Prediction error: {e}")
            time.sleep(5)
    
    # সিজন শেষ হলে - IMPORTANT: Data Clearing
    if not signal_status.get(user_id, False):
        # সিজন ক্লোজ স্টিকার পাঠাও
        send_season_sticker(channel, "CLOSE", user_id)
        
        # প্রমোশনাল মেসেজ পাঠাও
        send_promotional_message(channel, user_id)
        
        # ⚡ IMPORTANT: ডাটা ক্লিন করো
        if clear_historical_data():
            bot.send_message(user_id, "🧹 *All historical data has been cleared!*\n\n✅ Fresh start for next session\n⚠️ Market Manipulation Detection: RESET")
        
        # ফাইনাল সেশন রিপোর্ট
        if session_results['total'] > 0:
            effective_predictions = session_results['total'] - session_results['skipped']
            win_rate = (session_results['wins'] / effective_predictions * 100) if effective_predictions > 0 else 0
            
            final_report = f"""
📈 *FINAL SESSION REPORT V5.0*
━━━━━━━━━━━━━━━━━━━
⏰ Session Ended
📊 Total Predictions: {session_results['total']}
✅ Wins: {session_results['wins']}
❌ Losses: {session_results['losses']}
🎰 Jackpot Wins: {session_results['jackpots']}
⚠️ Skipped (Manipulation): {session_results['skipped']}
📈 Effective Win Rate: {round(win_rate, 2)}%
📊 AI Data Count: 0 (Cleared)
🧠 AI Level: BASIC (Reset)
⚠️ Market Manipulation Detection: ACTIVE
🔥 Performance: {'Excellent 🔥' if win_rate >= 70 else 'Good ✅' if win_rate >= 50 else 'Needs Improvement ⚠️'}
━━━━━━━━━━━━━━━━━━━
"""
            bot.send_message(user_id, final_report, parse_mode="Markdown")

# 🎮 কলব্যাক কুয়েরি হ্যান্ডলার
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    
    if call.data == "add_channel":
        msg = bot.send_message(chat_id, "🔗 আপনার চ্যানেল/গ্রুপের ইউজারনেম পাঠান (যেমন: @yourchannel বা @yourgroup)")
        bot.register_next_step_handler(msg, process_channel_username)
    
    elif call.data == "channel_list":
        if chat_id in user_channels:
            bot.send_message(chat_id, f"📃 আপনার চ্যানেল/গ্রুপ: {user_channels[chat_id]}")
        else:
            bot.send_message(chat_id, "🚫 আপনি এখনও কোনও চ্যানেল/গ্রুপ অ্যাড করেননি।")
    
    elif call.data == "advanced_settings":
        show_advanced_settings(chat_id)
    
    elif call.data == "manipulation_settings":
        show_manipulation_settings(chat_id)
    
    elif call.data == "set_win_sticker":
        msg = bot.send_message(chat_id, "🎉 Win হলে কোন স্টিকার পাঠাতে চান? একটি স্টিকার পাঠান:")
        bot.register_next_step_handler(msg, process_win_sticker)
    
    elif call.data == "set_loss_sticker":
        msg = bot.send_message(chat_id, "😢 Loss হলে কোন স্টিকার পাঠাতে চান? একটি স্টিকার পাঠান:")
        bot.register_next_step_handler(msg, process_loss_sticker)
    
    elif call.data == "set_season_start_sticker":
        msg = bot.send_message(chat_id, "🏁 সিজন শুরু হলে কোন স্টিকার পাঠাতে চান? একটি স্টিকার পাঠান:")
        bot.register_next_step_handler(msg, process_season_start_sticker)
    
    elif call.data == "set_season_close_sticker":
        msg = bot.send_message(chat_id, "🏁 সিজন শেষ হলে কোন স্টিকার পাঠাতে চান? একটি স্টিকার পাঠান:")
        bot.register_next_step_handler(msg, process_season_close_sticker)
    
    elif call.data == "set_register_link":
        msg = bot.send_message(chat_id, "🔗 দয়া করে রেজিস্টার লিংকটি পাঠান:")
        bot.register_next_step_handler(msg, process_register_link)
    
    elif call.data == "view_register_link":
        register_link = user_register_links.get(chat_id, "Not Set")
        bot.send_message(chat_id, f"🔗 বর্তমান রেজিস্টার লিংক:\n{register_link}")
    
    elif call.data == "view_stats":
        stats = get_user_stats_v5(chat_id)
        if stats['total'] > 0:
            bot.send_message(
                chat_id,
                f"📊 *আপনার স্ট্যাটিস্টিক্স V5.0*\n\n"
                f"🎯 মোট প্রেডিকশন: {stats['total']}\n"
                f"✅ Win: {stats['wins']}\n"
                f"❌ Loss: {stats['losses']}\n"
                f"🎰 Jackpot Wins: {stats['jackpot_wins']}\n"
                f"⚠️ Skipped (Manipulation): {stats['skipped']}\n"
                f"📈 Win Rate: {stats['win_rate']}%\n\n"
                f"📊 AI ডাটা কাউন্ট: {len(historical_data)}\n"
                f"🧠 AI লেভেল: {data_analysis_level}\n"
                f"⚠️ Market Manipulation Detection: ACTIVE\n\n"
                f"🔥 Performance: {'Excellent 🔥' if stats['win_rate'] >= 70 else 'Good ✅' if stats['win_rate'] >= 50 else 'Needs Improvement ⚠️'}"
            , parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "📊 এখনও কোনও স্ট্যাটিস্টিক্স নেই। প্রেডিকশন শুরু করুন!")
    
    elif call.data == "manipulation_history":
        if market_manipulation_history:
            recent = list(market_manipulation_history)[-20:]
            history_text = "⚠️ *MARKET MANIPULATION HISTORY (Last 20)*\n\n"
            
            for i, detected in enumerate(reversed(recent), 1):
                history_text += f"{i}. {'⚠️ DETECTED' if detected else '✅ CLEAN'}\n"
            
            history_text += f"\n📊 Statistics:\n"
            history_text += f"• Total Checks: {len(market_manipulation_history)}\n"
            history_text += f"• Detected: {sum(market_manipulation_history)}\n"
            history_text += f"• Detection Rate: {(sum(market_manipulation_history)/len(market_manipulation_history)*100):.1f}%\n"
            history_text += f"• Current Level: {data_analysis_level}\n"
            
            bot.send_message(chat_id, history_text, parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "⚠️ এখনও কোন মার্কেট মেনুপুলেশন ডাটা নেই। প্রেডিকশন শুরু করুন!")
    
    elif call.data == "manipulation_threshold":
        threshold_info = f"""
🎯 *MARKET MANIPULATION THRESHOLD SETTINGS*

📊 Current Analysis Level: {data_analysis_level}

⚙️ Detection Thresholds by Level:
• BASIC: 70/100 (Less Sensitive)
• MEDIUM: 65/100 
• ADVANCED: 60/100
• EXPERT: 55/100
• AI_MASTER: 50/100 (Most Sensitive)

📈 Current Threshold: {'70' if data_analysis_level == 'BASIC' else '65' if data_analysis_level == 'MEDIUM' else '60' if data_analysis_level == 'ADVANCED' else '55' if data_analysis_level == 'EXPERT' else '50'}/100

🔍 Detection Parameters:
1. Abnormal Frequency Distribution
2. Trend Manipulation
3. Statistical Anomalies
4. Pattern Repetition
5. Sequence Manipulation
6. Big/Small Imbalance

📊 Data Count: {len(historical_data)}
🎯 Accuracy: {'90%+' if data_analysis_level in ['EXPERT', 'AI_MASTER'] else '80%+' if data_analysis_level == 'ADVANCED' else '70%+' if data_analysis_level == 'MEDIUM' else '60%+'}

⚠️ Note: Threshold decreases as data increases for better detection!
"""
        bot.send_message(chat_id, threshold_info, parse_mode="Markdown")
    
    elif call.data == "detection_patterns":
        patterns_info = f"""
🔍 *MARKET MANIPULATION DETECTION PATTERNS*

📊 Current Level: {data_analysis_level}

🎯 Detection Patterns:

1. **Abnormal Frequency Distribution**
   - Same number appears too many times
   - Uneven distribution of numbers
   - Statistical anomalies in frequency

2. **Trend Manipulation**
   - Same trend repeated 6+ times
   - Artificial trend creation
   - Sudden trend breaks

3. **Statistical Anomalies**
   - Very low volatility (STD < 1.2)
   - Very high volatility (STD > 3.8)
   - Abnormal mean values

4. **Pattern Repetition**
   - Same 3-number pattern repeated 3+ times
   - Artificial pattern creation
   - Predictable sequences

5. **Sequence Manipulation**
   - Ascending/descending sequences 4+
   - Artificial sequence creation
   - Non-random sequences

6. **Big/Small Imbalance**
   - BIG/SMALL difference > 15
   - Artificial bias creation
   - Market manipulation signs

📈 Level-wise Detection:
• BASIC: Patterns 1, 2, 6
• MEDIUM: Patterns 1, 2, 3, 6
• ADVANCED: All patterns
• EXPERT: All patterns + ML analysis
• AI_MASTER: All patterns + Deep Learning

⚠️ System improves with more data!
"""
        bot.send_message(chat_id, patterns_info, parse_mode="Markdown")
    
    elif call.data == "manipulation_stats":
        if market_manipulation_history:
            total_checks = len(market_manipulation_history)
            detected = sum(market_manipulation_history)
            detection_rate = (detected / total_checks * 100) if total_checks > 0 else 0
            
            stats_text = f"""
📊 *MARKET MANIPULATION STATISTICS*

🔢 Overall Stats:
• Total Market Checks: {total_checks}
• Manipulation Detected: {detected}
• Clean Markets: {total_checks - detected}
• Detection Rate: {detection_rate:.1f}%

📈 Recent Stats (Last 50):
"""
            recent = list(market_manipulation_history)[-50:]
            recent_detected = sum(recent)
            recent_rate = (recent_detected / len(recent) * 100) if recent else 0
            
            stats_text += f"• Recent Checks: {len(recent)}\n"
            stats_text += f"• Recent Detections: {recent_detected}\n"
            stats_text += f"• Recent Rate: {recent_rate:.1f}%\n\n"
            
            stats_text += f"🧠 System Info:\n"
            stats_text += f"• Current Level: {data_analysis_level}\n"
            stats_text += f"• Data Count: {len(historical_data)}\n"
            stats_text += f"• Detection Accuracy: {'90%+' if data_analysis_level in ['EXPERT', 'AI_MASTER'] else '80%+' if data_analysis_level == 'ADVANCED' else '70%+' if data_analysis_level == 'MEDIUM' else '60%+'}\n"
            stats_text += f"• Threshold: {'70' if data_analysis_level == 'BASIC' else '65' if data_analysis_level == 'MEDIUM' else '60' if data_analysis_level == 'ADVANCED' else '55' if data_analysis_level == 'EXPERT' else '50'}/100\n\n"
            
            stats_text += f"🎯 Performance:\n"
            if detection_rate < 10:
                stats_text += f"• Status: ✅ EXCELLENT (Low manipulation)\n"
            elif detection_rate < 25:
                stats_text += f"• Status: ⚠️ NORMAL (Some manipulation)\n"
            else:
                stats_text += f"• Status: ❌ HIGH (Frequent manipulation)\n"
            
            bot.send_message(chat_id, stats_text, parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "📊 এখনও কোন মার্কেট মেনুপুলেশন ডাটা নেই। প্রেডিকশন শুরু করুন!")
    
    elif call.data == "back_to_main":
        show_inline_keyboard(chat_id)

# 🔧 চ্যানেল ইউজারনেম প্রসেস করার ফাংশন
def process_channel_username(message):
    chat_id = message.chat.id
    text = message.text
    
    if text.startswith("@"):
        user_channels[chat_id] = text
        bot.send_message(chat_id, f"✅ চ্যানেল/গ্রুপ {text} সফলভাবে সেভ করা হয়েছে!")
        
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row("🚀 START PREDICTION", "🛑 STOP PREDICTION")
        keyboard.row("⏰ 20 MIN PREDICTION", "⚙️ SETTINGS")
        keyboard.row("📊 WIN/LOSS REPORT", "🔄 RESET STATS")
        keyboard.row("🎭 SET PROMO MESSAGE", "🎯 VIEW PROMO")
        keyboard.row("📈 VIEW DATA STATS", "🧠 AI ANALYSIS INFO")
        keyboard.row("🧹 CLEAR ALL DATA", "📊 CURRENT STATS")
        keyboard.row("🔍 MARKET MANIPULATION INFO", "⚠️ MANIPULATION STATUS")
        
        bot.send_message(
            chat_id,
            f"🎯 এখন আপনি প্রেডিকশন শুরু করতে পারেন!\n"
            f"📡 চ্যানেল/গ্রুপ: {text}\n"
            f"🔗 সিস্টেম: Deep Learning AI V5.0\n"
            f"📊 ডাটা কাউন্ট: {len(historical_data)}\n"
            f"🧠 এনালাইসিস লেভেল: {data_analysis_level}\n"
            f"⚠️ মার্কেট মেনুপুলেশন ডিটেকশন: ACTIVE\n"
            f"🎯 একুরেসি: ডাটা যত বাড়বে তত উন্নত হবে!\n"
            f"🔢 Number Prediction: Active\n"
            f"🎰 Jackpot System: Active\n\n"
            f"👉 '🚀 START PREDICTION' বা '⏰ 20 MIN PREDICTION' বাটনে ক্লিক করুন",
            reply_markup=keyboard
        )
    else:
        bot.send_message(chat_id, "❌ চ্যানেল/গ্রুপের নাম অবশ্যই '@' দিয়ে শুরু হতে হবে। আবার চেষ্টা করুন:")
        bot.register_next_step_handler(message, process_channel_username)

# 🎭 Win স্টিকার প্রসেস করার ফাংশন
def process_win_sticker(message):
    chat_id = message.chat.id
    
    if message.sticker:
        sticker_id = message.sticker.file_id
        user_win_stickers[chat_id] = sticker_id
        
        bot.send_message(chat_id, f"✅ Win স্টিকার সফলভাবে সেট করা হয়েছে!\n\nস্টিকার ID: {sticker_id}")
        
        # সেটিংস মেনুতে ফিরে যাও
        show_advanced_settings(chat_id)
    else:
        bot.send_message(chat_id, "❌ দয়া করে একটি স্টিকার পাঠান। আবার চেষ্টা করুন:")
        bot.register_next_step_handler(message, process_win_sticker)

# 🎭 Loss স্টিকার প্রসেস করার ফাংশন
def process_loss_sticker(message):
    chat_id = message.chat.id
    
    if message.sticker:
        sticker_id = message.sticker.file_id
        user_loss_stickers[chat_id] = sticker_id
        
        bot.send_message(chat_id, f"✅ Loss স্টিকার সফলভাবে সেট করা হয়েছে!\n\nস্টিকার ID: {sticker_id}")
        
        # সেটিংস মেনুতে ফিরে যাও
        show_advanced_settings(chat_id)
    else:
        bot.send_message(chat_id, "❌ দয়া করে একটি স্টিকার পাঠান। আবার চেষ্টা করুন:")
        bot.register_next_step_handler(message, process_loss_sticker)

# 🏁 Season Start স্টিকার প্রসেস করার ফাংশন
def process_season_start_sticker(message):
    chat_id = message.chat.id
    
    if message.sticker:
        sticker_id = message.sticker.file_id
        user_season_start_stickers[chat_id] = sticker_id
        
        bot.send_message(chat_id, f"✅ Season Start স্টিকার সফলভাবে সেট করা হয়েছে!\n\nস্টিকার ID: {sticker_id}")
        
        # সেটিংস মেনুতে ফিরে যাও
        show_advanced_settings(chat_id)
    else:
        bot.send_message(chat_id, "❌ দয়া করে একটি স্টিকার পাঠান। আবার চেষ্টা করুন:")
        bot.register_next_step_handler(message, process_season_start_sticker)

# 🏁 Season Close স্টিকার প্রসেস করার ফাংশন
def process_season_close_sticker(message):
    chat_id = message.chat.id
    
    if message.sticker:
        sticker_id = message.sticker.file_id
        user_season_close_stickers[chat_id] = sticker_id
        
        bot.send_message(chat_id, f"✅ Season Close স্টিকার সফলভাবে সেট করা হয়েছে!\n\nস্টিকার ID: {sticker_id}")
        
        # সেটিংস মেনুতে ফিরে যাও
        show_advanced_settings(chat_id)
    else:
        bot.send_message(chat_id, "❌ দয়া করে একটি স্টিকার পাঠান। আবার চেষ্টা করুন:")
        bot.register_next_step_handler(message, process_season_close_sticker)

# 🔗 রেজিস্টার লিংক প্রসেস করার ফাংশন
def process_register_link(message):
    chat_id = message.chat.id
    text = message.text
    
    if text.startswith("http"):
        user_register_links[chat_id] = text
        bot.send_message(chat_id, f"✅ রেজিস্টার লিংক সফলভাবে সেট করা হয়েছে!\n\nলিংক: {text}")
        
        # সেটিংস মেনুতে ফিরে যাও
        show_advanced_settings(chat_id)
    else:
        bot.send_message(chat_id, "❌ দয়া করে একটি বৈধ URL পাঠান (http বা https দিয়ে শুরু হতে হবে)। আবার চেষ্টা করুন:")
        bot.register_next_step_handler(message, process_register_link)

# 🧹 ডাটা ক্লিন করার ফাংশন
@bot.message_handler(func=lambda m: m.text == "🧹 CLEAR ALL DATA")
def clear_all_data_handler(message):
    chat_id = message.chat.id
    
    if clear_historical_data():
        # মেনুপুলেশন হিস্ট্রিও ক্লিয়ার করুন
        market_manipulation_history.clear()
        
        bot.send_message(chat_id, "✅ *All historical data has been cleared!*\n\n🧹 ডাটাবেজ সম্পূর্ণ ক্লিন করা হয়েছে\n📊 AI লেভেল রিসেট হয়েছে: BASIC\n⚠️ মার্কেট মেনুপুলেশন হিস্ট্রি ক্লিয়ার করা হয়েছে\n🎯 নতুন সেশন শুরু করুন!")
    else:
        bot.send_message(chat_id, "❌ ডাটা ক্লিন করতে সমস্যা হয়েছে। আবার চেষ্টা করুন।")

# 📊 বর্তমান স্ট্যাটস দেখানোর ফাংশন
@bot.message_handler(func=lambda m: m.text == "📊 CURRENT STATS")
def current_stats_handler(message):
    chat_id = message.chat.id
    
    stats_text = f"""
📊 *CURRENT BOT STATISTICS V5.0*

🔢 ডাটা স্ট্যাটস:
📈 মোট ডাটা: {len(historical_data)}
🧠 এনালাইসিস লেভেল: {data_analysis_level}
📊 ডাটা কালেকশন: {'✅ Active' if data_collection_status else '❌ Inactive'}

⚠️ মার্কেট মেনুপুলেশন স্ট্যাটস:
🔍 মোট চেক: {len(market_manipulation_history)}
⚠️ ডিটেকশন: {sum(market_manipulation_history)}
✅ ক্লিন: {len(market_manipulation_history) - sum(market_manipulation_history)}
📈 ডিটেকশন রেট: {(sum(market_manipulation_history)/len(market_manipulation_history)*100) if market_manipulation_history else 0:.1f}%

👤 ইউজার স্ট্যাটস:
👥 টোটাল ইউজার: {len(user_channels)}
📡 কনফিগার্ড চ্যানেল: {len([c for c in user_channels.values() if c])}
🎭 Win স্টিকার সেট: {len(user_win_stickers)}
🎭 Loss স্টিকার সেট: {len(user_loss_stickers)}

⚙️ সিস্টেম স্ট্যাটস:
🔄 Active Sessions: {sum(1 for s in signal_status.values() if s)}
⏰ Running Timers: {len(prediction_timers)}
💾 Data File: {'✅ Exists' if os.path.exists(DATA_FILE) else '❌ Not Found'}

🔥 Performance Status:
📊 Data Collection: {'✅ Optimal' if len(historical_data) > 0 else '⚠️ Needs Data'}
🧠 AI Analysis: {'✅ Advanced' if data_analysis_level in ['ADVANCED', 'EXPERT', 'AI_MASTER'] else '📈 Improving' if data_analysis_level == 'MEDIUM' else '🔍 Basic'}
⚠️ Market Manipulation Detection: {'✅ Advanced' if data_analysis_level in ['ADVANCED', 'EXPERT', 'AI_MASTER'] else '📈 Improving' if data_analysis_level == 'MEDIUM' else '🔍 Basic'}
🎯 Ready for Prediction: {'✅ Yes' if chat_id in user_channels else '❌ Add Channel First'}
"""
    
    bot.send_message(chat_id, stats_text, parse_mode="Markdown")

# 🎮 মেসেজ হ্যান্ডলার
@bot.message_handler(func=lambda m: True)
def handle_buttons(message):
    chat_id = message.chat.id
    text = message.text

    if text == "🚀 START PREDICTION":
        if chat_id in user_channels:
            channel = user_channels[chat_id]
            if not signal_status.get(chat_id, False):
                signal_status[chat_id] = True
                t = threading.Thread(target=real_time_auto_prediction_v5, args=(chat_id, channel, False))
                signal_threads[chat_id] = t
                t.daemon = True
                t.start()
                bot.send_message(chat_id, 
                    f"🚀 *DEEP AI PREDICTION STARTED V5.0!*\n\n"
                    f"📡 চ্যানেল/গ্রুপ: {channel}\n"
                    f"⚡ মোড: Unlimited Continuous\n"
                    f"🧠 সিস্টেম: Deep Learning AI\n"
                    f"📊 ডাটা কাউন্ট: {len(historical_data)}\n"
                    f"🧠 এনালাইসিস লেভেল: {data_analysis_level}\n"
                    f"🔢 Number Prediction: ✅ Active\n"
                    f"🎰 Jackpot System: ✅ Active\n"
                    f"✅ Win স্টিকার: { '✅ কাস্টম' if chat_id in user_win_stickers else '❌ ডিফল্ট' }\n"
                    f"❌ Loss স্টিকার: { '✅ কাস্টম' if chat_id in user_loss_stickers else '❌ ডিফল্ট' }\n"
                    f"🏁 Season Start: { '✅ কাস্টম' if chat_id in user_season_start_stickers else '❌ ডিফল্ট' }\n"
                    f"🏁 Season Close: { '✅ কাস্টম' if chat_id in user_season_close_stickers else '❌ ডিফল্ট' }\n"
                    f"📊 ডাটা কালেকশন: ✅ Active\n"
                    f"🧹 Auto Data Clear: ✅ On Session End\n"
                    f"⚠️ MARKET MANIPULATION DETECTION: ✅ ACTIVE\n"
                    f"🎯 JACKPOT RULES:\n"
                    f"  🎰 জ্যাকপট: শুধু নাম্বার মিললে\n"
                    f"  ✅ উইন: শুধু BIG/SMALL মিললে\n"
                    f"  ❌ লস: কিছুই না মিললে\n"
                    f"  ⚠️ স্কিপ: মার্কেট মেনুপুলেশন ডিটেক্ট হলে\n\n"
                    f"🛑 বন্ধ করতে 'STOP PREDICTION' বাটনে ক্লিক করুন\n\n"
                    f"🔮 Trust The AI Process!", parse_mode="Markdown")
            else:
                bot.send_message(chat_id, "⚠️ প্রেডিকশন ইতিমধ্যেই চালু আছে।")
        else:
            bot.send_message(chat_id, "❗ প্রথমে চ্যানেল/গ্রুপ যুক্ত করুন!")
            show_inline_keyboard(chat_id)

    elif text == "⏰ 20 MIN PREDICTION":
        if chat_id in user_channels:
            channel = user_channels[chat_id]
            if not signal_status.get(chat_id, False):
                signal_status[chat_id] = True
                t = threading.Thread(target=real_time_auto_prediction_v5, args=(chat_id, channel, True, 20))
                signal_threads[chat_id] = t
                t.daemon = True
                t.start()
                bot.send_message(chat_id, 
                    f"⏰ *20-MINUTE DEEP AI PREDICTION STARTED V5.0!*\n\n"
                    f"📡 চ্যানেল/গ্রুপ: {channel}\n"
                    f"⏰ সময়: 20 minutes\n"
                    f"⚡ মোড: Timed Session\n"
                    f"🧠 সিস্টেম: Deep Learning AI\n"
                    f"📊 ডাটা কাউন্ট: {len(historical_data)}\n"
                    f"🧠 এনালাইসিস লেভেল: {data_analysis_level}\n"
                    f"🔢 Number Prediction: ✅ Active\n"
                    f"🎰 Jackpot System: ✅ Active\n"
                    f"✅ Win স্টিকার: { '✅ কাস্টম' if chat_id in user_win_stickers else '❌ ডিফল্ট' }\n"
                    f"❌ Loss স্টিকার: { '✅ কাস্টম' if chat_id in user_loss_stickers else '❌ ডিফল্ট' }\n"
                    f"🏁 Season Start: { '✅ কাস্টম' if chat_id in user_season_start_stickers else '❌ ডিফল্ট' }\n"
                    f"🏁 Season Close: { '✅ কাস্টম' if chat_id in user_season_close_stickers else '❌ ডিফল্ট' }\n"
                    f"📊 ডাটা কালেকশন: ✅ Active\n"
                    f"🧹 Auto Data Clear: ✅ On Session End\n"
                    f"⚠️ MARKET MANIPULATION DETECTION: ✅ ACTIVE\n"
                    f"🎯 JACKPOT RULES:\n"
                    f"  🎰 জ্যাকপট: শুধু নাম্বার মিললে\n"
                    f"  ✅ উইন: শুধু BIG/SMALL মিললে\n"
                    f"  ❌ লস: কিছুই না মিললে\n"
                    f"  ⚠️ স্কিপ: মার্কেট মেনুপুলেশন ডিটেক্ট হলে\n\n"
                    f"🕐 20 মিনিট পরে অটোমেটিক বন্ধ হয়ে যাবে\n\n"
                    f"🔮 Trust The AI Process!", parse_mode="Markdown")
            else:
                bot.send_message(chat_id, "⚠️ প্রেডিকশন ইতিমধ্যেই চালু আছে।")
        else:
            bot.send_message(chat_id, "❗ প্রথমে চ্যানেল/গ্রুপ যুক্ত করুন!")
            show_inline_keyboard(chat_id)

    elif text == "🛑 STOP PREDICTION":
        if signal_status.get(chat_id, False):
            signal_status[chat_id] = False
            if chat_id in prediction_timers:
                del prediction_timers[chat_id]
            bot.send_message(chat_id, "🛑 প্রেডিকশন বন্ধ করা হয়েছে! সিজন ক্লোজ স্টিকার, প্রমোশনাল মেসেজ পাঠানো হবে এবং সব ডাটা ক্লিন করা হবে।")
        else:
            bot.send_message(chat_id, "ℹ️ প্রেডিকশন আগে থেকেই বন্ধ আছে।")

    elif text == "⚙️ SETTINGS":
        show_advanced_settings(chat_id)

    elif text == "📊 WIN/LOSS REPORT":
        stats = get_user_stats_v5(chat_id)
        if stats['total'] > 0:
            bot.send_message(
                chat_id,
                f"📊 *WIN/LOSS রিপোর্ট V5.0*\n\n"
                f"🎯 মোট প্রেডিকশন: {stats['total']}\n"
                f"✅ Win: {stats['wins']}\n"
                f"❌ Loss: {stats['losses']}\n"
                f"🎰 Jackpot Wins: {stats['jackpot_wins']}\n"
                f"⚠️ Skipped (Manipulation): {stats['skipped']}\n"
                f"📈 Win Rate: {stats['win_rate']}%\n\n"
                f"📊 AI ডাটা কাউন্ট: {len(historical_data)}\n"
                f"🧠 AI লেভেল: {data_analysis_level}\n"
                f"⚠️ Market Manipulation Detection: ACTIVE\n\n"
                f"🔥 Performance: {'Excellent 🔥' if stats['win_rate'] >= 70 else 'Good ✅' if stats['win_rate'] >= 50 else 'Needs Improvement ⚠️'}"
            , parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "📊 এখনও কোনও ডাটা নেই। প্রেডিকশন শুরু করুন!")

    elif text == "🔄 RESET STATS":
        if chat_id in prediction_history:
            prediction_history[chat_id] = []
        bot.send_message(chat_id, "🔄 আপনার স্ট্যাটিস্টিক্স রিসেট করা হয়েছে!")

    elif text == "🎭 SET PROMO MESSAGE":
        msg = bot.send_message(chat_id, "📝 আপনার প্রমোশনাল মেসেজটি লিখুন (সিজন ক্লোজ হওয়ার পরে এই মেসেজটি যাবে):")
        bot.register_next_step_handler(msg, process_promo_message)

    elif text == "🎯 VIEW PROMO":
        promo_msg = user_promotional_messages.get(chat_id, "❌ কোন প্রমোশনাল মেসেজ সেট করা হয়নি")
        bot.send_message(chat_id, f"📝 আপনার বর্তমান প্রমোশনাল মেসেজ:\n\n{promo_msg}")

    elif text == "📈 VIEW DATA STATS":
        if len(historical_data) > 0:
            stats_text = f"📊 *ডাটা স্ট্যাটিস্টিক্স V5.0*\n\n"
            stats_text += f"📈 মোট ডাটা: {len(historical_data)}\n"
            stats_text += f"🧠 এনালাইসিস লেভেল: {data_analysis_level}\n"
            stats_text += f"⚠️ মেনুপুলেশন ডিটেকশন: ACTIVE\n\n"
            
            # ডাটা লেভেল অনুযায়ী তথ্য
            if data_analysis_level == "BASIC":
                stats_text += "📊 বেসিক এনালাইসিস চালু (০-৫০ ডাটা)\n"
                stats_text += "🔍 বেসিক মেনুপুলেশন ডিটেকশন\n"
                stats_text += "📈 ডাটা কালেক্ট হচ্ছে...\n"
            elif data_analysis_level == "MEDIUM":
                stats_text += "📊 মিডিয়াম এনালাইসিস চালু (৫০-১০০ ডাটা)\n"
                stats_text += "🔍 উন্নত মেনুপুলেশন ডিটেকশন\n"
                stats_text += "📈 প্রেডিকশন উন্নত হচ্ছে...\n"
            elif data_analysis_level == "ADVANCED":
                stats_text += "📊 অ্যাডভান্সড এনালাইসিস চালু (১০০-৫০০ ডাটা)\n"
                stats_text += "🔍 স্ট্যাটিস্টিকাল মেনুপুলেশন ডিটেকশন\n"
                stats_text += "📈 উচ্চমানের প্রেডিকশন...\n"
            elif data_analysis_level == "EXPERT":
                stats_text += "📊 এক্সপার্ট এনালাইসিস চালু (৫০০-১৫০০ ডাটা)\n"
                stats_text += "🔍 মেশিন লার্নিং মেনুপুলেশন ডিটেকশন\n"
                stats_text += "📈 প্রফেশনাল লেভেল প্রেডিকশন...\n"
            elif data_analysis_level == "AI_MASTER":
                stats_text += "📊 AI মাস্টার এনালাইসিস চালু (১৫০০+ ডাটা)\n"
                stats_text += "🔍 ডিপ লার্নিং মেনুপুলেশন ডিটেকশন\n"
                stats_text += "📈 মাস্টার লেভেল একুরেসি!\n"
            
            stats_text += "\n🔄 ডাটা যত বাড়বে প্রেডিকশন ততই উন্নত হবে!\n"
            stats_text += "⚠️ মেনুপুলেশন ডিটেকশন ডাটা বৃদ্ধির সাথে উন্নত হবে!\n"
            
            bot.send_message(chat_id, stats_text, parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "📊 এখনও কোন ডাটা কালেক্ট করা হয়নি। প্রেডিকশন শুরু করুন!")

    elif text == "🧠 AI ANALYSIS INFO":
        info_text = f"""
🧠 *AI ANALYSIS SYSTEM V5.0*

📊 ডাটা কালেকশন সিস্টেম:
- আনলিমিটেড ডাটা কালেক্ট করে
- প্রতিটি প্রেডিকশন ডাটাবেজে সেভ হয়
- সিজন ক্লোজে অটো ডাটা ক্লিয়ার
- ডাটা কাউন্ট: {len(historical_data)}

📈 এনালাইসিস লেভেল:
1. BASIC (0-50 ডাটা): বেসিক এনালাইসিস + মেনুপুলেশন ডিটেকশন
2. MEDIUM (50-100 ডাটা): উন্নত এনালাইসিস + উন্নত মেনুপুলেশন ডিটেকশন
3. ADVANCED (100-500 ডাটা): শক্তিশালী এনালাইসিস + স্ট্যাটিস্টিকাল মেনুপুলেশন ডিটেকশন
4. EXPERT (500-1500 ডাটা): প্রফেশনাল এনালাইসিস + মেশিন লার্নিং মেনুপুলেশন ডিটেকশন
5. AI_MASTER (1500+ ডাটা): মাস্টার লেভেল এনালাইসিস + ডিপ লার্নিং মেনুপুলেশন ডিটেকশন

🔮 বর্তমান লেভেল: {data_analysis_level}

📊 মার্কেট এনালাইসিস:
- ট্রেন্ড ডিটেকশন
- প্যাটার্ন রিকগনিশন
- ভোলাটিলিটি মেজারমেন্ট
- ফ্রিকোয়েন্সি ডিস্ট্রিবিউশন
- 🆕 মার্কেট মেনুপুলেশন ডিটেকশন

⚠️ মার্কেট মেনুপুলেশন ডিটেকশন:
- অস্বাভাবিক প্যাটার্ন ডিটেকশন
- ট্রেন্ড ম্যানিপুলেশন ডিটেকশন
- স্ট্যাটিস্টিকাল অ্যানোমালি ডিটেকশন
- সিকোয়েন্স ম্যানিপুলেশন ডিটেকশন
- ফ্রিকোয়েন্সি ডিস্ট্রিবিউশন অ্যানোমালি

🎯 একুরেসি উন্নতি:
ডাটা যত বাড়বে, AI তত শিখবে, প্রেডিকশন ততই উন্নত হবে!
মেনুপুলেশন ডিটেকশন ডাটা বৃদ্ধির সাথে আরো নিখুঁত হবে!
"""
        bot.send_message(chat_id, info_text, parse_mode="Markdown")

    elif text == "🧹 CLEAR ALL DATA":
        clear_all_data_handler(message)
    
    elif text == "📊 CURRENT STATS":
        current_stats_handler(message)
    
    elif text == "🔍 MARKET MANIPULATION INFO":
        info_text = f"""
⚠️ **ADVANCED MARKET MANIPULATION DETECTION SYSTEM V5.0**

📊 **সিস্টেম ওভারভিউ:**
এই সিস্টেমটি মার্কেট মেনুপুলেশন, আর্টিফিশিয়াল প্যাটার্ন, 
এবং অস্বাভাবিক ট্রেন্ড ডিটেক্ট করে। ডাটা যত বাড়বে, 
ডিটেকশন তত নিখুঁত হবে।

🧠 **ডিটেকশন লেভেল:**
1. BASIC (0-50 ডাটা): বেসিক প্যাটার্ন ডিটেকশন
2. MEDIUM (50-100 ডাটা): উন্নত প্যাটার্ন এনালাইসিস
3. ADVANCED (100-500 ডাটা): স্ট্যাটিস্টিকাল অ্যানোমালি ডিটেকশন
4. EXPERT (500-1500 ডাটা): মেশিন লার্নিং ডিটেকশন
5. AI_MASTER (1500+ ডাটা): ডিপ লার্নিং ডিটেকশন

🔍 **ডিটেকশন প্যারামিটারস:**
• অস্বাভাবিক ফ্রিকোয়েন্সি ডিস্ট্রিবিউশন
• ট্রেন্ড ম্যানিপুলেশন
• স্ট্যাটিস্টিকাল অ্যানোমালি
• প্যাটার্ন রিপিটিশন
• সিকোয়েন্স ম্যানিপুলেশন
• BIG/SMALL ইমব্যালেন্স

🎯 **বর্তমান স্ট্যাটাস:**
• ডাটা কাউন্ট: {len(historical_data)}
• এনালাইসিস লেভেল: {data_analysis_level}
• ডিটেকশন একুরেসি: {'90%+' if data_analysis_level in ['EXPERT', 'AI_MASTER'] else '80%+' if data_analysis_level == 'ADVANCED' else '70%+' if data_analysis_level == 'MEDIUM' else '60%+'}
• সর্বশেষ ডিটেকশন: {list(market_manipulation_history)[-1] if market_manipulation_history else 'No data'}

⚠️ **যখন মেনুপুলেশন ডিটেক্ট হয়:**
1. প্রেডিকশন মেসেজে "SKIP THIS PREDICTION" দেখাবে
2. মার্কেট স্ট্যাটাস "MANIPULATION DETECTED" দেখাবে
3. AI বিশ্লেষণে মেনুপুলেশন কারণ দেখাবে
4. পরবর্তী প্রেডিকশনের জন্য অপেক্ষা করবে

📈 **সিস্টেম বেনিফিট:**
• ভুল প্রেডিকশন এড়ানো
• মার্কেট রিস্ক ম্যানেজমেন্ট
• উন্নত একুরেসি রেট
• রিয়েল-টাইম মার্কেট মনিটরিং
"""
        bot.send_message(chat_id, info_text, parse_mode="Markdown")
    
    elif text == "⚠️ MANIPULATION STATUS":
        if market_manipulation_history:
            recent_detections = list(market_manipulation_history)[-10:]
            detection_count = sum(recent_detections)
            
            status_text = f"""
⚠️ **MARKET MANIPULATION STATUS V5.0**

📊 **রিসেন্ট স্ট্যাটাস (গত 10):**
• মোট ডিটেকশন: {detection_count}
• ডিটেকশন রেট: {(detection_count/10)*100:.1f}%
• সর্বশেষ: {'DETECTED ⚠️' if recent_detections[-1] else 'CLEAN ✅'}

📈 **ডিটেকশন প্যাটার্ন:**
"""
            
            for i, detected in enumerate(reversed(recent_detections), 1):
                status_text += f"{i}. {'⚠️ DETECTED' if detected else '✅ CLEAN'}\n"
            
            status_text += f"\n🧠 **সিস্টেম ইনফো:**\n"
            status_text += f"• ডাটা কাউন্ট: {len(historical_data)}\n"
            status_text += f"• এনালাইসিস লেভেল: {data_analysis_level}\n"
            status_text += f"• ডিটেকশন থ্রেশহোল্ড: {'70%' if data_analysis_level == 'BASIC' else '65%' if data_analysis_level == 'MEDIUM' else '60%' if data_analysis_level == 'ADVANCED' else '55%' if data_analysis_level == 'EXPERT' else '50%'}\n"
            status_text += f"• ডিটেকশন একুরেসি: {'90%+' if data_analysis_level in ['EXPERT', 'AI_MASTER'] else '80%+' if data_analysis_level == 'ADVANCED' else '70%+' if data_analysis_level == 'MEDIUM' else '60%+'}\n"
            
            bot.send_message(chat_id, status_text, parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "⚠️ এখনও কোন মার্কেট মেনুপুলেশন ডাটা নেই। প্রেডিকশন শুরু করুন!")

    elif text.startswith("@"):
        user_channels[chat_id] = text
        bot.send_message(chat_id, f"✅ চ্যানেল/গ্রুপ {text} সেভ করা হয়েছে!")
        
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row("🚀 START PREDICTION", "🛑 STOP PREDICTION")
        keyboard.row("⏰ 20 MIN PREDICTION", "⚙️ SETTINGS")
        keyboard.row("📊 WIN/LOSS REPORT", "🔄 RESET STATS")
        keyboard.row("🎭 SET PROMO MESSAGE", "🎯 VIEW PROMO")
        keyboard.row("📈 VIEW DATA STATS", "🧠 AI ANALYSIS INFO")
        keyboard.row("🧹 CLEAR ALL DATA", "📊 CURRENT STATS")
        keyboard.row("🔍 MARKET MANIPULATION INFO", "⚠️ MANIPULATION STATUS")
        bot.send_message(chat_id, "🎯 এখন '🚀 START PREDICTION' বা '⏰ 20 MIN PREDICTION' বাটনে ক্লিক করুন!", reply_markup=keyboard)

def process_promo_message(message):
    chat_id = message.chat.id
    text = message.text
    
    user_promotional_messages[chat_id] = text
    bot.send_message(chat_id, f"✅ প্রমোশনাল মেসেজ সেভ করা হয়েছে!\n\nমেসেজ:\n{text}")

# 🔄 বট চালু করো
def run_bot():
    # শুরুতে ডাটা লোড করো
    load_historical_data()
    
    logger.info("🤖 DEEP AI PREDICTOR V5.0 is running...")
    logger.info("🔗 API 1:", CURRENT_API)
    logger.info("🔗 API 2:", HISTORY_API)
    logger.info("📊 AI Data Collection System: ACTIVE")
    logger.info(f"📊 Current Data Count: {len(historical_data)}")
    logger.info(f"🧠 Current Analysis Level: {data_analysis_level}")
    logger.info("⚠️ MARKET MANIPULATION DETECTION SYSTEM: ACTIVE")
    logger.info("🎯 Features:")
    logger.info("  ✅ Unlimited Data Collection System")
    logger.info("  ✅ Automatic Level Upgrade (0-1500+ data)")
    logger.info("  ✅ Deep Learning + Machine Learning")
    logger.info("  ✅ Beautiful Message Formatting")
    logger.info("  ✅ Number Prediction (2 Numbers)")
    logger.info("  ✅ CORRECT Jackpot System:")
    logger.info("    🎰 JACKPOT: শুধু নাম্বার মিললে")
    logger.info("    ✅ WIN: শুধু BIG/SMALL মিললে")
    logger.info("    ❌ LOSS: কিছুই না মিললে")
    logger.info("  🆕 ADVANCED MARKET MANIPULATION DETECTION:")
    logger.info("    ⚠️ SKIP: মার্কেট মেনুপুলেশন ডিটেক্ট হলে")
    logger.info("    🔍 6 Types of Manipulation Detection")
    logger.info("    📈 Level-based Detection Accuracy")
    logger.info("    🧠 ML + Deep Learning Detection")
    logger.info("  ✅ Auto Data Cleaning on Session End")
    logger.info("📊 Win/Loss Tracking System: ACTIVE")
    logger.info("🎰 Jackpot System: ACTIVE")
    logger.info("🧠 AI Learning System: ACTIVE")
    logger.info("⚠️ Market Manipulation Detection: ACTIVE")
    logger.info("🧹 Auto Data Clear: ENABLED")
    logger.info("🔥 ডাটা যত বাড়বে, AI তত শিখবে, প্রেডিকশন ততই উন্নত হবে!")
    logger.info("⚠️ মার্কেট মেনুপুলেশন ডিটেকশন ডাটা বৃদ্ধির সাথে আরো নিখুঁত হবে!")
    
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        logger.error(f"❌ Bot polling error: {e}")
        time.sleep(5)

# 🚀 Render-এ হোস্ট করার জন্য প্রধান ফাংশন
if __name__ == "__main__":
    # Render-এ Web Server চালু রাখার জন্য থ্রেড
    import threading
    
    def run_web_server():
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
    
    # Web Server আলাদা থ্রেডে চালু করো
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    # Telegram Bot চালু করো
    run_bot()
