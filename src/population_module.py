import requests
from OSM_module import osm_parser
from random import choice, randint
import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import json
import geopandas as gpd


class population():

    def read_data_from_js(self, path):
        with open('buildings_area.json', 'r') as f:
            buildings_area_js = json.load(f)

        return buildings_area_js

    #Фунция для получения номера дома в нужном виде
    def get_house_number(self, address_line, str_addr):
        # Извлекаем адрес дома, делаем поиск по д.(он стоит перед номером дома) и выделяем номер дома
        house_addr = address_line.split(str_addr)[-1]
        house_addr = house_addr.split('д.')[1]
        # Если дом без корпуса (нет к), то просто берем номер
        if 'к' not in house_addr:
            house_addr = house_addr.split(' ')[-1]
        else:
            # Иначе же делим по букве к и отбираем с помощью регулярного выражения
            house_number = ''.join(re.findall(r'\d', house_addr.split('к')[0]))
            house_corpus = ''.join(re.findall(r'\d', house_addr.split('к')[1]))
            # Приводим номер дома к виду, который аналогичен виду в датаесте buildings_transform
            house_addr = house_number + ' к' + house_corpus

        return house_addr

    #Функция для преобразования сданий на цлице
    def street_transformation(self, buildings_area_js, street):
        buildings_area_js_df = gpd.GeoDataFrame(columns=['street', 'house', 'year', 'area'])
        for i in range(len(buildings_area_js)):
            if street in buildings_area_js[str(i + 1)]['address']:
                # buildings_area_js[str(i+1)]['address'].split(' ')[3]
                year = buildings_area_js[str(i + 1)]['year']
                area = buildings_area_js[str(i + 1)]['area']
                # Все разделено на проблеы, извлекаем улицу, отбрасываем последнюю запятую
                str_addr = buildings_area_js[str(i + 1)]['address'].split(' ')[3][:-1]
                house_addr = self.get_house_number(buildings_area_js[str(i + 1)]['address'], str_addr)
                buildings_area_js_df.loc[len(buildings_area_js_df.index)] = [str_addr, house_addr, year, area]
                #print(str_addr, house_addr, year, area)

        return buildings_area_js_df

    # Функция для добавления данных по площади и году к зданию
    # Поменять захардкоженные названия улиц на динамические и придумать как трансформировать улицы
    # Подробно в ноутбуке add_area_and_year_to_buildings в папке additional_code
    def add_data_to_buildings(self):

        osm = osm_parser()
        osm.get_path()
        df_buildings = osm.read_data(osm.building_data_name_transform)
        buildings_area_js = self.read_data_from_js(osm.data_path + self.buildings_area_data)

        #Выделение датасета с зданиями по одной улице
        sub_df = df_buildings[df_buildings['addr:street'].str.contains('1-я Владимирская улица')]
        sub_df['year'] = ''
        sub_df['area'] = ''

        #Датасет трансформированных адресов из вспомогательного датасета buildings_area
        buildings_area_js_df = self.street_transformation(buildings_area_js, '1-я Владимирская')

        # Добавляем данные по году и площади к зданиям
        for i in range(buildings_area_js_df.shape[0]):
            year = buildings_area_js_df.loc[i]['year']
            area = buildings_area_js_df.loc[i]['area']
            house = buildings_area_js_df.loc[i]['house']
            sub_df.loc[sub_df['addr:housenumber'] == house, 'year'] = year
            sub_df.loc[sub_df['addr:housenumber'] == house, 'area'] = area

        #Добавить запись основной датасет и сохранение в файл

    buildings_area_data = 'buildings_area.json'


class parser():

    #Функция для создаения ссылок на сатй реформы жкх
    #Ссылка выглядит так: https://www.reformagkh.ru/myhouse?tid=2281095&page=1&limit=60&view=list&sort=name&order=asc
    #В файле представлены данные в формате tid=xxxxxxx-y, y-количество странц
    #В самих ссылках все одинаковое, кроме tid и количества страниц
    def get_links(self, path):
        f = open(path, 'r')
        link_list = []
        for i in f:
            s = i[:-1]
            url_suf = s.split('-')[0]
            pages_number = int(s.split('-')[1])
            for j in range(pages_number):
                link = self.base_url + url_suf + self.url_page + str(j+1) + self.appendix_url
                link_list.append(link)

        return link_list

    def save_file(self, path, data):
        with open(path, 'a') as outfile:
            json.dump(data, outfile)

    #Функция для парсинга данных о жилплощади с сайта реформы жкх.
    def tyr_to_parse(self):
        osm = osm_parser()
        osm.get_path()
        #тут нюанс, если нужно будет докачать остатки данных, то вместо GKH_reforma_links используем GKH_reforma_links_short
        link_list = self.get_links(osm.data_path + self.likns_file)
        #link_list = self.get_links(osm.data_path + 'GKH_reforma_links_short.txt')
        print(len(link_list))
        #print(link_list)

        sur_id = 1
        #Вообще с 1 начинаем, тут просто костыль тк меня забанили и надо продолжить, а не заново,
        #забанили на tid=2281064, page=4
        #sur_id = 25906
        big_map = {}

        for i in link_list:

            print(i)
            self.browser.get(i)
            time.sleep(0.2)
            all_elements = self.browser.find_elements(By.XPATH, value='/html/body/section[5]/div/table/tbody/tr[*]')

            for j in range(len(all_elements)):
                try:
                    mini_map = {}
                    address = self.browser.find_element(By.XPATH, '//*[@id="myHouseList"]/tbody/tr[' + str(j+1)+ ']/td[2]/a').text
                    year = self.browser.find_element(By.XPATH, '/html/body/section[5]/div/table/tbody/tr[' + str(j+1) + ']/td[3]').text
                    area = self.browser.find_element(By.XPATH, '/html/body/section[5]/div/table/tbody/tr[' + str(j+1) + ']/td[4]').text
                    mini_map['address'] = address
                    mini_map['year'] = year
                    mini_map['area'] = area

                    big_map[sur_id] = mini_map
                    sur_id += 1
                except BaseException:
                    print('ERRRRROR', i)

                time.sleep(0.2)

            print(sur_id)

        self.browser.close()
        self.browser.quit()

        self.save_file(osm.data_path+self.buidings_area_file, big_map)

    likns_file = 'GKH_reforma_links.txt'
    buidings_area_file = 'buildings_area.json'
    base_url = 'https://www.reformagkh.ru/myhouse?'
    url_page = '&page='
    appendix_url = '&limit=60&view=list&sort=name&order=asc'
    browser = webdriver.Chrome()

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
    #pm = population_module()
    #pm.get_website()
    #pm.parse_students()
    pp = parser()
    pp.tyr_to_parse()
    #Я пошел пытаться совместить адреса с осм и адреса с реформы жкх. Пожелайте мне удачи





