import platform
import os
from bs4 import BeautifulSoup
import pyrosm
import geopandas as gpd

class osm_parser():

    def get_data(self):

        oper_s = platform.platform()
        if 'Windows' in oper_s:
            split_symbol = '\\'
        else:
            split_symbol = '/'

        current_dir = os.getcwd()
        # классический парсинг osm
        #self.dir_with_data = split_symbol.join(current_dir.split(split_symbol)[:-1]) + \
        #                split_symbol + 'data' + split_symbol + self.data_name


        #with open(self.dir_with_data, 'r', encoding='utf-8') as f:
        #    self.geo = f.read()

        # для парсинга через pyrosm файлов osm.pbf
        # Вставить файл RU-MOW.osm.pbf с рабочего стола в папку data!!
        self.dir_with_data = split_symbol.join(current_dir.split(split_symbol)[:-1]) + \
                        split_symbol + 'data' + split_symbol + self.geo_test_data_name
        print(self.dir_with_data)

        #print(self.geo[:50])

    def read_data(self):

        soup = BeautifulSoup(self.geo, 'xml')
        nodes = soup.find_all('node')
        print(nodes[0])


    data_name = 'map_test.osm'
    geo_test_data_name = 'RU-MOW.osm.pbf'
    dir_with_data = ''
    geo = ''

    def try_pyrosm(self):
        gdf = pyrosm.OSM(self.dir_with_data)
        print(type(gdf))
        boundaries = gdf.get_boundaries()
        boundaries.plot(facecolor="none", edgecolor="blue")
        #buildings = gdf.get_buildings()
        #buildings.plot()
        print(1)




osm = osm_parser()
osm.get_data()
#osm.read_data()
#osm.try_pyrosm()
