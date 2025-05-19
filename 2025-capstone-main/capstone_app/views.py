from django.http import JsonResponse
import requests
from bs4 import BeautifulSoup

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
