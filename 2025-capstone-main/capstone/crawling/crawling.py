
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import os
import xml.etree.ElementTree as ET
from io import BytesIO
import zipfile
from dotenv import load_dotenv

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from tqdm import tqdm
from datetime import datetime

# DART API 관련 설정
DART_API_KEY = os.getenv("DART_API_KEY")
bsns_year = "2024"
reprt_code = "11011"
fs_div = "CFS"

# CSV 읽기 (업종 추가됨)
company_df = pd.read_csv("capstone_company_list.csv")
headers = {"User-Agent": "Mozilla/5.0"}
os.makedirs("output", exist_ok=True)

# DART API 호출 (corpCode.xml)
corp_code_url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={DART_API_KEY}"
res = requests.get(corp_code_url)
if res.status_code == 200:
    with zipfile.ZipFile(BytesIO(res.content)) as z:
        z.extractall("corp_data")
        print("✅ corp_code.xml 추출 완료")
else:
    print("❌ corp_code.xml 다운로드 실패")
    exit()

corp_tree = ET.parse("corp_data/CORPCODE.xml")
corp_root = corp_tree.getroot()

def get_corp_code(name):
    for item in corp_root.findall("list"):
        if item.findtext("corp_name") == name:
            return item.findtext("corp_code")
    return None

def fetch_financial_statement(corp_name, corp_code):
    url = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
    params = {
        "crtfc_key": DART_API_KEY,
        "corp_code": corp_code,
        "bsns_year": bsns_year,
        "reprt_code": reprt_code,
        "fs_div": fs_div,
    }
    try:
        res = requests.get(url, params=params)
        data = res.json()
        if data["status"] == "000":
            df = pd.DataFrame(data["list"])
            df["기업명"] = corp_name
            return df
        else:
            print(f"⚠️ {corp_name}: 재무제표 없음 - {data['message']}")
            return None
    except Exception as e:
        print(f"❌ {corp_name} 재무제표 오류: {e}")
        return None

BASE_URL = "https://finance.naver.com/item"
TAB_MAP = {
    "시세": "시세",
    "차트": "차트",
    "투자자매매동향": "투자자매매동향",
    "뉴스공시": "뉴스공시",
    "종목분석": "종목분석",
    "종목토론실": "종목토론실",
    "공매도현황": "공매도현황"
}

def get_html(url, headers):
    res = requests.get(url, headers=headers)
    return res.text if res.status_code == 200 else None

def crawl_table_from_url(url, headers):
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    table = soup.select_one("table.type2")
    data = []
    if table:
        for tr in table.select("tr")[2:]:
            tds = tr.find_all("td")
            if len(tds) == 7:
                row = {
                    "날짜": tds[0].get_text(strip=True),
                    "종가": tds[1].get_text(strip=True),
                    "전일비": tds[2].get_text(strip=True),
                    "시가": tds[3].get_text(strip=True),
                    "고가": tds[4].get_text(strip=True),
                    "저가": tds[5].get_text(strip=True),
                    "거래량": tds[6].get_text(strip=True)
                }
                data.append(row)
    return data

def crawl_chart_image(url, code):
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)

    try:
        # 불필요한 배너나 광고 요소 숨기기
        driver.execute_script("""
            var ads = document.querySelectorAll('.ad-banner, .popup');
            ads.forEach(function(ad) {
                ad.style.display = 'none';
            });
        """)

        # 차트가 로드될 때까지 기다림
        chart_element = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.ciq-chart-area'))
        )

        # 차트 캡쳐
        chart_element.screenshot(f"./output/{today_str}_{code}_chart_image.png")
    except TimeoutException:
        print(f"⚠️ {code}: 차트 로딩 실패 - 너무 오래 걸렸습니다.")
    except Exception as e:
        print(f"⚠️ {code}: 차트 스크린샷 실패 - {e}")
    finally:
        driver.quit()

def crawl_frgn_trading(url, headers):
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    table = soup.select_one("table.type2")
    data = []
    if table:
        for tr in table.select("tr"):
            tds = tr.select("td")
            if len(tds) == 4:
                data.append({
                    "매도상위": tds[0].get_text(strip=True),
                    "매도거래량": tds[1].get_text(strip=True),
                    "매수상위": tds[2].get_text(strip=True),
                    "매수거래량": tds[3].get_text(strip=True)
                })
        total = table.select_one("tr.total")
        if total:
            tds = total.select("td")
            data.append({
                "외국계추정합_매도": tds[1].get_text(strip=True),
                "외국계추정합_매수": tds[2].get_text(strip=True),
                "외국계추정합_거래량": tds[3].get_text(strip=True)
            })
    return data

def crawl_short_trade(url):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(url)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    tbody = soup.find('tbody', class_='CI-GRID-BODY-TABLE-TBODY')
    rows = tbody.find_all('tr')
    data = []
    for row in rows:
        cols = row.find_all('td')
        if len(cols) == 9:
            data.append({
                '일자': cols[0].text.strip(),
                '거래량 전체': cols[1].text.strip(),
                '거래량 업틱률적용': cols[2].text.strip(),
                '거래량 업틱률예외': cols[3].text.strip(),
                '순보유 잔고수량': cols[4].text.strip(),
                '거래대금 전체': cols[5].text.strip(),
                '거래대금 업틱률적용': cols[6].text.strip(),
                '거래대금 업틱률예외': cols[7].text.strip(),
                '순보유 잔고금액': cols[8].text.strip()
            })
    driver.quit()
    return pd.DataFrame(data)

def crawl_google_news(company_name):
    from selenium.common.exceptions import NoSuchElementException, WebDriverException

    news_data = []

    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    query = company_name
    url = f"https://www.google.com/search?q={query}&tbm=nws&hl=ko&gl=kr"
    driver.get(url)
    time.sleep(3)

    articles = driver.find_elements(By.CSS_SELECTOR, "#rso > div > div > div")

    for idx, article in enumerate(articles[:10], 1):
        try:
            title = article.find_element(By.CSS_SELECTOR, "div.n0jPhd.ynAwRc.MBeuO.nDgy9d").text.strip()
            press = article.find_element(By.CSS_SELECTOR, "div.MgUUmf span").text.strip()
            date = article.find_element(By.CSS_SELECTOR, "div.OSrXXb span").text.strip()
            link = article.find_element(By.CSS_SELECTOR, "a").get_attribute("href")

            driver.execute_script("window.open(arguments[0]);", link)
            driver.switch_to.window(driver.window_handles[1])
            time.sleep(4)

            try:
                content = driver.find_element(By.TAG_NAME, "body").get_attribute("innerText").strip()
            except:
                content = "본문 없음"

            # 창을 닫기 전에 열려있는지 확인
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

            if len(content) >= 500:
                content_trimmed = content[50:-50]  # 앞뒤 50자씩 제거하고 중간만 남김
            else:
                content_trimmed = content

            news_data.append({
                "제목": title,
                "언론사": press,
                "날짜": date,
                "본문": content_trimmed,
                "링크": link
            })

        except (NoSuchElementException, WebDriverException) as e:
            print(f"⚠️ 오류 발생: {e} (기사: {idx})")
            continue  # 에러 발생 시 다음 기사로 넘어감

    driver.quit()
    return news_data


def crawl_company_info(company_name):
    # 웹드라이버 설정
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # 네이버 증권 기업개요 페이지로 이동
    base_url = f"https://navercomp.wisereport.co.kr/v2/company/c1020001.aspx?cmp_cd=318160&cn="
    driver.get(base_url)
    time.sleep(3)  # 페이지 로딩 대기
    
    try:
        # 본사주소, 홈페이지, 대표이사, 설립일 크롤링
        address = driver.find_element(By.XPATH, '//*[@id="cTB201"]/tbody/tr[1]/td').text.strip()  # 본사주소
        homepage = driver.find_element(By.XPATH, '//*[@id="cTB201"]/tbody/tr[2]/td[1]/a').get_attribute("href").strip()  # 홈페이지
        ceo = driver.find_element(By.XPATH, '//*[@id="cTB201"]/tbody/tr[3]/td[2]').text.strip()  # 대표이사
        establishment_date = driver.find_element(By.XPATH, '//*[@id="cTB201"]/tbody/tr[3]/td[1]').text.strip()  # 설립일

        # 크롤링한 정보 저장
        company_info = {
            "본사주소": address,
            "홈페이지": homepage,
            "대표이사": ceo,
            "설립일": establishment_date
        }

    except Exception as e:
        print(f"❌ 크롤링 오류: {e}")
        company_info = {}

    driver.quit()
    return company_info


today_str = datetime.today().strftime('%Y%m%d')

def crawl_tab_content(url, code, section, sector=None):
    if section == "시세":
        main_url = f"{BASE_URL}/main.naver?code={code}"
        time_url = f"{BASE_URL}/sise_time.naver?code={code}"
        day_url = f"{BASE_URL}/sise_day.naver?code={code}"
        return {
            "주요시세": get_html(main_url, headers),
            "시간별시세": get_html(time_url, headers),
            "일별시세": crawl_table_from_url(day_url, headers)
        }
    elif section == "차트":
        crawl_chart_image(f"{BASE_URL}/fchart.naver?code={code}", code)
        return {"차트": "저장됨"}
    elif section == "투자자매매동향":
        return crawl_frgn_trading(f"{BASE_URL}/frgn.naver?code={code}", headers)
    elif section == "뉴스공시":
        return crawl_google_news(name)  # 'name' → 'code' 또는 실제 회사명
    elif section == "종목분석":
        # 업종 추가
        company_info = crawl_company_info(name)  # 크롤링한 기업정보 추가
        return {
            "업종": sector,
            "본사주소": company_info.get("본사주소"),
            "홈페이지": company_info.get("홈페이지"),
            "대표이사": company_info.get("대표이사"),
            "설립일": company_info.get("설립일"),
            "종목분석": crawl_table_from_url(f"{BASE_URL}/coinfo.naver?code={code}", headers)
        }
    elif section == "종목토론실":
        soup = BeautifulSoup(get_html(f"{BASE_URL}/board.nhn?code={code}", headers), 'html.parser')
        posts = []
        for tr in soup.select('table.type2 tbody tr')[5:]:
            title_tag = tr.select_one('td.title a')
            date_tag = tr.select_one('td span')
            if title_tag:
                link = "https://finance.naver.com" + title_tag['href']
                content = BeautifulSoup(requests.get(link, headers=headers).text, 'html.parser').select_one('#body')
                posts.append({
                    "title": title_tag.text.strip(),
                    "date": date_tag.text.strip() if date_tag else "날짜 없음",
                    "content": content.text.strip() if content else "내용 없음"
                })
        return posts
    elif section == "공매도현황":
        return crawl_short_trade(f"https://data.krx.co.kr/comm/srt/srtLoader/index.cmd?screenId=MDCSTAT300&isuCd={code}")


# 기업 크롤링 실행
for idx, row in tqdm(company_df.iterrows(), total=len(company_df), desc="기업 크롤링 진행"):
    name = row['기업명']
    code = str(row['종목코드']).zfill(6)
    sector = row['업종']  # 업종 데이터 추가

    print(f"\n📦 {name} ({code}) 크롤링 중...")

    result = {"기업명": name, "종목코드": code, "업종": sector}  # 업종 포함

    # 본사주소, 홈페이지, 대표이사, 설립일 크롤링
    company_info = crawl_company_info(name)
    result.update(company_info)  # 딕셔너리 업데이트하여 추가

    df_short = crawl_short_trade(f"https://data.krx.co.kr/comm/srt/srtLoader/index.cmd?screenId=MDCSTAT300&isuCd={code}")
    result["공매도현황"] = df_short.to_dict(orient="records")

    for section, title in TAB_MAP.items():
        if section == "공매도현황":
            continue
        print(f" → {title} 크롤링 중...")
        result[title] = crawl_tab_content(f"{BASE_URL}/{section}.naver?code={code}", code, title, sector)
        time.sleep(10)

    corp_code = get_corp_code(name)
    if corp_code:
        df_fin = fetch_financial_statement(name, corp_code)
        if df_fin is not None:
            df_fin.to_csv(f"output/{today_str}_{name}_{bsns_year}_재무제표.csv", index=False, encoding="utf-8-sig")

    with open(f"output/{today_str}_{name}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    df_short.to_csv(f"output/{today_str}_{name}_short_trade.csv", index=False, encoding="utf-8-sig")
    time.sleep(5)
