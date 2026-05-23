import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
import io
import os
import time
import warnings
from deep_translator import GoogleTranslator

# 忽略 pandas 未來版本的警告
warnings.simplefilter(action='ignore', category=FutureWarning)

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

SECTOR_MAP = {
    'Technology': '科技', 'Financial Services': '金融服務', 'Consumer Defensive': '必需消費',
    'Consumer Cyclical': '非必需消費', 'Healthcare': '醫療保健', 'Industrials': '工業',
    'Basic Materials': '原物料', 'Energy': '能源', 'Utilities': '公用事業',
    'Real Estate': '房地產', 'Communication Services': '通訊服務'
}

def get_company_details(ticker, close_price):
    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        company_name = info.get('shortName', info.get('longName', ticker))
        sector = info.get('sector', 'Unknown')
        pe = f"{info.get('trailingPE', 0):.2f}" if isinstance(info.get('trailingPE'), (int, float)) else "N/A"
        raw_yield = info.get('dividendYield')
        div = f"{raw_yield * 100:.2f}%" if isinstance(raw_yield, (int, float)) else "N/A"
        summary_en = info.get('longBusinessSummary', '')[:300]
        summary_zh = GoogleTranslator(source='auto', target='zh-TW').translate(summary_en) + "..."
        return summary_zh, pe, div, company_name, sector
    except:
        return "暫無簡介", "N/A", "N/A", ticker, "Unknown"

def send_to_discord(ticker, name, sector, price, pct, img, summary, pe, div):
    emoji, trend = ("📈", "漲幅") if pct > 0 else ("📉", "跌幅")
    msg = (f"{emoji} **{ticker} - {name}**\n🏢 版塊: {SECTOR_MAP.get(sector, sector)}\n"
           f"📊 本益比: {pe} | 💰 股息率: {div}\n📝 簡介: {summary}\n"
           f"🔹 收盤價: ₩{price:.2f}\n{emoji} {trend}: **{pct * 100:.2f}%**")
    img.seek(0)
    requests.post(WEBHOOK_URL, data={"content": msg}, files={"file": (f"{ticker}.png", img, "image/png")})

def process_and_send_list(series, title, color):
    requests.post(WEBHOOK_URL, json={"content": f"📊 **{title}** 📊"})
    for ticker, pct in series.items():
        try:
            data = yf.download(ticker, period="9mo", progress=False)
            if data.empty: continue
            
            if isinstance(data.columns, pd.MultiIndex):
                close_series = data['Close'][ticker] if 'Close' in data.columns else data.iloc[:, 0]
            else:
                close_series = data['Close'] if 'Close' in data.columns else data.iloc[:, 0]

            sum_zh, pe, div, name, sec = get_company_details(ticker, close_series.iloc[-1])

            plt.figure(figsize=(10, 5))
            plt.plot(close_series.index, close_series, color=color, linewidth=1.5)
            plt.title(f"{ticker} {name} - 1 Year Trend", fontsize=14)
            plt.grid(True, linestyle='--', alpha=0.5)
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            plt.close()
            
            send_to_discord(ticker, name, sec, close_series.iloc[-1], pct, buf, sum_zh, pe, div)
            time.sleep(2)
        except Exception as e:
            print(f"處理 {ticker} 發生錯誤: {e}")
            continue

def main():
    # KOSPI 前 200 大權值股 (KOSPI 200 成分股)
    KOSPI_TICKERS = [
        "005930.KS", "000660.KS", "373220.KS", "207940.KS", "005380.KS", "000270.KS", "068270.KS", "005490.KS", 
        "035420.KS", "006400.KS", "051910.KS", "105560.KS", "035720.KS", "028260.KS", "055550.KS", "012330.KS", 
        "066570.KS", "032830.KS", "086900.KS", "015760.KS", "034730.KS", "034020.KS", "323410.KS", "003550.KS", 
        "011200.KS", "018260.KS", "090430.KS", "033920.KS", "316140.KS", "009150.KS", "009830.KS", "051900.KS", 
        "010950.KS", "259960.KS", "010130.KS", "024110.KS", "011170.KS", "003670.KS", "030200.KS", "042700.KS", 
        "000810.KS", "352820.KS", "000100.KS", "010140.KS", "271560.KS", "005830.KS", "011070.KS", "047810.KS", 
        "086280.KS", "028050.KS", "004020.KS", "001450.KS", "021240.KS", "161390.KS", "008770.KS", "012450.KS", 
        "006800.KS", "139480.KS", "282330.KS", "112610.KS", "000720.KS", "008930.KS", "000120.KS", "005940.KS", 
        "032640.KS", "006280.KS", "180640.KS", "011790.KS", "036570.KS", "267250.KS", "204320.KS", "004990.KS", 
        "002380.KS", "000990.KS", "010620.KS", "069260.KS", "016360.KS", "001430.KS", "001040.KS", "001800.KS", 
        "017800.KS", "039490.KS", "014680.KS", "078930.KS", "003490.KS", "047040.KS", "020150.KS", "138040.KS", 
        "005385.KS", "029780.KS", "000210.KS", "000080.KS", "007310.KS", "241560.KS", "096770.KS", "010060.KS", 
        "004170.KS", "064350.KS", "005935.KS", "128940.KS", "001500.KS", "006360.KS", "004800.KS", "000240.KS",
        "005387.KS", "001440.KS", "020000.KS", "000150.KS", "031430.KS", "005389.KS", "001060.KS", "003410.KS",
        "008560.KS", "012510.KS", "011210.KS", "073240.KS", "009540.KS", "010120.KS", "004000.KS", "005850.KS",
        "000030.KS", "002790.KS", "042660.KS", "005250.KS", "000670.KS", "001740.KS", "069960.KS", "001680.KS",
        "000880.KS", "036460.KS", "013890.KS", "001120.KS", "002320.KS", "071050.KS", "009240.KS", "004370.KS",
        "026960.KS", "001230.KS", "003300.KS", "011780.KS", "014830.KS", "009420.KS", "011000.KS", "006260.KS",
        "000230.KS", "001520.KS", "003090.KS", "000220.KS", "001130.KS", "004490.KS", "005930.KS", "014820.KS",
        "001750.KS", "000370.KS", "003240.KS", "002240.KS", "005440.KS", "000815.KS", "005610.KS", "004890.KS",
        "001360.KS", "000390.KS", "009410.KS", "000400.KS", "006120.KS", "002200.KS", "001390.KS", "005300.KS",
        "002310.KS", "003200.KS", "001510.KS", "000500.KS", "000490.KS", "001080.KS", "001470.KS", "002810.KS",
        "003530.KS", "003540.KS", "001790.KS", "001250.KS", "001720.KS", "000520.KS", "003620.KS", "001380.KS",
        "001420.KS", "003850.KS", "001020.KS", "004130.KS", "002710.KS", "002270.KS", "002350.KS", "003650.KS"
    ]
    
    print(f"正在下載 {len(KOSPI_TICKERS)} 檔韓國股價...")
    data = yf.download(KOSPI_TICKERS, period="10d", progress=False)
    
    if data.empty:
        return

    try:
        close_data = data['Close']
    except KeyError:
        try:
            close_data = data.xs('Close', level=0, axis=1)
        except KeyError:
            close_data = data

    last_two = close_data.dropna(how='all').tail(2)
    if len(last_two) < 2:
        requests.post(WEBHOOK_URL, json={"content": "⚠️ 目前韓國市場休市，無最新漲跌資料可計算。"})
        return
        
    returns = last_two.pct_change(fill_method=None).iloc[-1].dropna()
    
    if returns.empty:
        requests.post(WEBHOOK_URL, json={"content": "⚠️ 無法計算漲跌幅，可能是因為資料缺失。"})
        return
    
    process_and_send_list(returns.nlargest(10), "今日 KOSPI 漲幅前十名", '#1f77b4')
    process_and_send_list(returns.nsmallest(10), "今日 KOSPI 跌幅最重前十名", 'green')

if __name__ == "__main__":
    main()
