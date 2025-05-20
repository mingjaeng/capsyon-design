from django.shortcuts import render, redirect
from django.http import JsonResponse
import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


# 홈 리디렉션
def home_redirect(request):
    return redirect('https://mingjaeng.github.io/capsyon-design/')


# 기업명 → 종목코드 검색
def get_stock_code(company_name):
    search_url = f"https://finance.naver.com/search/searchList.naver?query={company_name}"
    res = requests.get(search_url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(res.text, 'html.parser')
    a_tag = soup.select_one('ul.searchList li a')
    if a_tag:
        href = a_tag.get('href')
        if 'code=' in href:
            return href.split('code=')[-1]
    return None


# 종목코드로 주가 정보 가져오기
def get_stock_info(code):
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(res.text, 'html.parser')
    try:
        price = soup.select_one('p.no_today span.blind').text
        change = soup.select_one('p.no_exday span.blind').text
        rate = soup.select('p.no_exday span')[-1].text.strip()
        return price, change, rate
    except:
        return None, None, None


# 경제지표 정보 가져오기
def get_economic_indicators():
    indicators = {}
    market_url = 'https://finance.naver.com/marketindex/'
    res = requests.get(market_url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(res.text, 'html.parser')

    try:
        usd_tag = soup.select_one('div.market1 ul.data_lst li:nth-of-type(1) span.value')
        indicators['USD/KRW'] = usd_tag.text.strip() if usd_tag else None
    except:
        indicators['USD/KRW'] = None

    try:
        gold_items = soup.select("ul.data_lst li")
        for item in gold_items:
            title_tag = item.select_one('h3')
            if title_tag and '국내 금' in title_tag.text:
                gold_value = item.select_one('.value')
                indicators['국내 금'] = gold_value.text.strip() if gold_value else None
                break
        else:
            indicators['국내 금'] = None
    except:
        indicators['국내 금'] = None

    try:
        sise_url = 'https://finance.naver.com/sise/'
        res2 = requests.get(sise_url, headers={'User-Agent': 'Mozilla/5.0'})
        soup2 = BeautifulSoup(res2.text, 'html.parser')
        indicators['KOSPI'] = soup2.select_one('#KOSPI_now').text.strip()
        indicators['KOSDAQ'] = soup2.select_one('#KOSDAQ_now').text.strip()
    except:
        indicators['KOSPI'] = None
        indicators['KOSDAQ'] = None

    return indicators


# API 응답: 종목 + 경제지표 종합
def stock_info_api(request):
    company_name = request.GET.get('name')
    if not company_name:
        return JsonResponse({'error': '기업명을 입력하세요'}, status=400)

    code = get_stock_code(company_name)
    if not code:
        return JsonResponse({'error': '종목코드를 찾을 수 없습니다'}, status=404)

    price, change, rate = get_stock_info(code)
    econ = get_economic_indicators()

    result = {
        '기업명': company_name,
        '종목코드': code,
        '현재가': price,
        '전일비': change,
        '등락률': rate,
        'USD/KRW': econ['USD/KRW'],
        '국내 금': econ['국내 금'],
        'KOSPI': econ['KOSPI'],
        'KOSDAQ': econ['KOSDAQ'],
    }

    return JsonResponse(result)


# 기업 개요 정보 크롤링
def crawl_company_info():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    url = "https://navercomp.wisereport.co.kr/v2/company/c1020001.aspx?cmp_cd=318160&cn="
    driver.get(url)
    time.sleep(2)

    try:
        address = driver.find_element(By.XPATH, '//*[@id="cTB201"]/tbody/tr[1]/td').text.strip()
        homepage = driver.find_element(By.XPATH, '//*[@id="cTB201"]/tbody/tr[2]/td[1]/a').get_attribute("href").strip()
        ceo = driver.find_element(By.XPATH, '//*[@id="cTB201"]/tbody/tr[3]/td[2]').text.strip()
        establishment_date = driver.find_element(By.XPATH, '//*[@id="cTB201"]/tbody/tr[3]/td[1]').text.strip()

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


# 기업 개요 detail.html 렌더링
def company_detail(request):
    company_info = crawl_company_info()
    return render(request, 'detail.html', {'company_info': company_info})
