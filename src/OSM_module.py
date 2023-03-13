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

        #print(self.data_path + file_name)
        df = gpd.read_file(self.data_path + file_name)
        return df

    def geo_write_data(self, df, file_path):
        df.to_file(self.data_path + file_path, driver="GeoJSON")

    #Функция для вычисления центроида для объектов
    def calculate_centroid(self, df):
        centroid_list_longitude = []
        centroid_list_latitude = []
        for i in range(df.shape[0]):
            centroid_x = 0
            centroid_y = 0
            counter = 0
            if str(type(df.iloc[i]['geometry'])).split("'")[1] == 'shapely.geometry.polygon.Polygon':
                longitude, latitude = df.iloc[i]['geometry'].exterior.coords.xy
                for j in range(len(longitude)):
                    counter += 1
                    centroid_x += longitude[j]
                    centroid_y += latitude[j]
                centroid_x = centroid_x / counter
                centroid_y = centroid_y / counter

            elif str(type(df.iloc[i]['geometry'])).split("'")[1] == 'shapely.geometry.point.Point':
                centroid_x = list(df.iloc[-1]['geometry'].coords)[0][0]
                centroid_y = list(df.iloc[-1]['geometry'].coords)[0][1]

            elif str(type(df.iloc[i]['geometry'])).split("'")[1] == 'shapely.geometry.multipolygon.MultiPolygon':
                mycoordslist = [list(x.exterior.coords) for x in df.iloc[i]['geometry'].geoms]
                for j in mycoordslist:
                    for k in range(len(j)):
                        counter += 1
                        centroid_x += j[k][0]
                        centroid_y += j[k][1]
                centroid_x = centroid_x / counter
                centroid_y = centroid_y / counter

            elif str(type(df.iloc[i]['geometry'])).split("'")[1] == 'shapely.geometry.linestring.LineString':
                longitude, latitude = df.iloc[i]['geometry'].coords.xy
                for j in range(len(longitude)):
                    counter += 1
                    centroid_x += longitude[j]
                    centroid_y += latitude[j]
                centroid_x = centroid_x / counter
                centroid_y = centroid_y / counter

            centroid_list_longitude.append(centroid_x)
            centroid_list_latitude.append(centroid_y)

        return centroid_list_longitude, centroid_list_latitude

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

        # Добавление данных о количестве студентов
        df_school['students_number'] = ""
        df_school['students_number'] = df_school['students_number'].replace('', '0')

        #Добавление центроидов
        df_school['centroid longitude'], df_school['centroid latitude'] = self.calculate_centroid(df_school)

        #Запись в файл
        self.geo_write_data(df_school, self.school_data_name_transform)

    # Функция по преобразованию raw geojson с данными по детским садам. Ноутбук с детальным преобразованием
    # в папке additional_code -- data_filtering_kindergarten_diploma
    def transform_kindergarten(self):

        df_kindergarten = self.read_data(self.kindergarten_data_name_raw)

        full_list_of_columns = df_kindergarten.columns.values.tolist()
        target_list_of_columns = ['id', 'addr:city', 'addr:full', 'addr:housenumber', 'addr:postcode', 'addr:street',
                                  'addr:place',
                                  'amenity', 'building', 'building:levels', 'name', 'type', 'short_name', 'old_name',
                                  'website',
                                  'contact:website', 'official_name', 'capacity', 'geometry']

        #Определяем столбцы, которые надо удалить
        drop_list_of_columns = []
        for i in full_list_of_columns:
            if i not in target_list_of_columns:
                drop_list_of_columns.append(i)

        df_kindergarten.drop(drop_list_of_columns, axis=1, inplace=True)
        updated_list_of_columns = df_kindergarten.columns.values.tolist()

        # Заполняем пустые значение города Москвой
        df_kindergarten['addr:city'] = df_kindergarten['addr:city'].fillna('Москва')

        # Заполняем пустые значение посткода нулями
        df_kindergarten['addr:postcode'] = df_kindergarten['addr:postcode'].fillna('000000')

        # Заполняем поле amenity на kindergarten
        df_kindergarten['amenity'] = df_kindergarten['amenity'].fillna('kindergarten')

        # Заменяем поле building на kindergarten
        df_kindergarten['building'] = df_kindergarten['building'].fillna('kindergarten')
        df_kindergarten['building'].replace('yes', 'kindergarten', inplace=True)

        # Заполнение addr:street из addr:place
        df_kindergarten['addr:street'] = df_kindergarten['addr:street'].fillna('empty')
        df_kindergarten['addr:place'] = df_kindergarten['addr:place'].fillna('empty')
        for i in range(df_kindergarten.shape[0]):
            if df_kindergarten.iloc[i]['addr:street'] == 'empty' and df_kindergarten.iloc[i]['addr:place'] != 'empty':
                df_kindergarten.iloc[i]['addr:street'] = df_kindergarten.iloc[i]['addr:place']

        # Заполнение name из official_name	old_name	short_name
        df_kindergarten['name'] = df_kindergarten['name'].fillna('empty')
        df_kindergarten['official_name'] = df_kindergarten['official_name'].fillna('empty')
        df_kindergarten['old_name'] = df_kindergarten['old_name'].fillna('empty')
        df_kindergarten['short_name'] = df_kindergarten['short_name'].fillna('empty')
        for i in range(df_kindergarten.shape[0]):
            if df_kindergarten.iloc[i]['name'] == 'empty' and df_kindergarten.iloc[i]['official_name'] != 'empty':
                df_kindergarten.iloc[i]['name'] = df_kindergarten.iloc[i]['official_name']
            elif df_kindergarten.iloc[i]['name'] == 'empty' and df_kindergarten.iloc[i]['short_name'] != 'empty':
                df_kindergarten.iloc[i]['name'] = df_kindergarten.iloc[i]['short_name']
            elif df_kindergarten.iloc[i]['name'] == 'empty' and df_kindergarten.iloc[i]['old_name'] != 'empty':
                df_kindergarten.iloc[i]['name'] = df_kindergarten.iloc[i]['old_name']

        # Заполнение website из url contact:website
        df_kindergarten['website'] = df_kindergarten['website'].fillna('empty')
        df_kindergarten['contact:website'] = df_kindergarten['contact:website'].fillna('empty')
        for i in range(df_kindergarten.shape[0]):
            if df_kindergarten.iloc[i]['website'] == 'empty' and df_kindergarten.iloc[i]['contact:website'] != 'empty':
                df_kindergarten.iloc[i]['website'] = df_kindergarten.iloc[i]['contact:website']

        # Удаление колонок, которые больше не пригодятся
        addititonal_dropping_columns = ['addr:full', 'addr:place', 'short_name', 'contact:website', 'old_name',
                                        'official_name']
        df_kindergarten.drop(addititonal_dropping_columns, axis=1, inplace=True)

        # Заполнение оставшихся пустых данных нулевыми значениями
        df_kindergarten['building:levels'] = df_kindergarten['building:levels'].fillna('0')
        df_kindergarten['capacity'] = df_kindergarten['capacity'].fillna('0')

        # Добавление данных о количестве студентов
        df_kindergarten['students_number'] = ""
        df_kindergarten['students_number'] = df_kindergarten['students_number'].replace('', '0')

        # Добавление центроидов
        df_kindergarten['centroid longitude'], df_kindergarten['centroid latitude'] = self.calculate_centroid(df_kindergarten)

        # Запись в файл
        self.geo_write_data(df_kindergarten, self.kindergarten_data_name_transform)

    # Функция по преобразованию raw geojson с данными по мед учереждениям. Ноутбук с детальным преобразованием
    # в папке additional_code -- data_filtering_medicine_diploma
    def deftransform_medicine(self):

        df_medicine = self.read_data(self.medicine_data_name_raw)
        full_list_of_columns = df_medicine.columns.values.tolist()
        target_list_of_columns = ['id', 'addr:city', 'addr:full', 'addr:housenumber', 'addr:postcode', 'addr:street',
                                  'addr:place',
                                  'amenity', 'building', 'building:levels', 'name', 'type', 'short_name', 'old_name',
                                  'website',
                                  'contact:website', 'official_name', 'url', 'geometry']

        drop_list_of_columns = []
        for i in full_list_of_columns:
            if i not in target_list_of_columns:
                drop_list_of_columns.append(i)

        df_medicine.drop(drop_list_of_columns, axis=1, inplace=True)
        updated_list_of_columns = df_medicine.columns.values.tolist()

        # Заполняем пустые значение города Москвой
        df_medicine['addr:city'] = df_medicine['addr:city'].fillna('Москва')

        # Заполняем пустые значение посткода нулями
        df_medicine['addr:postcode'] = df_medicine['addr:postcode'].fillna('000000')

        # Заменяем поле building на medicine
        df_medicine['building'] = df_medicine['building'].fillna('medicine')
        df_medicine['building'].replace('yes', 'medicine', inplace=True)
        df_medicine['building'].replace('clinic', 'medicine', inplace=True)
        df_medicine['building'].replace('doctors', 'medicine', inplace=True)
        df_medicine['building'].replace('hospital', 'medicine', inplace=True)

        # Заполнение addr:street из addr:place
        df_medicine['addr:street'] = df_medicine['addr:street'].fillna('empty')
        df_medicine['addr:place'] = df_medicine['addr:place'].fillna('empty')
        for i in range(df_medicine.shape[0]):
            if df_medicine.iloc[i]['addr:street'] == 'empty' and df_medicine.iloc[i]['addr:place'] != 'empty':
                df_medicine.iloc[i]['addr:street'] = df_medicine.iloc[i]['addr:place']

        # Заполнение name из official_name	old_name	short_name
        df_medicine['name'] = df_medicine['name'].fillna('empty')
        df_medicine['official_name'] = df_medicine['official_name'].fillna('empty')
        df_medicine['old_name'] = df_medicine['old_name'].fillna('empty')
        df_medicine['short_name'] = df_medicine['short_name'].fillna('empty')
        for i in range(df_medicine.shape[0]):
            if df_medicine.iloc[i]['name'] == 'empty' and df_medicine.iloc[i]['official_name'] != 'empty':
                df_medicine.iloc[i]['name'] = df_medicine.iloc[i]['official_name']
            elif df_medicine.iloc[i]['name'] == 'empty' and df_medicine.iloc[i]['short_name'] != 'empty':
                df_medicine.iloc[i]['name'] = df_medicine.iloc[i]['short_name']
            elif df_medicine.iloc[i]['name'] == 'empty' and df_medicine.iloc[i]['old_name'] != 'empty':
                df_medicine.iloc[i]['name'] = df_medicine.iloc[i]['old_name']

        # Заполнение website из url contact:website
        df_medicine['website'] = df_medicine['website'].fillna('empty')
        df_medicine['url'] = df_medicine['url'].fillna('empty')
        df_medicine['contact:website'] = df_medicine['contact:website'].fillna('empty')
        for i in range(df_medicine.shape[0]):
            if df_medicine.iloc[i]['website'] == 'empty' and df_medicine.iloc[i]['url'] != 'empty':
                df_medicine.iloc[i]['website'] = df_medicine.iloc[i]['url']
            elif df_medicine.iloc[i]['website'] == 'empty' and df_medicine.iloc[i]['contact:website'] != 'empty':
                df_medicine.iloc[i]['website'] = df_medicine.iloc[i]['contact:website']

        # Удаление колонок, которые больше не пригодятся
        addititonal_dropping_columns = ['addr:full', 'addr:place', 'short_name', 'contact:website', 'old_name',
                                        'official_name']
        df_medicine.drop(addititonal_dropping_columns, axis=1, inplace=True)

        # Заполнение оставшихся пустых данных нулевыми значениями
        df_medicine['building:levels'] = df_medicine['building:levels'].fillna('0')

        # Добавление центроидов
        df_medicine['centroid longitude'], df_medicine['centroid latitude'] = self.calculate_centroid(df_medicine)

        # Запись в файл
        self.geo_write_data(df_medicine, self.medicine_data_name_transform)




    data_name = 'map_test.osm'
    school_data_name_raw = 'schools_raw.geojson'
    school_data_name_transform = 'schools_transform.geojson'
    kindergarten_data_name_raw = 'kindergartens_raw.geojson'
    kindergarten_data_name_transform = 'kindergartens_transform.geojson'
    medicine_data_name_raw = 'medicine_raw.geojson'
    medicine_data_name_transform = 'medicine_transform.geojson'
    geo_test_data_name = 'RU-MOW.osm.pbf'
    data_path = ''
    geo = ''



osm = osm_parser()
osm.get_path()
#osm.transform_school()
#osm.transform_kindergarten()
osm.deftransform_medicine()






def try_parse_students():
    # открываем сайт школы -- например https://schv444.mskobr.ru/
    # Там переходим в раздел дполнительная информация -> классы -- https://schv444.mskobr.ru/info_add/classes
    # Там нам нужен файл classes.json?eoId, для каждой школы меняется только eoId
    # Пробуем его спиздить

    resp = requests.get('https://info-sites.mskobr.ru/api/ekis/classes.json?eoId=13935')
    #resp = requests.get('https://info-sites.mskobr.ru/api/ekis/classes.json?eoId=13264')
    print(resp.text)

#try_parse_students()