import folium
from OSM_module import osm_parser
import h3
import pandas as pd
import numpy as np
from shapely.geometry import Polygon
import geopandas as gpd
import json

class Map_master():

    #Загружаем датасет границ районов и выбираем нужные нам по id
    def get_districts(self, districts_list):
        self.osm.get_path()
        df_borders = self.osm.read_data(self.osm.borders_data_name_transform)
        df_target_borders = df_borders.loc[df_borders['district_id'].isin(districts_list)]

        return df_target_borders

    def get_regions(self, districts_list):
        self.osm.get_path()
        df_borders = self.osm.read_data(self.osm.regions_borders_data_name_transform)
        df_target_borders = df_borders.loc[df_borders['region_id'].isin(districts_list)]

        return df_target_borders

    #Функция меняет долготу и широту местами
    def swap_points(self, points):
        for j in range(len(points)):
            points[j] = points[j][::-1]

        return points

    #функция для формирования линий границ районов
    def get_borders_in_right_oreder(self, df_target_borders, id_type):
        borders_map = {}
        #Если район целый и его тип Полигон, то все супер, просто меняем последовательность долготы и широты
        #На выходе словарь, где каждому району id соответствует список, содержаший список точек
        #Для полигонов там один список, для мультиполигонов несколько, это сделано чтоб все отображлось корректно
        #И не было линий от конца одной части района к началу другой
        for i in range(df_target_borders.shape[0]):
            if str(type(df_target_borders.iloc[i]['geometry'])).split("'")[1] == 'shapely.geometry.polygon.Polygon':
                points = list(df_target_borders.iloc[i]['geometry'].exterior.coords)
                borders_map[df_target_borders.iloc[i][id_type]] = [self.swap_points(points)]
            #Если же район раздлене пространственно и его тип Мультиполигон, то мы добавляем его части по отдельности
            elif str(type(df_target_borders.iloc[i]['geometry'])).split("'")[1] == 'shapely.geometry.multipolygon.MultiPolygon':
                mycoordslist = [list(x.exterior.coords) for x in df_target_borders.iloc[i]['geometry'].geoms]
                for j in mycoordslist:
                    points = j
                    points = self.swap_points(points)
                    if df_target_borders.iloc[i][id_type] not in borders_map:
                        borders_map[df_target_borders.iloc[i][id_type]] = [points]
                    else:
                        borders_map[df_target_borders.iloc[i][id_type]] += [points]

        return borders_map

    #Функция по выводу границ районов. На вход получает список id районов
    def print_district_borders(self, maps, districts_list, type_t, feature_group_name):
        if type_t == 'district':
            df_target_borders = self.get_districts(districts_list)
            id_type = 'district_id'
            color = 'black'
        elif type_t == 'region':
            df_target_borders = self.get_regions(districts_list)
            id_type = 'region_id'
            color = 'red'

        borders_map = self.get_borders_in_right_oreder(df_target_borders, id_type=id_type)

        feature_group_borders = folium.FeatureGroup(feature_group_name)

        #fill_color отвечает за заливку внутри полигона
        #fill_opacity отвечает за прозрачность заливки
        for i in borders_map:
            for j in borders_map[i]:
                #folium.PolyLine(locations=j, color=color, fill_color="blue", fill_opacity=0.3).add_to(maps)
                folium.PolyLine(locations=j, color=color).add_to(feature_group_borders)

        feature_group_borders.add_to(maps)
        return maps

    #Функция извлечения координат для полигоново и мультиполигонов в нужном формате
    def extract_borders(self, geom):
        geoJson = json.loads(gpd.GeoSeries(geom).to_json())
        geoJson = geoJson['features'][0]['geometry']
        gjs = []
        if geoJson['type'] == 'Polygon':
            gjs.append([np.column_stack((np.array(geoJson['coordinates'][0])[:, 1],
                                         np.array(geoJson['coordinates'][0])[:,
                                         0])).tolist()])
            geoJson = {'type': 'Polygon', 'coordinates': gjs}
        elif geoJson['type'] == 'MultiPolygon':
            for i in range(len(geoJson['coordinates'])):
                gjs.append([np.column_stack((np.array(geoJson['coordinates'][i][0])[:, 1],
                                             np.array(geoJson['coordinates'][i][0])[:, 0])).tolist()])

            geoJson = {'type': 'Polygon', 'coordinates': gjs}

        return geoJson

    #Функция по отрисовке гексагонов внутри полигона, на вход карта, геометрия района и размер гексагона с его цветом
    def create_hexagons(self, maps, geom, hexagone_size, color, feature_group_hex):
        geoJson = self.extract_borders(geom)
        polylines_list = []
        polygons_hex_list = []
        for k in range(len(geoJson['coordinates'])):
            sub_geoJson = {'type': 'Polygon', 'coordinates': geoJson['coordinates'][k]}
            hexagons = list(h3.polyfill(sub_geoJson, hexagone_size))
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
                #my_PolyLine = folium.PolyLine(locations=polyline, weight=3, color=color).add_to(feature_group_hex)
                #maps.add_child(my_PolyLine)
                folium.PolyLine(locations=polyline, weight=3, color=color).add_to(feature_group_hex)
                feature_group_hex.add_to(maps)

            polylines_x = []
            for j in range(len(polylines)):
                a = np.column_stack((np.array(polylines[j])[:, 1], np.array(polylines[j])[:, 0])).tolist()
                polylines_x.append([(a[i][0], a[i][1]) for i in range(len(a))])

            polygons_hex = pd.Series(polylines_x).apply(lambda x: Polygon(x))

            polylines_list.append(polylines)
            polygons_hex_list.append(polygons_hex)

        return maps, polygons_hex_list, polylines_list, feature_group_hex

    #Функция для отрисовки гексагонов на карте в пределах выбранных районов
    def print_hexagones(self, maps, districts_list, type_t, feature_group_name):
        if type_t == 'district':
            df_target_borders = self.get_districts(districts_list)
            hexagone_size = 9
            color = 'blue'
        elif type_t == 'region':
            df_target_borders = self.get_regions(districts_list)
            hexagone_size = 8
            color = 'green'

        feature_group_hex = folium.FeatureGroup(feature_group_name)

        #maps, polygons_hex, polylines = self.create_hexagons(maps, df_target_borders.iloc[0]['geometry'])
        for i in range(df_target_borders.shape[0]):
            maps, polygons_hex, polylines, feature_group_hex = self.create_hexagons(maps, df_target_borders.iloc[i]['geometry'],
                                                             hexagone_size=hexagone_size,
                                                                 color=color, feature_group_hex=feature_group_hex)
            if type_t == 'district':
                self.big_polygons_hex_list_district.append(polygons_hex)
                self.big_polylines_list_district.append(polylines)
            elif type_t == 'region':
                self.big_polygons_hex_list_regions.append(polygons_hex)
                self.big_polylines_list_regions.append(polylines)

        #print('list_ken', len(self.big_polygons_hex_list_regions), len(self.big_polygons_hex_list_district))

        return maps

    #Функция для нанесения объектов на карту, которые ложатся внуть полигонов, поступающих на вход
    def print_objects(self, maps, df_objects, polygons_df, color, feature_group_name, marker, borders, circle):

        df_objects['centroid'] = df_objects.geometry.centroid
        objects_df = df_objects.set_geometry('centroid')
        df_inter = gpd.sjoin(objects_df, polygons_df)
        #print(len(df_inter))

        feature_group_object = folium.FeatureGroup(feature_group_name)

        for i in range(df_inter.shape[0]):
            #Добавление маркера объекта на карту
            location_latitude = df_inter.iloc[i]['centroid latitude']
            location_longitude = df_inter.iloc[i]['centroid longitude']
            if marker == True:
                folium.Marker(location=[location_latitude, location_longitude],
                          popup='<i>{}</i>'.format(df_inter.iloc[i]['short_name']),
                              tooltip='Click here', icon=folium.Icon(color=color)).add_to(feature_group_object)

            #Добавление границ объекта на карту
            if borders == True:
                points = [self.swap_points(list(df_inter.iloc[i]['geometry'].exterior.coords))]
                folium.PolyLine(locations=points, color=color, fill_color="blue", fill_opacity=0.3).add_to(feature_group_object)

            #Добавление кругов
            if circle == True:
                radius = 500
                circle_color = 'red'
                fill_color = 'blue'
                folium.Circle(location=[location_latitude, location_longitude], radius = radius,
                              color = circle_color, fill_color = fill_color).add_to(feature_group_object)

            if marker == False and borders == False and circle == False:
                pass

        feature_group_object.add_to(maps)

        return maps



    osm = osm_parser()
    #Их структура: в них хранятся районы/округа. По первому индексу можно получить соответственно один рейон или округ
    #Далее ддя каждого района/округа хрантся полигоны, если он является мультиполигоном, второй индекс отвечает за это
    #Далее хранятся уже сами гексагоны
    #Тут хранятся полигоны гексагонов по округам
    big_polygons_hex_list_regions = []
    big_polylines_list_regions = []
    #А тут хранятся полигоны гексагонов по районам
    big_polygons_hex_list_district = []
    big_polylines_list_district = []
