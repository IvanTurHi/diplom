import requests
from OSM_module import osm_parser
from random import choice
import time
import re
import pandas as pd

class population_module():

    def random_headers(self):
        return {'User-Agent': choice(self.desktop_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}

    #Получаем eoId из текста страницы, он находится в начале body в параметре data-eo-id
    def get_eoid(self, url):
        base_url = url
        #Некоторые Url Не имееют слеша, нужно добавить
        if url[-1] != '/':
            url += '/'

        url += 'info_add/classes'
        print(url)
        try:
            resp = self.session.get(url, headers=self.headers, timeout=3)
            #resp = self.session.get(url, headers=self.random_headers())
            text = resp.text
            position_start = text.find('data-eo-id')
            position_end = position_start + len('data-eo-id') + 10
            sub_s = text[position_start:position_end]
            eoId = sub_s.split('"')[1]
        except BaseException:
            print('FUUUUUUUUUUUUUUCK!')
            eoId = -1
            self.list_of_bad_urls.append(base_url)

        print(eoId)

        return eoId


    #Считаем количество студентов из ответа api
    def get_students_number(self, eoId):
        url = 'https://info-sites.mskobr.ru/api/ekis/classes.json?eoId=' + eoId
        resp = self.session.get(url, headers=self.headers)
        #resp = self.session.get(url, headers=self.random_headers())
        js_object = resp.json()
        data = js_object['data']
        primary_number = data['count_pupils_primary']
        secondary_number = data['count_pupils_secondary']
        common_number = data['count_pupils_common']

        return primary_number + secondary_number + common_number


    #Получаем количество студентов с сайта школы
    def parse_students(self):
        osm = osm_parser()
        osm.get_path()
        df_school = osm.read_data(osm.school_data_name_transform)

        #Если для очередной школы указан сайт, то получаем с ее сайта eoId и через api кидаем запрос,
        #где указываем этот eoID. Для тех у кого был сатй на mos ru Берем eoId От туда, иначе ищем на странице
        for i in range(df_school.shape[0]):
            if df_school.loc[i]['website'] != 'empty':
                if df_school.loc[i]['eoId'] == '0':
                    eoId = self.get_eoid(df_school.loc[i]['website'])
                else:
                    eoId = df_school.loc[i]['eoId']
                if eoId != -1:
                #print(eoId)
                    df_school.loc[i, 'students_number'] = self.get_students_number(eoId)
                time.sleep(1)

        print(self.list_of_bad_urls)
        with open(osm.data_path + 'bad_urls.txt', 'w') as f:
            for i in self.list_of_bad_urls:
                f.write(i + '\n')

        #записываем в файл
        osm.geo_write_data(df_school, osm.school_data_name_transform)

    #Ищем пересечения с нашим датасетом школ и датасетом с мос ру, где представлены данные по школам
    #и обогощаем наши данные информациео сайте и eoId
    #Подробно в папке additional_code ноутбук parse_students
    def get_website(self):
        #Загрузка данных
        osm = osm_parser()
        osm.get_path()
        df_mos = pd.read_excel(osm.data_path + self.xlsx_book)
        df_school = osm.read_data(osm.school_data_name_transform)

        #Вычленение номера школы из текста датасета с mos ru
        number_list = []
        for i in range(df_mos.shape[0]):
            num = ''.join(re.findall(r'\d', df_mos.loc[i]['ShortName']))
            if num == '':
                num = '0'
            number_list.append(num)
        df_mos['number'] = number_list

        #Вычленение сайте школы из текста датасета с mos ru
        web_list = []
        for i in range(df_mos.shape[0]):
            s = df_mos.loc[i]['InstitutionsAddresses']
            start = s.find('WebSite:')
            end = s.find('\nav')
            web_list.append(s[start + len('WebSite:'):end])
        df_mos['web'] = web_list

        #Вычленение номера школы в нашем датасете и создание колонки под eoId
        number_list = []
        list_eoId = []
        for i in range(df_school.shape[0]):
            num = ''.join(re.findall(r'\d', df_school.loc[i]['name']))
            list_eoId.append('0')
            if num == '':
                num = '0'
            if len(num) > 4:
                num = num[:4]
            number_list.append(num)
        df_school['number'] = number_list
        df_school['eoId'] = list_eoId

        #Обогощение данными с Mos ru
        for i in range(df_school.shape[0]):
            num = df_school.loc[i]['number']
            if num != '0':
                for j in range(df_mos.shape[0]):
                    if num == df_mos.loc[j]['number']:
                        df_school.loc[i, 'website'] = df_mos.loc[j]['web']
                        df_school.loc[i, 'eoId'] = df_mos.loc[j]['IDEKIS']

        osm.geo_write_data(df_school, osm.school_data_name_transform)


    def try_to_parse_data_mos(self):

        url = 'https://apidata.mos.ru/v1/datasets/2263/features?api_key=0d41eef2b32bf578f1dd43148c5ffed1'
        #url = 'https://apidata.mos.ru/v1/datasets/2263?api_key=0d41eef2b32bf578f1dd43148c5ffed1'
        response = requests.get(url)
        js_obj = response.json()
        osm = osm_parser()
        osm.get_path()
        osm.geo_write_data()



    api_key = '0d41eef2b32bf578f1dd43148c5ffed1'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; rv:14.0) Gecko/20100101 Firefox/14.0.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ru-ru,ru;q=0.8,en-us;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'DNT': '1'
    }
    desktop_agents = [
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14',
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0']
    session = requests.Session()
    list_of_bad_urls = []
    xlsx_book = 'data-54518-2023-03-14.xlsx'
    schools_mos_raw = 'schools_mos_row.geojson'


if __name__ == '__main__':
    pm = population_module()
    #pm.get_website()
    pm.parse_students()





