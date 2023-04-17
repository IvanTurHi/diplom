from flask import Flask
from flask import render_template, render_template_string, request
import folium
from map_module import Map_master
import geopandas as gpd


def run_flask(osm):

    app = Flask(__name__)
    map_slave = Map_master()
    df_schools = osm.read_data(osm.school_data_name_mos_transform)
    df_buildings = osm.read_data(osm.building_data_name_transform)
    df_medicine = osm.read_data(osm.medicine_data_name_transform)


    @app.route('/')
    def basic_page():
        return render_template('main_page.html')


    #Тестовая фигня, убрать потом
    def start():
        df_school = osm.read_data(osm.school_data_name_transform)
        df_school_test_with_444 = df_school.loc[df_school['district_name'] == 'район Измайлово']
        df_borders = osm.read_data(osm.borders_data_name_transform)
        df_borders_izm = df_borders.loc[df_borders['district_name'] == 'район Измайлово']
        return df_school_test_with_444, df_borders_izm

    @app.route('/hello_sasha')
    def hello_sasha():
        return 'Hello, Sasha! This is our diploma. CRY!'

    #Функция для загрузки данных
    def get_objects_df(type_o):
        if type_o == 'schools':
            #return osm.read_data(osm.school_data_name_mos_transform)
            return df_schools
        elif type_o == 'buildings':
            #return osm.read_data(osm.building_data_name_transform)
            return df_buildings
        elif type_o == 'medicine':
            #return osm.read_data(osm.medicine_data_name_transform)
            return df_medicine

    #Функция для сбора всех гексагонов в один большой список
    def form_geom_list_of_polygons(big_list):
        list_of_p = []
        for i in range(len(big_list)):
            for j in range(len(big_list[i])):
                list_of_p += list(big_list[i][j])

        return list_of_p

    #Функция возвращает датафрейм полигонов, что бы его потом можно было пересечь с датафреймом объектов
    def get_polygons_df():
        polygons_df = gpd.GeoDataFrame(columns=['geometry'])
        #if type_t == 'district':
        #    list_of_p = form_geom_list_of_polygons(map_slave.big_polygons_hex_list_district)
        #elif type_t == 'region':
        #    list_of_p = form_geom_list_of_polygons(map_slave.big_polygons_hex_list_regions)
        list_of_p = form_geom_list_of_polygons(map_slave.big_polygons_hex_list_district)
        list_of_p += form_geom_list_of_polygons(map_slave.big_polygons_hex_list_regions)

        polygons_df['geometry'] = list_of_p

        return polygons_df

    def get_district_and_region_list(items):
        districts_list = []
        regions_list = []
        category = 'none'
        #for i in items:
        #    print(i[0], i[1])
        for i in items:
            if 'district' in i[0]:
                districts_list.append(i[1])
            elif 'region' in i[0]:
                regions_list.append(i[1])
            elif 'category' in i[0]:
                category = i[1]
                #print(category)
        return districts_list, regions_list, category

    def form_df_borders_for_chlor(df_target, support_df, id_name):
        for i in range(len(support_df)):
            df_target.loc[len(df_target.index)] = [support_df.iloc[i][id_name], support_df.iloc[i]['geometry']]

        return df_target

    def get_districts_or_regions(districts_list, region_list):
        if len(districts_list) > 0:
            return map_slave.get_districts(districts_list), 'district'
        else:
            return map_slave.get_regions(region_list), 'region'


    @app.route('/map_d/', methods=['POST', 'GET'])
    def get_data():
        if request.method == 'POST':
            districts_list, regions_list, category = get_district_and_region_list(request.values.items())

            data_flag = True
            if len(districts_list) == 0 and len(regions_list) == 0:
                data_flag = False
            return basic_map(data_flag, districts_list, regions_list, category)
        elif request.method == 'GET':
            return basic_map(data_flag=False)

    #Фигня с картой
    @app.route('/map')
    def basic_map(data_flag=False, districts_list=[], region_list=[], category='none'):
        map_slave.big_polygons_hex_list_regions = []
        map_slave.big_polygons_hex_list_district = []
        maps = folium.Map(width=1000, height=500, left='11%', location=[55.4424, 37.3636], zoom_start=9)
        if data_flag == True:
            #districts_list = ['relation/181288', 'relation/364551', 'relation/2092928', 'relation/240229']
            #region_list = ['relation/226149', 'relation/1320234']

            if len(districts_list) > 0:
                #Отрисовка гексагонов на уровне районов
                type_t = 'district'
                feature_group_borders_name = 'district borders'
                feature_group_hexagon_name = 'district hexagons'
                borders_hex_list = districts_list
                #maps = map_slave.print_district_borders(maps, districts_list, type_t, 'district borders')
                #maps = map_slave.print_hexagones(maps, districts_list, type_t, 'district hexagons')
            else:
                #Отрисовка гексагонов на уровне округов
                type_t = 'region'
                feature_group_borders_name = 'region borders'
                feature_group_hexagon_name = 'region hexagons'
                borders_hex_list = region_list
                #maps = map_slave.print_district_borders(maps, region_list, type_t, 'region borders')
                #maps = map_slave.print_hexagones(maps, region_list, type_t, 'region hexagons')

            maps = map_slave.print_district_borders(maps, borders_hex_list, type_t, feature_group_borders_name)
            maps = map_slave.print_hexagones(maps, borders_hex_list, type_t, feature_group_hexagon_name)

            #Вывод школ
            #school_print = True
            #building_print = True
            polygons_df = get_polygons_df()
            if category == 'schools':
                type_o = category
                df_objects = get_objects_df(type_o)
                color = 'red'
                maps = map_slave.print_objects(maps, df_objects, polygons_df, color, 'school', 'schools',
                                               marker=False, borders=True, circle=False)

                df_borders, type_t = get_districts_or_regions(districts_list, region_list)
                maps = map_slave.print_choropleth(maps, df_objects, df_borders, 'schools in hex', type_t, 'schools')

            #Вывод зданий
            if category == 'buildings':
                type_o = category
                df_objects = get_objects_df(type_o)
                color = 'red'
                maps = map_slave.print_objects(maps, df_objects, polygons_df, color, 'buildings', 'buildings',
                                               marker=False, borders=True, circle=False)
                df_borders, type_t = get_districts_or_regions(districts_list, region_list)
                maps = map_slave.print_choropleth(maps, df_objects, df_borders, 'buildings in hex', type_t, 'buildings')

            if category == 'medicine':
                type_o = category
                df_objects = get_objects_df(type_o)
                color = 'red'
                maps = map_slave.print_objects(maps, df_objects, polygons_df, color, 'medicine', 'medicine',
                                               marker=False, borders=True, circle=False)
                df_borders, type_t = get_districts_or_regions(districts_list, region_list)
                maps = map_slave.print_choropleth(maps, df_objects, df_borders, 'medicine in hex', type_t, 'medicine')


            #df_districts = map_slave.get_regions(region_list)
            #type_t = 'region'
            #maps = map_slave.print_choropleth(maps, df_objects, df_districts, type_t, 'schools')

            #Построение хлорокарты для районов
            #df_borders_chlor = gpd.GeoDataFrame(columns=['id', 'geometry'])
            #df_districts = map_slave.get_districts(districts_list)
            #df_regions = map_slave.get_regions(region_list)
            #df_borders_chlor = form_df_borders_for_chlor(df_borders_chlor, df_districts, 'district_id')
            #df_borders_chlor = form_df_borders_for_chlor(df_borders_chlor, df_regions, 'region_id')






            folium.LayerControl().add_to(maps)

        #Вывод школ на уровне районов
        #type_t = 'district'
        #polygons_df = get_polygons_df(type_t)
        #color = 'red'
        #maps = map_slave.print_objects(maps, df_objects, polygons_df, color, 'school')


        #df_school_test_with_444, df_borders_izm = start()
        #print(df_borders_izm)
        #map = folium.Map()
#
        ##Вывод границ района, координаты указаны не в том порядке,
        ##поэтому координаты каждой точки необходимо поменять местами, иначе оказываемся где-то в Иране
        #geom = list(df_borders_izm['geometry'])[0]
        #points = list(geom.exterior.coords)
        #for i in range(len(points)):
        #    points[i] = points[i][::-1]
        #print(points)
#
        ##Добавление маркеров школы на карту
        #for i in range(df_school_test_with_444.shape[0]):
        #    location_latitude = df_school_test_with_444.iloc[i]['centroid latitude']
        #    location_longitude = df_school_test_with_444.iloc[i]['centroid longitude']
        #    folium.Marker(location=[location_latitude, location_longitude],
        #                  popup='<i>Школа №444</i>', tooltip='Click here').add_to(map)
#
        ##Добавление границ района на карту
        #folium.PolyLine(locations=points, color='red').add_to(map)

        #location_latitude = df_school_test_with_444.iloc[0]['centroid latitude']
        #location_longitude = df_school_test_with_444.iloc[0]['centroid longitude']
        #folium.Marker(location=[location_latitude, location_longitude],
        #              popup='<i>Marker</i>', tooltip='Click here').add_to(map)
#
        #location_latitude = df_school_test_with_444.iloc[1]['centroid latitude']
        #location_longitude = df_school_test_with_444.iloc[1]['centroid longitude']
        #folium.Marker(location=[location_latitude, location_longitude],
        #              popup='<i>Marker</i>', tooltip='Click here').add_to(map)




        html_map = maps._repr_html_()
        #with open('./templates/map.html', 'r') as f:
        #    html_text = f.read()
#
        return render_template('map_page.html', iframe=html_map)
#
        #return maps._repr_html_()

        #В целом работает
        #maps.save('templates/map.html')
        #return render_template('index.html')

        #return render_template_string(
        #"""
        #    <!DOCTYPE html>
        #    <html>
        #        <head></head>
        #        <body>
        #            <h1>Using an iframe</h1>
        #            {{ iframe|safe }}
        #        </body>
        #    </html>
        #""",
        #iframe=html_map,
        #)


    #Адрес сервера, раскомментить на сервере
    #app.run(host='82.148.28.79', port=5001)

    #Адрес локальный отладочный, закомментить на серврее
    app.run(host='127.0.0.1', port=5001)

if __name__ == '__main__':
    run_flask()

