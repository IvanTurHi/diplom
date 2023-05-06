import folium
from OSM_module import osm_parser
import h3
import pandas as pd
import numpy as np
from shapely.geometry import Polygon
import geopandas as gpd
import json
import branca
from shapely.geometry import Point

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
        if len(districts_list) > 0:
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

            #feature_group_borders.add_to(maps)
        return feature_group_borders

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
                #feature_group_hex.add_to(maps)

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

        return feature_group_hex

    def intersction(self, df_objects, polygons_df):
        df_objects['centroid'] = df_objects.geometry.centroid
        polygons_df['polygon'] = polygons_df.geometry
        objects_df = df_objects.set_geometry('centroid')

        return gpd.sjoin(objects_df, polygons_df)

    #Функция для визуализации тех объектов, у которых тип указан точкой
    def visualize_hexagons_for_point_object(self, hexagons):

        polylines = []
        lat = []
        lng = []
        for hex in hexagons:
            polygons = h3.h3_set_to_multi_polygon([hex], geo_json=False)
            outlines = [loop for polygon in polygons for loop in polygon]
            polyline = [outline + [outline[0]] for outline in outlines][0]
            lat.extend(map(lambda v: v[0], polyline))
            lng.extend(map(lambda v: v[1], polyline))
            polylines += polyline

        return polylines

    def get_table_row(self, left_column_value, right_column_value, left_col_color, right_col_color):
        table_row = """
        <tr>
        <td style="background-color: """ + left_col_color + """;"><big>""" + left_column_value + """</big></span></td>
        <td style="background-color: """ + right_col_color + """;"><big>{}</big></td>""".format(
            right_column_value) + """
        </tr>
        """

        return table_row

    def get_buffer_text(self, header, left_col_color, right_col_color, fields_map):
        static_text = """
                    <!DOCTYPE html>
                    <html>
        <head>
        <h4 style="margin-bottom:10"; width="200px">{}</h4>""".format(header) + """
          <style type="text/css">
   TABLE {
    width: 300px; /* Ширина таблицы */
    border-collapse: collapse; /* Убираем двойные линии между ячейками */
   }
   TD, TH {
    padding: 3px; /* Поля вокруг содержимого таблицы */
    border: 1px solid black; /* Параметры рамки */
   }
   TH {
    background: #b0e0e6; /* Цвет фона */
   }
  </style>
        </head>
        <table style="height: 150px; width: 300px; border: 8px">
        <tbody> """
        left_col_color_second = "#19a7bd"
        right_col_color_second = "#f2f0d3"
        right_col_color = "#FFD700"
        row_counter = 0
        for i in fields_map:
            if row_counter % 2 == 0:
                static_text += self.get_table_row(i, fields_map[i], right_col_color, right_col_color)
            else:
                static_text += self.get_table_row(i, fields_map[i], right_col_color_second, right_col_color_second)
            row_counter += 1

        static_text += """
        </tbody>
        </table>
        </html>
        """

        return static_text


    def add_marker(self, location_latitude, location_longitude, object, color, feature_group_object, feature_group_name, total_buildings_number, kinder_number, students_number, adults_number):
        if feature_group_name == 'schools':
            #static_text = """
            #<i>Количество жилых зданий в радиусе доступности: {} <Br> Количество детей школьного возраста, проживающих в радиусе доступности: {}
            #<Br> Общее количество человек, проживающих в радиусе доступности: {} <Br></i>
            #""".format(total_buildings_number, students_number, kinder_number + students_number + adults_number)
            left_col_color = "#00008b"
            right_col_color = "#ffff00"
            header = list(object['short_name'])[0]
            total_buildings_number_text = 'Количество жилых зданий в радиусе доступности'
            total_buildings_number = total_buildings_number
            children_text = 'Количество детей школьного возраста, проживающих в радиусе доступности'
            children_number = students_number
            total_number_text = 'Общее количество человек, проживающих в радиусе доступности'
            total_number = kinder_number + students_number + adults_number

            fields_map = {}
            fields_map[total_buildings_number_text] = total_buildings_number
            fields_map[children_text] = children_number
            fields_map[total_number_text] = total_number

            static_text = self.get_buffer_text(header, left_col_color, right_col_color, fields_map)
            tooltip_text = '<i>{}</i>'.format(list(object['short_name'])[0])
            folium.Marker(location=[location_latitude, location_longitude],
                          popup=folium.Popup(folium.Html(static_text, script=True), parse_html=True),
                          tooltip=folium.Tooltip(tooltip_text), icon=folium.Icon(color=color)).add_to(feature_group_object)

        if feature_group_name == 'kindergartens':
            left_col_color = "#00008b"
            right_col_color = "#ffff00"
            header = 'Детский сад при школе ' + list(object['short_name'])[0]
            total_buildings_number_text = 'Количество жилых зданий в радиусе доступности'
            total_buildings_number = total_buildings_number
            children_text = 'Количество детей детсадовского возраста, проживающих в радиусе доступности'
            children_number = kinder_number
            total_number_text = 'Общее количество человек, проживающих в радиусе доступности'
            total_number = kinder_number + students_number + adults_number

            fields_map = {}
            fields_map[total_buildings_number_text] = total_buildings_number
            fields_map[children_text] = children_number
            fields_map[total_number_text] = total_number

            static_text = self.get_buffer_text(header, left_col_color, right_col_color, fields_map)

            tooltip_text = '<i>{}</i>'.format(list(object['short_name'])[0])
            folium.Marker(location=[location_latitude, location_longitude],
                          popup=folium.Popup(folium.Html(static_text, script=True), parse_html=True),
                          tooltip=folium.Tooltip(tooltip_text), icon=folium.Icon(color=color)).add_to(feature_group_object)

        if feature_group_name == 'medicine':
            left_col_color = "#00008b"
            right_col_color = "#ffff00"
            header = 'Медицинское учреждение'
            total_buildings_number_text = 'Количество жилых зданий в радиусе доступности'
            total_buildings_number = total_buildings_number
            total_number_text = 'Общее количество человек, проживающих в радиусе доступности'
            total_number = kinder_number + students_number + adults_number

            fields_map = {}
            fields_map[total_buildings_number_text] = total_buildings_number
            fields_map[total_number_text] = total_number

            static_text = self.get_buffer_text(header, left_col_color, right_col_color, fields_map)

            tooltip_text = 'Медицинское учреждение'
            folium.Marker(location=[location_latitude, location_longitude],
                          popup=folium.Popup(folium.Html(static_text, script=True), parse_html=True),
                          tooltip=folium.Tooltip(tooltip_text), icon=folium.Icon(color=color)).add_to(feature_group_object)

    def add_object_borders(self, maps, object, color, fillcolor, fillopacity, feature_group_object, feature_group_name, mf_group):
        skip_flag = False
        if str(type(object['geometry'])).split("'")[1] == 'shapely.geometry.polygon.Polygon':
            points = [self.swap_points(list(object['geometry'].exterior.coords))]

        elif str(type(object['geometry'])).split("'")[1] == 'shapely.geometry.point.Point':
            h3_address = h3.geo_to_h3(object['centroid latitude'], object['centroid longitude'],  12)
            points = self.visualize_hexagons_for_point_object([h3_address])

        elif str(type(object['geometry'])).split("'")[1] == 'shapely.geometry.multipolygon.MultiPolygon':
            mycoordslist = [list(x.exterior.coords) for x in object['geometry'].geoms]
            mycoordslist_unzip = []
            for j in mycoordslist:
                mycoordslist_unzip += j
            points = [self.swap_points(mycoordslist_unzip)]

        elif str(type(object['geometry'])).split("'")[1] == 'shapely.geometry.linestring.LineString':
            h3_address = h3.geo_to_h3(object['centroid latitude'], object['centroid longitude'], 12)
            points = self.visualize_hexagons_for_point_object([h3_address])

        if feature_group_name == 'school':
            if object['workload'] < 100:
                fillcolor = 'green'
            elif object['workload'] < 200:
                fillcolor = 'yellow'
            elif object['workload'] >= 200:
                fillcolor = 'red'
            else:
                fillcolor = 'blue'
            html_text = """
            <li><a href="/map{}_{}" target=_parent><big><big>Построить радиус доступности</big></big></a></li>
            <li><a href="/data_update{}_{}" target=_parent><big><big>Редактировать данные</big></big></a></li>
            """.format('s', object['id'], 's', object['id'])
            #static_text = """
            #<i>Школа: {} <Br> Загруженность (в процентах от номинальной): {} <Br> Рейтинг: {}
            #<Br></i> <li><a href="https://{}" target=_blank>Сайт школы <br> </a></li>
            #""".format(object['short_name'], object['workload'], object['rating'], object['website'])

            name_text = 'Школа'
            students_number_text = 'Количество учеников'
            capacity_text = 'Номинальная вместимость'
            workload_text = 'Загруженность (в процентах от номинальной)'
            rating_text = 'Рейтинг'
            website_text = 'Сайт школы'
            header = object['short_name']
            left_col_color = "#00008b"
            right_col_color = "#ffff00"

            fields_map = {}
            fields_map[name_text] = object['short_name']
            fields_map[students_number_text] = object['students']
            fields_map[capacity_text] = object['capacity']
            fields_map[workload_text] = object['workload']
            fields_map[rating_text] = object['rating']
            fields_map[website_text] = '<a href="https://{}" target=_blank>{}<br> </a>'.format(object['website'], object['website'])

            if fields_map[rating_text] == '' or object['rating'] == 'nan':
                fields_map[rating_text] = 'Нет данных'

            static_text = self.get_buffer_text(header, left_col_color, right_col_color, fields_map)

            folium.PolyLine(locations=points, color=color, fill_color=fillcolor, fill_opacity=fillopacity,
                            popup=folium.Popup(static_text + html_text),
                            tooltip='<i>{}</i>'.format(object['short_name'])).add_to(feature_group_object)

        if feature_group_name == 'kindergartens':
            #static_text = """
            #<i>Детский сад при школе: {} <Br>  Рейтинг: {}
            #<Br></i> <li><a href="https://{}" target=_blank>Сайт детского сада<br> </a></li>
            #""".format(object['short_name'],  object['rating'], object['website'])

            name_text = 'Детский сад при школе'
            capacity_text = 'Расчетная вместимость(чел)'
            rating_text = 'Рейтинг'
            website_text = 'Сайт школы'
            header = 'Детский сад при школе ' + object['short_name']
            left_col_color = "#00008b"
            right_col_color = "#ffff00"

            fields_map = {}
            fields_map[name_text] = object['short_name']
            fields_map[capacity_text] = object['capacity']
            fields_map[rating_text] = object['rating']
            fields_map[website_text] = '<a href="https://{}" target=_blank>{}<br> </a>'.format(object['website'], object['website'])

            if fields_map[rating_text] == '' or object['rating'] == 'nan':
                fields_map[rating_text] = 'Нет данных'

            static_text = self.get_buffer_text(header, left_col_color, right_col_color, fields_map)

            html_text = """
            <li><a href="/map{}_{}" target=_parent><big><big>Построить радиус доступности</big></big></a></li>
            <li><a href="/data_update{}_{}" target=_parent><big><big>Редактировать данные</big></big></a></li>
              """.format('k', object['id'], 'k', object['id'])
            folium.PolyLine(locations=points, color=color, fill_color=fillcolor, fill_opacity=fillopacity,
                            popup=folium.Popup(static_text + html_text),
                            tooltip='<i>Детский сад при школе {}</i>'.format(object['short_name'])).add_to(feature_group_object)

        if feature_group_name == 'buildings':
            #Раскарска зданий в зависимости от года постройки, в try-except что не трогать все, что не имеет года
            try:
                if int(object['year']) < 1930:
                    fillcolor = 'red'
                elif int(object['year']) < 1970:
                    fillcolor = 'orange'
                elif int(object['year']) < 2000:
                    fillcolor = 'yellow'
                elif int(object['year']) < 2023:
                    fillcolor = 'green'
            except BaseException:
                fillcolor = 'blue'
            total_schools = int(object['over_schools']) + int(object['free_schools'])
            #statistic_text = """
            #<i>Количество детей: {} <Br> Количество школьников: {} <Br> Количество взрослых: {} <Br>
            #Год постройки: {} <Br> Количество школ в радиусе доступности: {} <Br> Количество свободных школ: {} <Br>
            # Количество детских садов в радиусе доступности: {} <Br>
            # Количество медицинских учреждений в радусе доступности: {} <Br></i>
            #""".format(object['kindergartens'], object['Pupils'], object['adults'], object['year'], total_schools,
            #           object['free_schools'], object['avaliable_kindergartens'], object['avaliable_medicine'])
            html = """
            <li><a href="/data_update{}_{}" target=_parent><big><big>Редактировать данные</big></big></a></li>
            """.format('b', object['id'].split('/')[0] + '=' + object['id'].split('/')[1])

            fields_map = {}
            kinder_text = 'Количество детей'
            student_text = 'Количество школьников'
            adult_text = 'Количество взрослых'
            year_text = 'Год постройки'
            schools_number_text = 'Количество школ в радиусе доступности'
            avaliable_schools_number_text = 'Количество свободных школ'
            kinder_number_text = 'Количество детских садов в радиусе доступности'
            med_number_text = 'Количество медицинских учреждений в радусе доступности'

            header = '<i>{}, {}</i>'.format(object['addr:street'],
                                                           object['addr:housenumber'])
            left_col_color = "#00008b"
            right_col_color = "#ffff00"
            fields_map[kinder_text] = object['kindergartens']
            fields_map[student_text] = object['Pupils']
            fields_map[adult_text] = object['adults']
            fields_map[year_text] = object['year']
            fields_map[schools_number_text] = total_schools
            fields_map[avaliable_schools_number_text] = object['free_schools']
            fields_map[kinder_number_text] = object['avaliable_kindergartens']
            fields_map[med_number_text] = object['avaliable_medicine']

            statistic_text = self.get_buffer_text(header, left_col_color, right_col_color, fields_map)

            polyline = folium.PolyLine(locations=points, color=color, fill_color=fillcolor, fill_opacity=fillopacity,
                            #popup=statistic_text.format(
                            #    object['kindergartens'], object['Pupils'],
                            #    object['adults'], object['year']),
                            popup=folium.Popup(statistic_text + html),
                            tooltip='<i>{}, {}</i>'.format(object['addr:street'],
                                                           object['addr:housenumber']))
            if mf_group == 'feature':
                polyline.add_to(feature_group_object)
            elif mf_group == 'map':
                polyline.add_to(maps)

        if feature_group_name == 'medicine':
            html_text = """
                        <li><a href="/map{}_{}" target=_parent><big><big>Построить радиус доступности</big></big></a></li>
                          """.format('m', object['id'].split('/')[0] + '=' + object['id'].split('/')[1])
            folium.PolyLine(locations=points, color=color, fill_color=fillcolor, fill_opacity=fillopacity,
                            popup=folium.Popup(html_text),
                            tooltip='<i>{}</i>'.format(object['addr:housenumber'])).add_to(feature_group_object)

    def add_circle(self, location_latitude, location_longitude, radius, circle_color, fill_color, feature_group_object, feature_group_name):
        folium.Circle(location=[location_latitude, location_longitude], radius=radius,
                      color=circle_color, fill_color=fill_color).add_to(feature_group_object)

    def get_feature_group_name_on_russian(self, feature_group_name):
        if feature_group_name == 'school':
            return 'Школы'
        elif feature_group_name == 'kindergartens':
            return 'Детские сады'
        elif feature_group_name == 'medicine':
            return 'Медицинские учреждения'
        elif feature_group_name == 'buildings':
            return 'Жилые зданий'

    #Функция для нанесения объектов на карту, которые ложатся внуть полигонов, поступающих на вход
    def print_objects(self, maps, df_objects, polygons_df, color, feature_group_name, object_type_name, marker, borders, circle):
        if len(polygons_df) > 0:
            #df_objects['centroid'] = df_objects.geometry.centroid
            #objects_df = df_objects.set_geometry('centroid')
            #df_inter = gpd.sjoin(objects_df, polygons_df)
            self.df_inter = self.intersction(df_objects, polygons_df)
            #Для отображения года постройки у жилых зданий
            if object_type_name == 'buildings':
                self.df_inter['year'].fillna('нет данных', inplace=True)


            feature_group_object = folium.FeatureGroup(self.get_feature_group_name_on_russian(feature_group_name))

            for i in range(self.df_inter.shape[0]):
                #Добавление маркера объекта на карту
                location_latitude = self.df_inter.iloc[i]['centroid latitude']
                location_longitude = self.df_inter.iloc[i]['centroid longitude']
                if marker == True:
                    #folium.Marker(location=[location_latitude, location_longitude],
                    #          popup='<i>{}</i>'.format(self.df_inter.iloc[i]['short_name']),
                    #              tooltip='Click here', icon=folium.Icon(color=color)).add_to(feature_group_object)
                    self.add_marker(location_latitude, location_longitude, self.df_inter.iloc[i], color, feature_group_object, feature_group_name)

                #Добавление границ объекта на карту
                if borders == True:
                    #points = [self.swap_points(list(self.df_inter.iloc[i]['geometry'].exterior.coords))]
                    #folium.PolyLine(locations=points, color=color, fill_color="blue", fill_opacity=0.3,
                    #                popup='<i>{}</i>'.format(self.df_inter.iloc[i]['short_name']), tooltip='<i>{}</i>'.format(self.df_inter.iloc[i]['short_name'])).add_to(feature_group_object)
                    self.add_object_borders(maps, self.df_inter.iloc[i], color=color,
                                            fillcolor='blue', fillopacity=0.3,
                                            feature_group_object=feature_group_object,
                                            feature_group_name=feature_group_name, mf_group='feature')

                #Добавление кругов
                if circle == True:
                    radius = 500
                    circle_color = 'red'
                    fill_color = 'blue'
                    #folium.Circle(location=[location_latitude, location_longitude], radius=radius,
                    #              color=circle_color, fill_color=fill_color).add_to(feature_group_object)

                    #self.add_circle(location_latitude, location_longitude, radius, circle_color, fill_color, feature_group_object, feature_group_name)
                    self.df_inter.iloc[i].buffer(500)

                if marker == False and borders == False and circle == False:
                    pass

            #feature_group_object.add_to(maps)

        return feature_group_object

    def color_poly_choropleth(self, maps, data, json, columns, legend_name, feature, bins):
        folium.Choropleth(
            geo_data=json,
            name="Распредление по районам",
            data=data,
            columns=columns,
            key_on="feature.id",
            fill_color="YlGn",
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name=legend_name,
            nan_fill_color='white',
            bins=bins

        ).add_to(maps)

        return maps

    def fill_opacity(self, x):
        positive_fill = 0.5
        negative_fill = 0.0
        if self.first_flag:
            self.first_flag = False
            return negative_fill
        if x['properties']['index_right'] not in self.is_hex_colored:
            self.is_hex_colored[x['properties']['index_right']] = 1
            return positive_fill
        else:
            self.is_hex_colored[x['properties']['index_right']] += 1
            return negative_fill


    def fill_color_for_hex(self, maps, df_intersection_for_choro, feature_group_name, count_map, object_type_name):

        max_count = max(count_map.values())
        min_count = min(count_map.values())
        avg_count = int((max_count + min_count) / 2)
        avg_1 = int((avg_count + min_count) / 2)
        avg_2 = int((avg_count + max_count) / 2)
        color_list = ['red', 'yellow', 'green']



        if object_type_name == 'schools':
            alias = ['Количество школ: ']
            avg_1 = 1
            avg_2 = 3
        elif object_type_name == 'buildings':
            alias = ['Количество жителей: ']
            avg_1 = 1000
            avg_2 = 3000
        elif object_type_name == 'medicine':
            alias = ['Количество медицинских учереждений: ']
            avg_1 = 1
            avg_2 = 3
        elif object_type_name == 'kindergartens':
            alias = ['Количество детских садов: ']
            avg_1 = 1
            avg_2 = 3
        else:
            alias = ['miss: ']

        colormap = branca.colormap.LinearColormap(vmin=avg_1, vmax=avg_2, colors=color_list, caption='Распределение внутри района')
        self.is_hex_colored.clear()
        self.first_flag = True

        feature_group_object = folium.FeatureGroup(feature_group_name)
        colormap.add_to(maps)
        #colormap._repr_html_()

        folium.GeoJson(
            df_intersection_for_choro,
            style_function=lambda x: {
                'fillColor': colormap(x['properties']['count']),
                'color': 'black',
                'fillOpacity': self.fill_opacity(x)},
            tooltip=folium.features.GeoJsonTooltip(fields=[
                'count'],
                 aliases=alias),
            name=feature_group_name).add_to(feature_group_object)

        #feature_group_object.add_to(maps)



        return feature_group_object

    def split_by_hex_and_calculate(self, df_object, object_type_name):
        ddf = df_object.groupby('index_right')['id'].nunique()
        index_list = list(ddf.index)
        value_list = list(ddf)
        cols_list = ['kindergartens', 'Pupils', 'adults']
        count_map = {}
        df_object['count'] = ''
        if object_type_name == 'schools' or object_type_name == 'medicine' or object_type_name == 'kindergartens':
            for i in range(len(index_list)):
                count_map[index_list[i]] = value_list[i]
                df_object.loc[(df_object['index_right'] == index_list[i]), 'count'] = value_list[i]

        if object_type_name == 'buildings':
            for i in range(len(index_list)):
                total_number_of_people = df_object.loc[df_object['index_right'] == index_list[i], cols_list].astype(int).sum()
                total_number_of_people = total_number_of_people[0] + total_number_of_people[1] + total_number_of_people[2]
                count_map[index_list[i]] = total_number_of_people
                df_object.loc[(df_object['index_right'] == index_list[i]), 'count'] = float(total_number_of_people)

        df_intersection_for_choro = gpd.GeoDataFrame(df_object.set_index('id')[["geometry", 'index_right', 'count']]).to_json()

        return df_intersection_for_choro, count_map

    def choropleth_for_hex(self, maps, feature_group_name, object_type_name):
        df_intersection_for_choro = self.df_inter.copy(deep=True)
        df_intersection_for_choro.set_geometry('polygon')
        df_intersection_for_choro.drop(columns=['geometry'], axis=1, inplace=True)
        df_intersection_for_choro.rename(columns={'polygon': 'geometry'}, inplace=True)

        #df_intersection_for_choro = gpd.GeoDataFrame(df_intersection_for_choro.set_index('id')[["geometry", 'index_right', 'school_count']]).to_json()

        self.df_intersection_for_choro, self.count_map = self.split_by_hex_and_calculate(df_intersection_for_choro, object_type_name)
        feature_group_object = self.fill_color_for_hex(maps, self.df_intersection_for_choro, feature_group_name, self.count_map, object_type_name)

        return feature_group_object

    def print_choropleth(self, maps, df_objects, df_borders, feature_group_name, type_t, object_type_name):
        if len(df_borders) > 0:
            if type_t == 'district':
                id_column = 'district_id'
            if type_t == 'region':
                id_column = 'region_id'
            district_list = list(df_borders[id_column])
            df_objects = df_objects.loc[df_objects[id_column].isin(district_list)]

            df_objects['geometry'] = df_objects['geometry'].astype(str)
            if object_type_name == 'buildings':
                df_objects['total_number_of_people'] = df_objects['kindergartens'].astype(int) + df_objects['Pupils'].astype(int) + df_objects['adults'].astype(int)
                agg_all = df_objects.groupby([id_column], as_index=False).agg({'total_number_of_people': 'sum'}).rename(
                    columns={'total_number_of_people': 'counts'})
                legend_name = 'Количество житилей в пределах района'
            else:
                agg_all = df_objects.groupby([id_column], as_index=False).agg({'centroid latitude': 'count'}).rename(
                    columns={'centroid latitude': 'counts'})
            if object_type_name == 'schools':
                legend_name = 'Количество школ в пределах района'
            if object_type_name == 'medicine':
                legend_name = 'Количество медицинских учреждений в пределах района'
            if object_type_name == 'kindergartens':
                legend_name = 'Количество детских садов в пределах района'
            agg_all.rename(columns={id_column: 'id'}, inplace=True)
            df_borders.rename(columns={id_column: 'id'}, inplace=True)
            data_geo_1 = gpd.GeoSeries(df_borders.set_index('id')["geometry"]).to_json()

            maps = self.color_poly_choropleth(maps, agg_all, data_geo_1, ["id","counts"],
                                                                  legend_name, 'counts', 10)

            feature_group_object = self.choropleth_for_hex(maps, feature_group_name, object_type_name)
            #self.feature_group_build.add_to(maps)
            #self.feature_group_school.add_to(maps)




        return feature_group_object

    def inter_for_buffer(self, df_objects, polygons_df):
        df_objects['centroid'] = df_objects.geometry.centroid
        polygons_df['polygon'] = polygons_df.geometry
        objects_df = df_objects.set_geometry('centroid')

        return gpd.sjoin(objects_df, polygons_df)

    def print_buffer(self, maps, object, radius, df_buildings, feature_group_name, type_o):
        centroid_latitude = list(object['centroid latitude'])[0]
        centroid_longitude = list(object['centroid longitude'])[0]

        feature_group = folium.FeatureGroup('Буфер доступности')

        df = pd.DataFrame(
            {
                'lat': [centroid_latitude],
                'lon': [centroid_longitude],
                'rad': [radius]
            }
        )

        #Отрисовка круга нужного радиуса на карте. Так сложно потому что земля вам не шарик, а хер пойми что
        df['geom'] = df.apply(lambda r: Point(r['lon'], r['lat']), axis=1)
        gdf = gpd.GeoDataFrame(df, geometry='geom', crs='epsg:4326')
        gdf_flat = gdf.to_crs('epsg:6347')
        gdf_flat['geom'] = gdf_flat.geometry.buffer(df.rad)
        gdf = gdf_flat.to_crs('epsg:4326')
        points = list(list(gdf['geom'])[0].exterior.coords)
        points = self.swap_points(points)
        color = 'red'
        fillcolor = 'blue'
        fillopacity = 0.3
        polyline = folium.PolyLine(locations=points, color=color, fill_color=fillcolor, fill_opacity=fillopacity)
        polyline.add_to(feature_group)

        #Датафрейм для пересечения
        frame_for_inter = gpd.GeoDataFrame()
        frame_for_inter['geometry'] = [Polygon(self.swap_points(points))]
        #print(frame_for_inter['geometry'])

        #Получаем множество жилых домов, которые попадют в заданный буфер и считаем данные
        df_inter_buffer = self.inter_for_buffer(df_buildings, frame_for_inter)
        kinder_number = 0
        students_number = 0
        adults_number = 0
        total_buildings_number = df_inter_buffer.shape[0]
        for i in range(df_inter_buffer.shape[0]):
            kinder_number += int(df_inter_buffer.iloc[i]['kindergartens'])
            students_number += int(df_inter_buffer.iloc[i]['Pupils'])
            adults_number += int(df_inter_buffer.iloc[i]['adults'])

        #Добавляем маркер для объекта,для которого строится буффер
        self.add_marker(centroid_latitude, centroid_longitude, object, 'blue', feature_group, type_o, total_buildings_number, kinder_number, students_number, adults_number)

        # Добавляем дома на карту
        for i in range(df_inter_buffer.shape[0]):
            self.add_object_borders(maps, df_inter_buffer.iloc[i], color='black',
                                            fillcolor='green', fillopacity=0.3,
                                            feature_group_object=feature_group,
                                            feature_group_name=feature_group_name, mf_group='feature')
            #points = [self.swap_points(list(df_inter_buffer.iloc[i]['geometry'].exterior.coords))]
            #folium.PolyLine(locations=points, color='black', fill_color='green', fill_opacity=0.3,
            #            popup='<i>{}</i>'.format(df_inter_buffer.iloc[i]['addr:street']),
            #            tooltip='<i>{}</i>'.format(df_inter_buffer.iloc[i]['addr:housenumber'])).add_to(maps)

        #feature_group.add_to(maps)

        return feature_group

    def print_buffer_short(self, object, radius, df_buildings):
        centroid_latitude = list(object['centroid latitude'])[0]
        centroid_longitude = list(object['centroid longitude'])[0]

        df = pd.DataFrame(
            {
                'lat': [centroid_latitude],
                'lon': [centroid_longitude],
                'rad': [radius]
            }
        )

        #Отрисовка круга нужного радиуса на карте. Так сложно потому что земля вам не шарик, а хер пойми что
        df['geom'] = df.apply(lambda r: Point(r['lon'], r['lat']), axis=1)
        gdf = gpd.GeoDataFrame(df, geometry='geom', crs='epsg:4326')
        gdf_flat = gdf.to_crs('epsg:6347')
        gdf_flat['geom'] = gdf_flat.geometry.buffer(df.rad)
        gdf = gdf_flat.to_crs('epsg:4326')
        points = list(list(gdf['geom'])[0].exterior.coords)
        points = self.swap_points(points)

        #Датафрейм для пересечения
        frame_for_inter = gpd.GeoDataFrame()
        frame_for_inter['geometry'] = [Polygon(self.swap_points(points))]

        #Получаем множество жилых домов, которые попадют в заданный буфер и считаем данные
        df_inter_buffer = self.inter_for_buffer(df_buildings, frame_for_inter)

        return df_inter_buffer


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
    #Датафрейм для пересеченных объектов
    df_inter = gpd.GeoDataFrame()
    #Вспомогательные переменные для раскраски гексагонов
    is_hex_colored = {}
    first_flag = True

    df_intersection_for_choro = gpd.GeoDataFrame()
    count_map = {}
