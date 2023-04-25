from flask import Flask
from flask import render_template, render_template_string, request
import folium
from map_module import Map_master
import geopandas as gpd
from flask import session
from json2html import *
from statistic import Stat_master

people_counter = 0
map_dict = {}

class map_class():

    def initiation(self, centroid_latitude=55.757220, centroid_longitude=37.621184, zoom=12):
        self.maps = folium.Map(width=1000, height=500, left='11%', location=[centroid_latitude, centroid_longitude], zoom_start=zoom)

    def repr(self):
        self.html_map = self.maps._repr_html_()


    maps = folium.Map(width=1000, height=500, left='11%', location=[55.4424, 37.3636], zoom_start=9)

    html_map = maps._repr_html_()

    stat_slave = Stat_master()

    control = folium.LayerControl()

    feature_group_borders_name = 'borders'
    feature_group_hexagon_name = 'hexagons'
    feature_group_borders = folium.FeatureGroup(feature_group_borders_name)
    feature_group_hexagon = folium.FeatureGroup(feature_group_hexagon_name)

    feature_group_objects_name = 'object'
    feature_group_objects = folium.FeatureGroup(feature_group_objects_name)

    feature_group_choropleth_name = 'choropleth'
    feature_group_choropleth = folium.FeatureGroup(feature_group_choropleth_name)

    feature_group_buffer_name = 'buffer'
    feature_group_buffer = folium.FeatureGroup(feature_group_buffer_name)

    districts_list = []
    regions_list = []

    category = 'none'




def run_flask(osm):

    app = Flask(__name__)
    app.secret_key = '1234567890'
    map_slave = Map_master()
    df_schools = osm.read_data(osm.school_data_name_mos_transform)
    df_buildings = osm.read_data(osm.building_data_name_transform)
    df_medicine = osm.read_data(osm.medicine_data_name_transform)
    districts_df = osm.read_data(osm.borders_data_name_transform)
    regions_df = osm.read_data(osm.regions_borders_data_name_transform)
    #Map = map_class()


    @app.route('/')
    def basic_page():
        global people_counter
        global map_dict
        if 'visits' in session:
            session['visits'] = session.get('visits') + 1# чтение и обновление данных сессии
            map_dict[session['Map']] = map_dict[session['Map']]
        else:
            session['visits'] = 1  # настройка данных сессии
            session['Map'] = people_counter
            Mapp = map_class()
            map_dict[session['Map']] = Mapp
            people_counter += 1
        #return "Total visits: {}".format(session.get('visits'))
        return render_template('main_page.html')

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
            return render_template('map_page.html', iframe=map_dict[session['Map']].html_map)

    @app.route('/map_<object_id>')
    def popup_id(object_id):
        type_o = 'schools'
        df_objects = get_objects_df(type_o)
        object = df_objects.loc[df_objects['id'] == int(object_id)]
        #Тут идет проверка на то, что наша школа не входит в ЦАО, тк для них радиус 750 метров, а не 500
        distrcit_id_list = ['relation/1257484', 'relation/2162195', 'relation/1255942', 'relation/1257218',
                            'relation/364001', 'relation/1275551', 'relation/1275608', 'relation/1257786',
                            'relation/1255987', 'relation/1275627']
        region_id_list = ['relation/2162196']
        district_id = list(object['district_id'])[0]
        region_id = list(object['region_id'])[0]
        centroid_latitude = float(list(object['centroid latitude'])[0])
        centroid_longitude = float(list(object['centroid longitude'])[0])
        if district_id in distrcit_id_list or region_id in region_id_list:
            radius = 750
        else:
            radius = 500
        #return render_template('main_page.html')
        feature_group_name = 'buildings'
        map_dict[session['Map']].initiation(centroid_latitude, centroid_longitude, 15)
        map_dict[session['Map']].feature_group_borders.add_to(map_dict[session['Map']].maps)
        map_dict[session['Map']].feature_group_hexagon.add_to(map_dict[session['Map']].maps)
        map_dict[session['Map']].feature_group_objects.add_to(map_dict[session['Map']].maps)
        #map_dict[session['Map']].feature_group_choropleth.add_to(map_dict[session['Map']].maps)
        map_dict[session['Map']].feature_group_choropleth = map_slave.choropleth_for_hex(map_dict[session['Map']].maps, map_dict[session['Map']].feature_group_choropleth_name, map_dict[session['Map']].category)
        map_dict[session['Map']].feature_group_choropleth.add_to(map_dict[session['Map']].maps)
        map_dict[session['Map']].feature_group_buffer = map_slave.print_buffer(map_dict[session['Map']].maps, object, radius, df_buildings, feature_group_name)
        map_dict[session['Map']].feature_group_buffer.add_to(map_dict[session['Map']].maps)
        map_dict[session['Map']].control.add_to(map_dict[session['Map']].maps)
        map_dict[session['Map']].repr()
        return render_template('map_page.html', iframe=map_dict[session['Map']].html_map)

    #Фигня с картой
    @app.route('/map')
    def basic_map(data_flag=False, districts_list=[], region_list=[], category='none'):
        print(session)
        map_slave.big_polygons_hex_list_regions = []
        map_slave.big_polygons_hex_list_district = []
        #maps = folium.Map(width=1000, height=500, left='11%', location=[55.4424, 37.3636], zoom_start=9)
        #Map = map_class()
        map_dict[session['Map']].initiation()
        map_dict[session['Map']].districts_list = districts_list
        map_dict[session['Map']].region_list = region_list
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

            map_dict[session['Map']].feature_group_borders = map_slave.print_district_borders(map_dict[session['Map']].maps, borders_hex_list, type_t, feature_group_borders_name)
            map_dict[session['Map']].feature_group_hexagon = map_slave.print_hexagones(map_dict[session['Map']].maps, borders_hex_list, type_t, feature_group_hexagon_name)

            map_dict[session['Map']].feature_group_borders.add_to(map_dict[session['Map']].maps)
            map_dict[session['Map']].feature_group_hexagon.add_to(map_dict[session['Map']].maps)

            #Вывод школ
            #school_print = True
            #building_print = True
            polygons_df = get_polygons_df()
            if category == 'schools':
                map_dict[session['Map']].category = 'schools'
                type_o = category
                df_objects = get_objects_df(type_o)
                color = 'red'
                map_dict[session['Map']].feature_group_objects = map_slave.print_objects(map_dict[session['Map']].maps, df_objects, polygons_df, color, 'school', 'schools',
                                               marker=False, borders=True, circle=False)

                map_dict[session['Map']].feature_group_objects.add_to(map_dict[session['Map']].maps)

                df_borders, type_t = get_districts_or_regions(districts_list, region_list)
                map_dict[session['Map']].feature_group_choropleth = map_slave.print_choropleth(map_dict[session['Map']].maps, df_objects, df_borders, 'schools in hex', type_t, 'schools')

                map_dict[session['Map']].feature_group_choropleth.add_to(map_dict[session['Map']].maps)

            #Вывод зданий
            if category == 'buildings':
                map_dict[session['Map']].category = 'buildings'
                type_o = category
                df_objects = get_objects_df(type_o)
                color = 'red'
                map_dict[session['Map']].feature_group_objects = map_slave.print_objects(map_dict[session['Map']].maps, df_objects, polygons_df, color, 'buildings', 'buildings',
                                               marker=False, borders=True, circle=False)

                map_dict[session['Map']].feature_group_objects.add_to(map_dict[session['Map']].maps)

                df_borders, type_t = get_districts_or_regions(districts_list, region_list)
                map_dict[session['Map']].feature_group_choropleth = map_slave.print_choropleth(map_dict[session['Map']].maps, df_objects, df_borders, 'buildings in hex', type_t, 'buildings')

                map_dict[session['Map']].feature_group_choropleth.add_to(map_dict[session['Map']].maps)

            if category == 'medicine':
                map_dict[session['Map']].category = 'medicine'
                type_o = category
                df_objects = get_objects_df(type_o)
                color = 'red'
                map_dict[session['Map']].feature_group_objects = map_slave.print_objects(map_dict[session['Map']].maps, df_objects, polygons_df, color, 'medicine', 'medicine',
                                               marker=False, borders=True, circle=False)
                map_dict[session['Map']].feature_group_objects.add_to(map_dict[session['Map']].maps)

                df_borders, type_t = get_districts_or_regions(districts_list, region_list)
                map_dict[session['Map']].feature_group_choropleth = map_slave.print_choropleth(map_dict[session['Map']].maps, df_objects, df_borders, 'medicine in hex', type_t, 'medicine')

                map_dict[session['Map']].feature_group_choropleth.add_to(map_dict[session['Map']].maps)

            #control = folium.LayerControl()

            #folium.LayerControl().add_to(Map.maps)
            map_dict[session['Map']].control.add_to(map_dict[session['Map']].maps)




        #html_map = Map.maps._repr_html_()
        map_dict[session['Map']].repr()
#
        return render_template('map_page.html', iframe=map_dict[session['Map']].html_map)

    @app.route('/stat', methods=['POST', 'GET'])
    def stat():
        models = {}
        if len(map_dict[session['Map']].districts_list) > 0:
            territories = map_dict[session['Map']].stat_slave.get_districts(map_dict[session['Map']].districts_list, districts_df)
            for i in range(len(territories)):
                models[territories[i]] = map_dict[session['Map']].stat_slave.get_district_area(territories[i])

        elif len(map_dict[session['Map']].region_list) > 0:
            territories = map_dict[session['Map']].stat_slave.get_regions(map_dict[session['Map']].region_list, regions_df)
            for i in range(len(territories)):
                models[territories[i]] = map_dict[session['Map']].stat_slave.get_region_area(territories[i])

        else:
            models['Список выбранных территорий'] = 'Территории не выбраны'

        models = json2html.convert(json=models)

        return render_template('stat.html', json_obj=models)



    #Адрес сервера, раскомментить на сервере
    #app.run(host='82.148.28.79', port=5001)

    #Адрес локальный отладочный, закомментить на серврее
    app.run(host='127.0.0.1', port=5001)

if __name__ == '__main__':
    run_flask()

