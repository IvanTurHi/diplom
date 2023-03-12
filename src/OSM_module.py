import platform
import os
from bs4 import BeautifulSoup
import pyrosm
import requests
import h3
import geopandas as gpd
import geojson

class osm_parser():

    def get_path(self):

        oper_s = platform.platform()
        if 'Windows' in oper_s:
            split_symbol = '\\'
        else:
            split_symbol = '/'

        current_dir = os.getcwd()
        # классический парсинг osm
        self.data_path = split_symbol.join(current_dir.split(split_symbol)[:-1]) + \
                        split_symbol + 'data' + split_symbol


    def read_data(self, file_name):

        print(self.data_path + file_name)
        df = gpd.read_file(self.data_path + file_name)
        return df

    def geo_write_data(self, df, file_path):
        df.to_file(self.data_path + file_path, driver="GeoJSON")

    #Функция по преобразованию raw geojson с данными по школам. Ноутбук с детальным преобразованием
    #в папке additional_code -- data_filtering_schools_diploma
    def transform_school(self):
        df_school = self.read_data(self.school_data_name_raw)
        full_list_of_columns = df_school.columns.values.tolist()
        target_list_of_columns = ['id', 'addr:city', 'addr:full', 'addr:housenumber', 'addr:postcode', 'addr:street',
                                  'addr:place',
                                  'amenity', 'building', 'building:levels', 'name', 'type', 'short_name', 'old_name',
                                  'website',
                                  'contact:website', 'official_name', 'capacity', 'url', 'geometry']

        drop_list_of_columns = []
        for i in full_list_of_columns:
            if i not in target_list_of_columns:
                drop_list_of_columns.append(i)


        df_school.drop(drop_list_of_columns, axis=1, inplace=True)
        updated_list_of_columns = df_school.columns.values.tolist()

        # Заполняем пустые значение города Москвой
        df_school['addr:city'] = df_school['addr:city'].fillna('Москва')

        # Заполняем пустые значение посткода нулями
        df_school['addr:postcode'] = df_school['addr:postcode'].fillna('000000')

        # Заполняем поле amenity на school
        df_school['amenity'] = df_school['amenity'].fillna('school')

        # Заменяем поле building на school
        df_school['building'] = df_school['building'].fillna('school')
        df_school['building'].replace('yes', 'school', inplace=True)

        # Заполнение addr:street из addr:place
        df_school['addr:street'] = df_school['addr:street'].fillna('empty')
        df_school['addr:place'] = df_school['addr:place'].fillna('empty')
        for i in range(df_school.shape[0]):
            if df_school.iloc[i]['addr:street'] == 'empty' and df_school.iloc[i]['addr:place'] != 'empty':
                df_school.iloc[i]['addr:street'] = df_school.iloc[i]['addr:place']

        # Заполнение name из official_name	old_name	short_name
        df_school['name'] = df_school['name'].fillna('empty')
        df_school['official_name'] = df_school['official_name'].fillna('empty')
        df_school['old_name'] = df_school['old_name'].fillna('empty')
        df_school['short_name'] = df_school['short_name'].fillna('empty')
        for i in range(df_school.shape[0]):
            if df_school.iloc[i]['name'] == 'empty' and df_school.iloc[i]['official_name'] != 'empty':
                df_school.iloc[i]['name'] = df_school.iloc[i]['official_name']
            elif df_school.iloc[i]['name'] == 'empty' and df_school.iloc[i]['short_name'] != 'empty':
                df_school.iloc[i]['name'] = df_school.iloc[i]['short_name']
            elif df_school.iloc[i]['name'] == 'empty' and df_school.iloc[i]['old_name'] != 'empty':
                df_school.iloc[i]['name'] = df_school.iloc[i]['old_name']

        # Заполнение website из url contact:website
        df_school['website'] = df_school['website'].fillna('empty')
        df_school['url'] = df_school['url'].fillna('empty')
        df_school['contact:website'] = df_school['contact:website'].fillna('empty')
        for i in range(df_school.shape[0]):
            if df_school.iloc[i]['website'] == 'empty' and df_school.iloc[i]['url'] != 'empty':
                df_school.iloc[i]['website'] = df_school.iloc[i]['url']
            elif df_school.iloc[i]['website'] == 'empty' and df_school.iloc[i]['contact:website'] != 'empty':
                df_school.iloc[i]['website'] = df_school.iloc[i]['contact:website']

        # Удаление колонок, которые больше не пригодятся
        addititonal_dropping_columns = ['addr:full', 'addr:place', 'short_name', 'contact:website', 'url', 'old_name',
                                        'official_name']
        df_school.drop(addititonal_dropping_columns, axis=1, inplace=True)

        # Заполнение оставшихся пустых данных нулевыми значениями
        df_school['building:levels'] = df_school['building:levels'].fillna('0')
        df_school['capacity'] = df_school['capacity'].fillna('0')

        #Запись в файл
        self.geo_write_data(df_school, self.school_data_name_transform)





    data_name = 'map_test.osm'
    school_data_name_raw = 'schools_raw.geojson'
    school_data_name_transform = 'schools_transform.geojson'
    geo_test_data_name = 'RU-MOW.osm.pbf'
    data_path = ''
    geo = ''



osm = osm_parser()
osm.get_path()
osm.transform_school()






def try_parse_students():
    # открываем сайт школы -- например https://schv444.mskobr.ru/
    # Там переходим в раздел дполнительная информация -> классы -- https://schv444.mskobr.ru/info_add/classes
    # Там нам нужен файл classes.json?eoId, для каждой школы меняется только eoId
    # Пробуем его спиздить

    resp = requests.get('https://info-sites.mskobr.ru/api/ekis/classes.json?eoId=13935')
    #resp = requests.get('https://info-sites.mskobr.ru/api/ekis/classes.json?eoId=13264')
    print(resp.text)

#try_parse_students()