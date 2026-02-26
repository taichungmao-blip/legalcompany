import os
import json
import requests
import datetime
import urllib3
from bs4 import BeautifulSoup

# 關閉略過 SSL 驗證時產生的警告訊息
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

HISTORY_FILE = "history.json"

def send_discord_notify(message):
    if not WEBHOOK_URL or "你的/真實網址" in WEBHOOK_URL:
        print("未設定有效的 DISCORD_WEBHOOK_URL，跳過發送通知")
        return
    data = {"content": message}
    requests.post(WEBHOOK_URL, json=data)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def fetch_mops_data(typek):
    url_main = "https://mopsov.twse.com.tw/mops/web/t100sb02_1"
    url_ajax = "https://mopsov.twse.com.tw/mops/web/ajax_t100sb02_1"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://mopsov.twse.com.tw/mops/web/t100sb02_1",
        "Origin": "https://mopsov.twse.com.tw",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    now = datetime.datetime.now()
    roc_year = str(now.year - 1911)
    current_month = str(now.month).zfill(2)

    payload = {
        "encodeURIComponent": "1",
        "step": "1",
        "firstin": "1",
        "off": "1",
        "TYPEK": typek,
        "year": roc_year,
        "month": current_month,
        "co_id": ""
    }
    
    try:
        session = requests.Session()
        session.get(url_main, headers=headers, verify=False, timeout=10)
        response = session.post(url_ajax, headers=headers, data=payload, verify=False, timeout=10)
        
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"爬取 {typek} 失敗: {e}")
        return ""

def parse_and_notify():
    history = load_history()
    new_history = history.copy()
    
    # 加入 rotc (興櫃)
    for typek in ["sii", "otc", "rotc"]:
        html = fetch_mops_data(typek)
        if not html:
            continue
            
        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")
        
        if not tables:
            continue
            
        # 跳過標題列，直接解析資料列
        for tr in tables[0].find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 5: 
                continue
                
            try:
                company_code = tds[0].text.strip()
                company_name = tds[1].text.strip()
                date = tds[2].text.strip()
                time = tds[3].text.strip()
                location = tds[4].text.strip() 
                summary = tds[5].text.strip()  
            except IndexError:
                continue
            
            event_id = f"{company_code}_{date}"
            
            if event_id not in history:
                # 判斷公司類型中文名稱
                if typek == "sii":
                    type_name = "上市"
                elif typek == "otc":
                    type_name = "上櫃"
                elif typek == "rotc":
                    type_name = "興櫃"
                else:
                    type_name = "未知"

                message = (
                    f"📢 **新法說會通知 ({type_name})**\n"
                    f"**公司**：{company_code} {company_name}\n"
                    f"**日期**：{date}\n"
                    f"**時間**：{time}\n"
                    f"**地點**：{location}\n"
                    f"**內容**：{summary}\n"
                    f"[前往公開資訊觀測站](https://mopsov.twse.com.tw/mops/web/t100sb02_1)"
                )
                send_discord_notify(message)
                new_history.append(event_id)
                
    save_history(new_history)

if __name__ == "__main__":
    parse_and_notify()
