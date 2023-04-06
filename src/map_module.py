import folium
from OSM_module import osm_parser
import h3
import pandas as pd
import numpy as np
from shapely.geometry import Polygon
import geopandas as gpd
import json

class Map_master():

    #Загружаем датасет границ и выбираем нужные нам по id
    def get_districts(self, districts_list):
        self.osm.get_path()
        df_borders = self.osm.read_data(self.osm.borders_data_name_transform)
        df_target_borders = df_borders.loc[df_borders['district_id'].isin(districts_list)]

        return df_target_borders

    #Функция меняет долготу и широту местами
    def swap_points(self, points):
        for j in range(len(points)):
            points[j] = points[j][::-1]

        return points

    #функция для формирования линий границ районов
    def get_borders_in_right_oreder(self, df_target_borders):
        borders_map = {}
        #Если район целый и его тип Полигон, то все супер, просто меняем последовательность долготы и широты
        #На выходе словарь, где каждому району id соответствует список, содержаший список точек
        #Для полигонов там один список, для мультиполигонов несколько, это сделано чтоб все отображлось корректно
        #И не было линий от конца одной части района к началу другой
        for i in range(df_target_borders.shape[0]):
            if str(type(df_target_borders.iloc[i]['geometry'])).split("'")[1] == 'shapely.geometry.polygon.Polygon':
                points = list(df_target_borders.iloc[i]['geometry'].exterior.coords)
                borders_map[df_target_borders.iloc[i]['district_id']] = [self.swap_points(points)]
            #Если же район раздлене пространственно и его тип Мультиполигон, то мы добавляем его части по отдельности
            elif str(type(df_target_borders.iloc[i]['geometry'])).split("'")[1] == 'shapely.geometry.multipolygon.MultiPolygon':
                mycoordslist = [list(x.exterior.coords) for x in df_target_borders.iloc[i]['geometry'].geoms]
                for j in mycoordslist:
                    points = j
                    points = self.swap_points(points)
                    if df_target_borders.iloc[i]['district_id'] not in borders_map:
                        borders_map[df_target_borders.iloc[i]['district_id']] = [points]
                    else:
                        borders_map[df_target_borders.iloc[i]['district_id']] += [points]

            #geom = list(df_target_borders['geometry'])[0]
            #points = list(geom.exterior.coords)
            #for j in range(len(points)):
            #    points[j] = points[j][::-1]
            #borders_map[df_target_borders.loc[i]['district_id']] = points

        return borders_map

    #Функция по выводу границ районов. На вход получает список id районов
    def print_district_borders(self, maps, districts_list):
        df_target_borders = self.get_districts(districts_list)
        borders_map = self.get_borders_in_right_oreder(df_target_borders)

        color = 'red'
        #fill_color отвечает за заливку внутри полигона
        #fill_opacity отвечает за прозрачность заливки
        for i in borders_map:
            for j in borders_map[i]:
                folium.PolyLine(locations=j, color=color, fill_color="blue", fill_opacity=0.3).add_to(maps)

        return maps

    #Функция извлечения координат для полигоново и мультиполигонов в нужном формате
    def extract_borders(self, geom):
        geoJson = json.loads(gpd.GeoSeries(geom).to_json())
        geoJson = geoJson['features'][0]['geometry']
        if geoJson['type'] == 'Polygon':
            geoJson = {'type': 'Polygon', 'coordinates': [np.column_stack((np.array(geoJson['coordinates'][0])[:, 1],
                                                                           np.array(geoJson['coordinates'][0])[:,
                                                                           0])).tolist()]}
        elif geoJson['type'] == 'MultiPolygon':
            gjs = [[]]
            for i in range(len(geoJson['coordinates'])):
                gjs[0] += np.column_stack((np.array(geoJson['coordinates'][i][0])[:, 1],
                                           np.array(geoJson['coordinates'][i][0])[:, 0])).tolist()

            geoJson = {'type': 'Polygon', 'coordinates': gjs}

        return geoJson

    #Функция по отрисовке гексагонов внутри полигона, на вход карта, геометрия района и размер гексагона с его цветом
    def create_hexagons(self, maps, geom, hexagone_size, color):
        geoJson = self.extract_borders(geom)
        hexagons = list(h3.polyfill(geoJson, hexagone_size))
        polylines = []
        lat = []
        lng = []
        for hex in hexagons:
            polygons = h3.h3_set_to_multi_polygon([hex], geo_json=False)
            # flatten polygons into loops.
            outlines = [loop for polygon in polygons for loop in polygon]
            polyline = [outline + [outline[0]] for outline in outlines][0]
            lat.extend(map(lambda v: v[0], polyline))
            lng.extend(map(lambda v: v[1], polyline))
            polylines.append(polyline)
        for polyline in polylines:
            my_PolyLine = folium.PolyLine(locations=polyline, weight=3, color=color)
            maps.add_child(my_PolyLine)

        polylines_x = []
        for j in range(len(polylines)):
            a = np.column_stack((np.array(polylines[j])[:, 1], np.array(polylines[j])[:, 0])).tolist()
            polylines_x.append([(a[i][0], a[i][1]) for i in range(len(a))])

        polygons_hex = pd.Series(polylines_x).apply(lambda x: Polygon(x))

        return maps, polygons_hex, polylines


    def print_hexagones(self, maps, districts_list):
        df_target_borders = self.get_districts(districts_list)

        polygons_hex_list = []
        polylines_list = []
        #maps, polygons_hex, polylines = self.create_hexagons(maps, df_target_borders.iloc[0]['geometry'])
        for i in range(df_target_borders.shape[0]):
            maps, polygons_hex, polylines = self.create_hexagons(maps, df_target_borders.iloc[i]['geometry'],
                                                                 hexagone_size=9, color='green')
            polygons_hex_list.append(polygons_hex)
            polylines_list.append(polylines)

        return maps


    osm = osm_parser()