# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import urllib.request
from urllib.parse import quote
import json
import re
import requests, time
import pandas as pd

#네이버 검색 Open API 사용 요청시 얻게되는 정보를 입력합니다
naver_client_id = "wXxPslZJGJrplu5FPfKk"
naver_client_secret = "4kkKrmJzRF"

def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def searchByTitle(title):
    myurl = 'https://openapi.naver.com/v1/search/movie.json?display=100&yearfrom=1960&yearto=2017&query=' + quote(title)
    request = urllib.request.Request(myurl)
    request.add_header("X-Naver-Client-Id",naver_client_id)
    request.add_header("X-Naver-Client-Secret",naver_client_secret)
    response = urllib.request.urlopen(request)
    rescode = response.getcode()
    if(rescode==200):
        response_body = response.read()
        d = json.loads(response_body.decode('utf-8'))
        if (len(d['items']) > 0):
            return d['items']
        else:
            return None

    else:
        print("Error Code:" + rescode)

def findItemByInput(items, meta,year,title):
    total_len = len(items)
    compare = []
    for index, item in enumerate(items):
        if index > 10: return []

        navertitle = cleanhtml(item['title'])
        naversubtitle = cleanhtml(item['subtitle'])
        naverpubdate = cleanhtml(item['pubDate'])
        naveractor = cleanhtml(item['actor'])
        naverlink = cleanhtml(item['link'])
        naveruserScore = cleanhtml(item['userRating'])
        naverDirector = cleanhtml(item['director'])

        naveractor = ",".join(naveractor.split("|")[:-1])
        naverDirector = ",".join(naverDirector.split("|")[:-1])


        navertitle1 = navertitle.replace(" ","")
        navertitle1 = navertitle1.replace("-", ",")
        navertitle1 = navertitle1.replace(":", ",")

        #기자 평론가 평점을 얻어 옵니다
        # spScore = getSpecialScore(naverlink)

        #네이버가 다루는 영화 고유 ID를 얻어 옵니다다
        naverid = re.split("code=", naverlink)[1]

        review_html = get_soup("https://movie.naver.com/movie/bi/mi/point.nhn?code="+naverid)
        # content > div.article > div.mv_info_area > div.mv_info > dl > dd:nth-child(2) > p > span:nth-child(3)
        try:
            movie_step1 = review_html.find("div",{'id':"content"}).find('div',{'class':'article'}).\
            find('div',{'class':'mv_info_area'}).find('div',{'class':'mv_info'}).find('dl',{'class':'info_spec'}).\
            find('dd').find('p').find_all("span")
            movie_length = None

            for i in movie_step1:
                if '분' in i.text:
                    movie_length = int(i.text.replace('분', ''))
                    break
        except:
            movie_length = None
        # print(naverid)


        # netizen_point_tab_inner > span > em
        try:
            rating_count = review_html.find('div',{'id':"netizen_point_tab_inner"}).find('span',{'class':'user_count'}).find('em').text
            rating_count = int(rating_count.replace(",",""))

        except AttributeError: rating_count = 0

        title = str(title.split(":")[0])
        title = str(title.split("-")[0])
        title = title.replace(" ","")

        _navertitle = clean(navertitle)[0]
        _navertitle = str(_navertitle.split(":")[0])
        _navertitle = str(_navertitle.split("-")[0])
        _navertitle = _navertitle.replace(" ","")

        if year != 0 and year == int(naverpubdate) and title == _navertitle:
            print(year,naverpubdate)
            compare.append([naverid, navertitle, naversubtitle, naverpubdate, naveractor, naveruserScore, naverDirector, movie_length,
             rating_count])
            return compare[-1]

        # elif year != 0 and year == int(naverpubdate):
        #     compare.append([naverid, navertitle, naversubtitle, naverpubdate, naveractor, naveruserScore, naverDirector,
        #                     movie_length,
        #                     rating_count])
        #     return compare[-1]


        elif year == 0 and title == _navertitle:
            compare.append([naverid, navertitle, naversubtitle, naverpubdate, naveractor, naveruserScore, naverDirector,
                            movie_length,
                            rating_count])
            continue


        # if str(title).replace(" ","") == str(navertitle).replace(" ",""):
        #     if (naverpubdate != "" and int(naverpubdate) == year) or index+1==total_len:
        #         print(navertitle, meta, naverDirector, naverpubdate, year)
                # compare.append([naverid, navertitle, naversubtitle, naverpubdate, naveractor, naveruserScore, naverDirector,movie_length,rating_count])
                # break

        # 영화의 타이틀 이미지를 표시합니다
        # if (item['image'] != None and "http" in item['image']):
        #    response = requests.get(item['image'])
        #    img = Image.open(BytesIO(response.content))
        #    img.show()

    if len(compare) > 0:
        # print(compare)
        compare = pd.DataFrame(compare)
        print(compare)
        compare = compare.sort_values(by=8,ascending=False)
        compare = compare.values.tolist()
        # print(compare)
        return compare[0]



    return compare

def getInfoFromNaver(searchTitle,meta,year,title):
    items = searchByTitle(searchTitle)
    if (items != None):
        return findItemByInput(items,meta,year,title)
    else:
        return []

def get_soup(url):
    source_code = requests.get(url)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text, 'lxml')
    return soup

#기자 평론가 평점을 얻어 옵니다
# def getSpecialScore(URL):
#     soup = get_soup(URL)
#     scorearea = soup.find_all('div', "spc_score_area")
#     newsoup = BeautifulSoup(str(scorearea), 'lxml')
#     score = newsoup.find_all('em')
#     if (score and len(score) > 5):
#         scoreis = score[1].text + score[2].text + score[3].text + score[4].text
#         return float(scoreis)
#     else:
#         return 0.0

def clean(text):
    y = str(text).find("(")
    year = 0
    if y != -1:
        year = str(text)[y+1:y+5]
        try:
            year = int(year)
        except ValueError:
            year = 0
        print(year)
    # year = y.findall(str(text))
    p = re.compile('\[.*?\]|\(.*?\)')
    cleantext = p.sub("",str(text))

    if year != 0:
        return cleantext, int(year)
    else: return cleantext, 0

movie_data = pd.read_excel("C:\\Users\msi\Desktop\Soohyun\CHALLENGERS\TBCC\Final_DATA\TBC_MOVIES_TITLE.xlsx")

output = []
for movie in movie_data.values[:]:
    mid = int(movie[0])
    print(mid)
    title = movie[1]
    title, year = clean(title)
    meta = title
    # print(meta)
    ret = getInfoFromNaver(u"%s"%title,meta,year,title)
    if len(ret) > 0:
        ret = [mid] + ret
        output.append(ret)
        print(ret)
    time.sleep(0.1)

df = pd.DataFrame(output)
# print(df)
df.to_excel("Second_round.xlsx",index_label=False)
# getInfoFromNaver(u"007 제1탄-살인번호")