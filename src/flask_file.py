from flask import Flask
from flask import render_template, render_template_string, request
import folium
from map_module import Map_master
import geopandas as gpd
from flask import session
from json2html import *
from statistic import Stat_master
from folium.plugins import Draw

people_counter = 0
map_dict = {}

class map_class():

    def initiation(self, centroid_latitude=55.757220, centroid_longitude=37.621184, zoom=12):
        self.maps = folium.Map(width=1000, height=500, left='11%', top='10%', location=[centroid_latitude, centroid_longitude], zoom_start=zoom)

    def repr(self):
        self.html_map = self.maps._repr_html_()


    maps = folium.Map(width=1000, height=500, left='11%', top='10%', location=[55.4424, 37.3636], zoom_start=9)

    html_map = maps._repr_html_()

    stat_slave = Stat_master()

    control = folium.LayerControl()

    draw = Draw(export=False, draw_options={'circle': False, 'rectangle': False, 'circlemarker': False, 'polyline':False})

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
    df_kindergartens = osm.read_data(osm.kindergartens_data_name_mos_transform)
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
        elif type_o == 'kindergartens':
            return df_kindergartens

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

    def return_object_for_buffer_and_update(type, object_id):
        if type == 's':
            type_o = 'schools'
        elif type == 'k':
            type_o = 'kindergartens'
        elif type == 'm':
            type_o = 'medicine'
        elif type == 'b':
            type_o = 'buildings'
        df_objects = get_objects_df(type_o)
        if type == 's' or type == 'k':
            object = df_objects.loc[df_objects['id'] == int(object_id)]
        elif type == 'm' or 'b':
            idd = object_id.replace('=', '/')
            object = df_objects.loc[df_objects['id'] == idd]

        return object, type_o

    def get_radius_and_lat_lon(object, type, distrcit_id_list, region_id_list):
        district_id = list(object['district_id'])[0]
        region_id = list(object['region_id'])[0]
        centroid_latitude = float(list(object['centroid latitude'])[0])
        centroid_longitude = float(list(object['centroid longitude'])[0])
        if district_id in distrcit_id_list or region_id in region_id_list:
            if type == 's':
                radius = 750
            elif type == 'k':
                radius = 500
            elif type == 'm':
                radius = 1500
        else:
            if type == 's':
                radius = 500
            elif type == 'k':
                radius = 300
            elif type == 'm':
                radius = 1500

        return centroid_latitude, centroid_longitude, radius

    def change_buildings_avaliable(object, change_value):
        distrcit_id_list = ['relation/1257484', 'relation/2162195', 'relation/1255942', 'relation/1257218',
                            'relation/364001', 'relation/1275551', 'relation/1275608', 'relation/1257786',
                            'relation/1255987', 'relation/1275627']
        region_id_list = ['relation/2162196']

        centroid_latitude, centroid_longitude, radius = get_radius_and_lat_lon(object, 's', distrcit_id_list, region_id_list)

        df_changed_buildings = map_slave.print_buffer_short(object, radius, df_buildings)

        for i in range(df_changed_buildings.shape[0]):
            id = df_changed_buildings.iloc[i]['id']
            df_buildings.loc[df_buildings['id'] == id, 'free_schools'] = df_buildings.loc[df_buildings['id'] == id]['free_schools'] + change_value
            df_buildings.loc[df_buildings['id'] == id, 'over_schools'] = df_buildings.loc[df_buildings['id'] == id]['over_schools'] - change_value

    def change_district_statistic_for_schools(districi_id, type_t):
        zone_1 = ['relation/1281220', 'relation/1250526', 'relation/1257484', 'relation/446079', 'relation/2162195',
                  'relation/445298',
                  'relation/1281648', 'relation/444908', 'relation/446114', 'relation/1255942', 'relation/952191',
                  'relation/1257218',
                  'relation/240229', 'relation/1281702', 'relation/1252407', 'relation/364001', 'relation/1278046',
                  'relation/1292499',
                  'relation/1250619', 'relation/1299106', 'relation/1275551', 'relation/1292679', 'relation/446115',
                  'relation/446272',
                  'relation/445281', 'relation/445280', 'relation/364551', 'relation/1275608', 'relation/1257786',
                  'relation/1292731',
                  'relation/446112', 'relation/1255987', 'relation/428431', 'relation/445299', 'relation/1281263',
                  'relation/1275627']
        zone_2 = ['relation/1252465', 'relation/1319060', 'relation/1252424', 'relation/446078', 'relation/1255704',
                  'relation/445297',
                  'relation/1319142', 'relation/1281209', 'relation/1292286', 'relation/1319263', 'relation/1319245',
                  'relation/445277',
                  'relation/1292211', 'relation/444812', 'relation/226927', 'relation/442741', 'relation/445273',
                  'relation/1278064',
                  'relation/1252448', 'relation/1250724', 'relation/455222', 'relation/1319078', 'relation/442733',
                  'relation/1257472',
                  'relation/445283', 'relation/455528', 'relation/535655', 'relation/455460', 'relation/535662',
                  'relation/1298976',
                  'relation/455539', 'relation/456807', 'relation/445282', 'relation/1292749', 'relation/1299013',
                  'relation/446081',
                  'relation/1250618', 'relation/1255680', 'relation/446086', 'relation/445279', 'relation/1299031',
                  'relation/434560',
                  'relation/455184', 'relation/445276', 'relation/446111', 'relation/445274', 'relation/950641',
                  'relation/535680',
                  'relation/951305', 'relation/950664', 'relation/431464', 'relation/446087', 'relation/446080',
                  'relation/1278096',
                  'relation/446271', 'relation/951334']

        zone_3 = ['relation/181288', 'relation/380702', 'relation/380703', 'relation/380704', 'relation/380705', 'relation/380706', 'relation/380707', 'relation/380708', 'relation/445275', 'relation/445278', 'relation/445284', 'relation/445285', 'relation/446082', 'relation/446083', 'relation/446084', 'relation/446085', 'relation/446116', 'relation/446117', 'relation/455203', 'relation/455208', 'relation/455451', 'relation/531264', 'relation/531287', 'relation/548619', 'relation/574667', 'relation/950639', 'relation/950658', 'relation/951336', 'relation/1255563', 'relation/1255576', 'relation/1255577', 'relation/1255602', 'relation/1257403', 'relation/1257455', 'relation/1320371', 'relation/1320424', 'relation/1320510', 'relation/1320566', 'relation/1320570', 'relation/1668007', 'relation/1693596', 'relation/1693661', 'relation/1693667', 'relation/1693672', 'relation/1703093', 'relation/1703095', 'relation/2092922', 'relation/2092924', 'relation/2092925', 'relation/2092927', 'relation/2092928', 'relation/2092929', 'relation/2092931']

        school_zone_1 = 105
        school_zone_2 = 112
        school_zone_3 = 124
        kinder_zone_1 = 46
        kinder_zone_2 = 55
        kinder_zone_3 = 63

        if type_t == 's':
            sub_df = df_schools.loc[df_schools['district_id'] == districi_id]
        elif type_t == 'k':
            sub_df = df_kindergartens.loc[df_kindergartens['district_id'] == districi_id]

        total_capacity = sub_df['capacity'].astype(int).sum()

        sub_df = df_buildings.loc[df_buildings['district_id'] == districi_id]
        cols_list = ['kindergartens', 'Pupils', 'adults']
        total_number_of_people = sub_df[cols_list].astype(int).sum()
        total_number_of_people = total_number_of_people[0] + total_number_of_people[1] + total_number_of_people[2]
        districts_df.loc[districts_df['district_id'] == districi_id, 'residents_number'] = total_number_of_people

        try:
            min_ob_index = int(total_capacity / total_number_of_people * 1000)
            if type_t == 's':
                if districi_id in zone_1:
                    if min_ob_index >= school_zone_1:
                        is_min_ob = 1
                    else:
                        is_min_ob = 0

                elif districi_id in zone_2:
                    if min_ob_index >= school_zone_2:
                        is_min_ob = 1
                    else:
                        is_min_ob = 0
                elif districi_id in zone_3:
                    if min_ob_index >= school_zone_3:
                        is_min_ob = 1
                    else:
                        is_min_ob = 0
            elif type_t == 'k':
                if districi_id in zone_1:
                    if min_ob_index >= kinder_zone_1:
                        is_min_ob = 1
                    else:
                        is_min_ob = 0

                elif districi_id in zone_2:
                    if min_ob_index >= kinder_zone_2:
                        is_min_ob = 1
                    else:
                        is_min_ob = 0
                elif districi_id in zone_3:
                    if min_ob_index >= kinder_zone_3:
                        is_min_ob = 1
                    else:
                        is_min_ob = 0
        except BaseException:
            min_ob_index = -1
            is_min_ob = -1

        if type_t == 's':
            districts_df.loc[districts_df['district_id'] == districi_id, 'obespech_schools_index'] = min_ob_index
            districts_df.loc[districts_df['district_id'] == districi_id, 'is_obespech_schools'] = is_min_ob
        if type_t == 'k':
            districts_df.loc[districts_df['district_id'] == districi_id, 'obespech_kinder_index'] = min_ob_index
            districts_df.loc[districts_df['district_id'] == districi_id, 'is_obespech_kinder'] = is_min_ob

    @app.route('/map_redaction_<type_t>_<object_id>')
    def data_redaction(type_t, object_id):
        new_object_dict = {}
        for i in request.values.items():
            new_object_dict[i[0]] = i[1]
        if type_t == 's':
            object_id = int(object_id)
            change_house_free_school_avaliable_flag = False
            new_object_dict['workload'] = int(int(new_object_dict['students']) / int(new_object_dict['capacity']) * 100)
            old_workload = list(df_schools.loc[df_schools['id'] == object_id]['workload'])[0]
            #print(old_workload)
            if (new_object_dict['workload'] >= 100 and old_workload < 100):
                change_value = -1
                change_house_free_school_avaliable_flag = True
            if (new_object_dict['workload'] < 100 and old_workload >= 100):
                change_value = 1
                change_house_free_school_avaliable_flag = True

            if change_house_free_school_avaliable_flag:
                change_buildings_avaliable(df_schools.loc[df_schools['id'] == object_id], change_value)

            df_schools.loc[df_schools['id'] == object_id, 'capacity'] = new_object_dict['capacity']
            df_schools.loc[df_schools['id'] == object_id, 'students'] = new_object_dict['students']
            df_schools.loc[df_schools['id'] == object_id, 'rating'] = new_object_dict['rating']
            df_schools.loc[df_schools['id'] == object_id, 'workload'] = new_object_dict['workload']

            change_district_statistic_for_schools(list(df_schools.loc[df_schools['id'] == object_id]['district_id'])[0], type_t)

        if type_t == 'k':
            object_id = int(object_id)
            df_kindergartens.loc[df_kindergartens['id'] == object_id, 'capacity'] = new_object_dict['capacity']
            df_kindergartens.loc[df_kindergartens['id'] == object_id, 'rating'] = new_object_dict['rating']

            change_district_statistic_for_schools(list(df_kindergartens.loc[df_kindergartens['id'] == object_id]['district_id'])[0], type_t)

        if type_t == 'b':
            object_id = object_id.replace('=', '/')
            print(df_buildings.loc[df_buildings['id'] == object_id]['kindergartens'])
            df_buildings.loc[df_buildings['id'] == object_id, 'kindergartens'] = new_object_dict['kindergartens']
            df_buildings.loc[df_buildings['id'] == object_id, 'Pupils'] = new_object_dict['Pupils']
            df_buildings.loc[df_buildings['id'] == object_id, 'adults'] = new_object_dict['adults']

            print(df_buildings.loc[df_buildings['id'] == object_id]['kindergartens'])

            change_district_statistic_for_schools(list(df_buildings.loc[df_buildings['id'] == object_id]['district_id'])[0], 's')
            change_district_statistic_for_schools(list(df_buildings.loc[df_buildings['id'] == object_id]['district_id'])[0], 'k')



        return basic_map(True, map_dict[session['Map']].districts_list, map_dict[session['Map']].region_list, map_dict[session['Map']].category)

    @app.route('/data_update<type>_<object_id>')
    def data_update(type, object_id):
        object, type_o = return_object_for_buffer_and_update(type, object_id)
        total_map = {}
        total_map['id'] = object_id
        total_map['type'] = type
        if type == 's':
            total_map['capacity'] = list(object['capacity'])[0]
            total_map['students_number'] = list(object['students'])[0]
            total_map['rating'] = list(object['rating'])[0]
            return render_template('data_update_schools.html', total_map=total_map)
        elif type == 'k':
            total_map['capacity'] = list(object['capacity'])[0]
            total_map['rating'] = list(object['rating'])[0]
            return render_template('data_update_kinder.html', total_map=total_map)
        elif type == 'b':
            total_map['kindergartens'] = list(object['kindergartens'])[0]
            total_map['Pupils'] = list(object['Pupils'])[0]
            total_map['adults'] = list(object['adults'])[0]
            return render_template('data_update_buildings.html', total_map=total_map)




    @app.route('/map<type>_<object_id>')
    def popup_id(type, object_id):
        distrcit_id_list = ['relation/1257484', 'relation/2162195', 'relation/1255942', 'relation/1257218',
                            'relation/364001', 'relation/1275551', 'relation/1275608', 'relation/1257786',
                            'relation/1255987', 'relation/1275627']
        region_id_list = ['relation/2162196']
        object, type_o = return_object_for_buffer_and_update(type, object_id)

        #Тут идет проверка на то, что наша  объект не входит в ЦАО, тк для них радиус 750 метров, а не 500
        centroid_latitude, centroid_longitude, radius = get_radius_and_lat_lon(object, type, distrcit_id_list, region_id_list)
        #return render_template('main_page.html')
        feature_group_name = 'buildings'
        map_dict[session['Map']].initiation(centroid_latitude, centroid_longitude, 15)
        map_dict[session['Map']].feature_group_borders.add_to(map_dict[session['Map']].maps)
        map_dict[session['Map']].feature_group_hexagon.add_to(map_dict[session['Map']].maps)
        map_dict[session['Map']].feature_group_objects.add_to(map_dict[session['Map']].maps)
        #map_dict[session['Map']].feature_group_choropleth.add_to(map_dict[session['Map']].maps)
        map_dict[session['Map']].feature_group_choropleth = map_slave.choropleth_for_hex(map_dict[session['Map']].maps, map_dict[session['Map']].feature_group_choropleth_name, map_dict[session['Map']].category)
        map_dict[session['Map']].feature_group_choropleth.add_to(map_dict[session['Map']].maps)
        map_dict[session['Map']].feature_group_buffer = map_slave.print_buffer(map_dict[session['Map']].maps, object, radius, df_buildings, feature_group_name, type_o)
        map_dict[session['Map']].feature_group_buffer.add_to(map_dict[session['Map']].maps)
        map_dict[session['Map']].control.add_to(map_dict[session['Map']].maps)
        map_dict[session['Map']].repr()
        return render_template('map_page.html', iframe=map_dict[session['Map']].html_map)

    @app.route('/map_add')
    def map_add():
        new_object_dict = {}
        for i in request.values.items():
            new_object_dict[i[0]] = i[1]

        return 'Sorry, but it does not work'

    @app.route('/add_building')
    def add_object():
        map_dict[session['Map']].initiation()
        map_dict[session['Map']].draw.add_to(map_dict[session['Map']].maps)
        map_dict[session['Map']].repr()
        return render_template('add_page.html', iframe=map_dict[session['Map']].html_map)

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

            if category == 'kindergartens':
                map_dict[session['Map']].category = 'kindergartens'
                type_o = category
                df_objects = get_objects_df(type_o)
                color = 'red'
                map_dict[session['Map']].feature_group_objects = map_slave.print_objects(map_dict[session['Map']].maps, df_objects, polygons_df, color, 'kindergartens', 'kindergartens',
                                               marker=False, borders=True, circle=False)

                map_dict[session['Map']].feature_group_objects.add_to(map_dict[session['Map']].maps)

                df_borders, type_t = get_districts_or_regions(districts_list, region_list)
                map_dict[session['Map']].feature_group_choropleth = map_slave.print_choropleth(map_dict[session['Map']].maps, df_objects, df_borders, 'kindergartens in hex', type_t, 'kindergartens')

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

    #Преобразование данных по районам и округам в папке additional_code ноутбук preparation_for_statistic
    @app.route('/stat', methods=['POST', 'GET'])
    def stat():
        models = {}
        if len(map_dict[session['Map']].districts_list) > 0:
            territories = map_dict[session['Map']].stat_slave.get_districts(map_dict[session['Map']].districts_list, districts_df)
            for i in range(len(territories)):
                area = map_dict[session['Map']].stat_slave.get_area(territories[i], 'district')
                schools_number = map_dict[session['Map']].stat_slave.get_data(territories[i], 'district', 'schools_number')
                schools_workload = map_dict[session['Map']].stat_slave.get_data(territories[i], 'district', 'schools_workload')
                kindergartens_number = map_dict[session['Map']].stat_slave.get_data(territories[i], 'district', 'kindergartens_number')
                medicine_number = map_dict[session['Map']].stat_slave.get_data(territories[i], 'district', 'medicine_number')
                buildings_number = map_dict[session['Map']].stat_slave.get_data(territories[i], 'district', 'buildings_number')
                residents_number = map_dict[session['Map']].stat_slave.get_data(territories[i], 'district', 'residents_number')
                avg_year = map_dict[session['Map']].stat_slave.get_data(territories[i], 'district', 'avg_year')
                without_schools = map_dict[session['Map']].stat_slave.get_data(territories[i], 'district', 'without_schools')
                without_kindergartens = map_dict[session['Map']].stat_slave.get_data(territories[i], 'district', 'without_kindergartens')
                without_medicine = map_dict[session['Map']].stat_slave.get_data(territories[i], 'district', 'without_medicine')
                schools_index = map_dict[session['Map']].stat_slave.get_data(territories[i], 'district', 'obespech_schools_index')
                is_schools_obespech = map_dict[session['Map']].stat_slave.get_data(territories[i], 'district',
                                                                             'is_obespech_schools')
                if is_schools_obespech == 0:
                    is_schools_obespech = 'Нет'
                elif is_schools_obespech == 1:
                    is_schools_obespech = 'Да'
                kinder_index = map_dict[session['Map']].stat_slave.get_data(territories[i], 'district', 'obespech_kinder_index')
                is_kinder_obespech = map_dict[session['Map']].stat_slave.get_data(territories[i], 'district',
                                                                             'is_obespech_kinder')
                if is_kinder_obespech == 0:
                    is_kinder_obespech = 'Нет'
                elif is_kinder_obespech == 1:
                    is_kinder_obespech = 'Да'

                models[territories[i]] = {'Площадь (м2)': area,
                                          'Количество школ': schools_number,
                                          'Средняя загруженность школ(в процентах)': schools_workload,
                                          'Количество детских садов': kindergartens_number,
                                          'Количество мед учреждений': medicine_number,
                                          'Количество жилых домов': buildings_number,
                                          'Количество жителей': residents_number,
                                          'Средний год постройки зданий': avg_year,
                                          'Процент домов,находящихся вне установленной зоны пешей доступности от школ': without_schools,
                                          'Процент домов,находящихся вне установленной зоны пешей доступности от детских садов': without_kindergartens,
                                          'Процент домов,находящихся вне установленной зоны пешей доступности от медицинских учреждений': without_medicine,
                                          'Количество мест в школах (на 1000 человек)': schools_index,
                                          'Удовлетворяет ли количество мест в школах нормативам': is_schools_obespech,
                                          'Количество мест в детских садах (на 1000 человек)': kinder_index,
                                          'Удовлетворяет ли количество мест детских садах нормативам': is_kinder_obespech}

        elif len(map_dict[session['Map']].region_list) > 0:
            territories = map_dict[session['Map']].stat_slave.get_regions(map_dict[session['Map']].region_list, regions_df)
            for i in range(len(territories)):
                area = map_dict[session['Map']].stat_slave.get_area(territories[i], 'region')
                schools_number = map_dict[session['Map']].stat_slave.get_data(territories[i], 'region',
                                                                              'schools_number')
                schools_workload = map_dict[session['Map']].stat_slave.get_data(territories[i], 'region',
                                                                                'schools_workload')
                kindergartens_number = map_dict[session['Map']].stat_slave.get_data(territories[i], 'region',
                                                                                    'kindergartens_number')
                medicine_number = map_dict[session['Map']].stat_slave.get_data(territories[i], 'region',
                                                                               'medicine_number')
                buildings_number = map_dict[session['Map']].stat_slave.get_data(territories[i], 'region',
                                                                                'buildings_number')
                residents_number = map_dict[session['Map']].stat_slave.get_data(territories[i], 'region',
                                                                                'residents_number')
                avg_year = map_dict[session['Map']].stat_slave.get_data(territories[i], 'region', 'avg_year')
                without_schools = map_dict[session['Map']].stat_slave.get_data(territories[i], 'region',
                                                                               'without_schools')
                without_kindergartens = map_dict[session['Map']].stat_slave.get_data(territories[i], 'region',
                                                                                     'without_kindergartens')
                without_medicine = map_dict[session['Map']].stat_slave.get_data(territories[i], 'region',
                                                                                'without_medicine')
                models[territories[i]] = {'Площадь (м2)': area,
                                          'Количество школ': schools_number,
                                          'Средняя загруженность школ(в процентах)': schools_workload,
                                          'Количество детских садов': kindergartens_number,
                                          'Количество мед учреждений': medicine_number,
                                          'Количество жилых домов': buildings_number,
                                          'Количество жителей': residents_number,
                                          'Средний год постройки зданий': avg_year,
                                          'Процент домов,находящихся вне установленной зоны пешей доступности от школ': without_schools,
                                          'Процент домов,находящихся вне установленной зоны пешей доступности от детских садов': without_kindergartens,
                                          'Процент домов,находящихся вне установленной зоны пешей доступности от медицинских учреждений': without_medicine}

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

