"""
STRUGGLE AI - Quotex Price Collector
Auto runs every 1 minute via GitHub Actions
"""

import json
import os
from datetime import datetime
import requests
import pytz

# Dhaka Timezone
DHAKA_TZ = pytz.timezone('Asia/Dhaka')

# All Currency Pairs
REAL_PAIRS = [
    "CAD/JPY", "GBP/JPY", "EUR/JPY", "AUD/JPY", "CHF/JPY",
    "EUR/CHF", "EUR/USD", "GBP/AUD", "AUD/CAD", "EUR/AUD",
    "EUR/CAD", "GBP/USD", "AUD/CHF", "AUD/USD", "GBP/CAD",
    "GBP/CHF", "EUR/GBP", "USD/JPY", "USD/CAD", "USD/CHF"
]

OTC_PAIRS = [
    "USD/BRL", "EUR/NZD", "USD/PHP", "USD/BDT", "NZD/JPY",
    "USD/IDR", "CAD/CHF", "NZD/CHF", "USD/ARS", "NZD/CAD",
    "USD/DZD", "USD/NGN", "USD/COP", "USD/ZAR", "AUD/NZD",
    "USD/EGP", "USD/INR", "USD/MXN", "USD/PKR", "NZD/USD",
    "GBP/NZD"
]

def get_current_time():
    """Get current Dhaka time"""
    return datetime.now(DHAKA_TZ)

def fetch_price_data(pair, market_type="real"):
    """
    Fetch price data for a pair
    Using Yahoo Finance API (FREE, no key needed)
    """
    try:
        # Convert pair format: EUR/USD -> EURUSD=X
        symbol = pair.replace("/", "") + "=X"
        
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {
            "interval": "1m",
            "range": "1d"
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        
        if "chart" in data and data["chart"]["result"]:
            result = data["chart"]["result"][0]
            timestamps = result["timestamp"]
            quotes = result["indicators"]["quote"][0]
            
            candles = []
            for i, ts in enumerate(timestamps):
                if quotes["open"][i] is not None:
                    candle_time = datetime.fromtimestamp(ts, DHAKA_TZ)
                    candles.append({
                        "time": candle_time.strftime("%H:%M:%S"),
                        "timestamp": ts,
                        "open": quotes["open"][i],
                        "high": quotes["high"][i],
                        "low": quotes["low"][i],
                        "close": quotes["close"][i],
                        "volume": quotes["volume"][i] if quotes["volume"][i] else 0
                    })
            
            return {
                "pair": pair,
                "market_type": market_type,
                "last_updated": get_current_time().strftime("%Y-%m-%d %H:%M:%S"),
                "candles": candles[-100:]  # Last 100 candles
            }
    except Exception as e:
        print(f"❌ Error fetching {pair}: {str(e)}")
        return None

def save_to_folder(data, market_type, pair):
    """Save data to organized folder structure"""
    if data is None:
        return False
    
    # Create folder structure
    today = get_current_time().strftime("%Y-%m-%d")
    pair_clean = pair.replace("/", "_")
    
    folder_path = f"data/{market_type}_market/{pair_clean}"
    os.makedirs(folder_path, exist_ok=True)
    
    # Save daily file
    file_path = f"{folder_path}/{today}.json"
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Saved: {file_path}")
    return True

def collect_all_data():
    """Main function to collect all pairs data"""
    current_time = get_current_time()
    print(f"\n{'='*60}")
    print(f"🚀 STRUGGLE AI - Data Collection Started")
    print(f"⏰ Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')} (Dhaka)")
    print(f"{'='*60}\n")
    
    success_count = 0
    fail_count = 0
    
    # Check if weekend
    is_weekend = current_time.weekday() in [5, 6]  # Saturday=5, Sunday=6
    
    # Collect Real Market Data (Mon-Fri only)
    if not is_weekend:
        print("🌍 COLLECTING REAL MARKET DATA...\n")
        for pair in REAL_PAIRS:
            data = fetch_price_data(pair, "real")
            if save_to_folder(data, "real", pair):
                success_count += 1
            else:
                fail_count += 1
    else:
        print("📅 Weekend detected - Real Market closed\n")
    
    # Collect OTC Data (24/7)
    print("\n🤖 COLLECTING OTC MARKET DATA...\n")
    for pair in OTC_PAIRS:
        # For OTC, we use real pair data as baseline
        data = fetch_price_data(pair, "otc")
        if data:
            data["pair"] = pair + "-OTC"
            data["note"] = "OTC simulated from real market data"
        if save_to_folder(data, "otc", pair):
            success_count += 1
        else:
            fail_count += 1
    
    # Save collection summary
    summary = {
        "last_collection": current_time.strftime("%Y-%m-%d %H:%M:%S"),
        "success": success_count,
        "failed": fail_count,
        "total_pairs": len(REAL_PAIRS) + len(OTC_PAIRS),
        "is_weekend": is_weekend,
        "real_market": "closed" if is_weekend else "open",
        "otc_market": "open"
    }
    
    os.makedirs("data", exist_ok=True)
    with open("data/last_update.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ Collection Complete!")
    print(f"📊 Success: {success_count} | Failed: {fail_count}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    collect_all_data()
