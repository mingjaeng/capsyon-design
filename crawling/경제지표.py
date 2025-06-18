import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime  # ⬅️ 현재 시간 추가용

def get_naver_finance_index():
    result = {}

    # KOSPI, KOSDAQ 크롤링
    try:
        url = "https://finance.naver.com/sise/"
        resp = requests.get(url)
        resp.encoding = "euc-kr"
        soup = BeautifulSoup(resp.text, "html.parser")

        kospi = soup.select_one("#KOSPI_now")
        kosdaq = soup.select_one("#KOSDAQ_now")

        result["KOSPI"] = kospi.text.strip() if kospi else "N/A"
        result["KOSDAQ"] = kosdaq.text.strip() if kosdaq else "N/A"
    except Exception as e:
        result["KOSPI"] = result["KOSDAQ"] = f"에러: {e}"

    # 환율, 금시세 크롤링
    try:
        fx_url = "https://finance.naver.com/marketindex/"
        fx_resp = requests.get(fx_url)
        fx_resp.encoding = "euc-kr"
        fx_soup = BeautifulSoup(fx_resp.text, "html.parser")

        # USD/KRW 환율
        usd = fx_soup.select_one("div.market1 div.head_info > span.value")
        result["USD/KRW"] = usd.text.strip() if usd else "N/A"

        # 금 시세 (1g 기준)
        gold = fx_soup.select_one("div.market2 div.head_info > span.value")
        result["금시세(1g)"] = gold.text.strip() if gold else "N/A"

    except Exception as e:
        result["USD/KRW"] = result["금시세(1g)"] = f"에러: {e}"

    # 📅 현재 시간 추가 (자연어 형식)
    now = datetime.now()
    result["last_updated"] = now.strftime("%m월 %d일 %H시 %M분 %S초 기준")

    return result

if __name__ == "__main__":
    data = get_naver_finance_index()

    # JSON 저장
    with open("economic_index.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print("📈 크롤링된 경제지표:")
    print(json.dumps(data, indent=4, ensure_ascii=False))
