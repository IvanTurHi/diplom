from flask import Flask
from flask import render_template, request
import requests
from utils import dictfromdatabase, notUsedTypes, centralDistricts
import json
import h3
from json2html import *
app = Flask(__name__)

@app.route('/hello_sasha')
def hello_sasha():
    return 'Hello, Sasha! This is our diploma. CRY!'

@app.route('/hello_vanya')
def hello_vanya():
    return 'Hello, Vanya! The server is working. The reason you here is not I have dropped the server'

#тестовая
@app.route('/main_page')
def hello_world():
    return render_template('main_page.html', user="test")

@app.route('/')
def basic_page():
    return render_template('main_page.html')

@app.route('/about')
def about():
    return render_template('about_page.html')

@app.route('/statistics')
def main_page():
    r = requests.get("http://connector:8000/counties")
    datacounties = json.loads(r.text)
    if len(datacounties) == 0:
        return "<h1>NO counts</h1>"
    keyscounts = [dictfromdatabase.get(x, x) for x in list(datacounties[0].keys())]
    r = requests.get("http://connector:8000/districts")
    datadistricts = json.loads(r.text)
    if len(datadistricts) == 0:
        return "<h1>NO districts</h1>"
    keysdistricts = [dictfromdatabase.get(x, x) for x in list(datadistricts[0].keys())]
    return render_template('statistics.html',
                        keyscounts = keyscounts,
                        counts=datacounties,
                        keysdistricts=keysdistricts,
                        datadistricts=datadistricts)

@app.route('/map')
def map_page():
    r = requests.get("http://connector:8000/districtcountyname")
    datadistricts = json.loads(r.text)
    #return datadistricts
    return render_template('map.html', user="test2", datadistricts=datadistricts)

def without_keys(d, listThrow):
    if listThrow == []:
        return {dictfromdatabase.get(x, x): d[x] for x in d if x not in notUsedTypes}
    else:
        return {dictfromdatabase.get(x, x): d[x] for x in d if x not in listThrow}

def makegeojson(data, listThrow = []):
    geojson = {
    "type": "FeatureCollection",
    "features": [
    {
        "type": "Feature",
        "geometry" : d['geometry'],
        "properties" : without_keys(d, listThrow),
    } for d in data]
    }
    return geojson

@app.route('/buildingfullinfo', methods=['POST'])
def buildingfullinfo():
    input_json = request.get_json(force=True)
    database = input_json['database']   
    r = requests.post("http://connector:8000/buildingfullinfo", json=input_json)
    datadistricts = json.loads(r.text)
    if database == 0:
        throwList = ['eoid', 'geometry', 'idspatial', 'shortname', 'totalarea', 'nametype', 'storey']
        return makegeojson(data=datadistricts, listThrow=throwList)
    elif database == 3:
        throwList = ['eoid', 'geometry', 'idspatial', 'shortname', 'totalarea', 'nametype', 'storey', 'currentworkload']
        return makegeojson(data=datadistricts, listThrow=throwList)
    else:
        return makegeojson(data=datadistricts)

@app.route('/districtsfullinfo', methods=['POST'])
def districtsfullinfo():
    input_json = request.get_json(force=True)
    r = requests.post("http://connector:8000/districtsfullinfo", json=input_json)
    datadistricts = json.loads(r.text)
    return makegeojson(data=datadistricts)

@app.route('/nearcoordinates', methods=['POST'])
def nearcoordinates():
    input_json = request.get_json(force=True)
    r = requests.post("http://connector:8000/pointInDistrict", json=input_json)
    datadistrict = json.loads(r.text)
    districtID = datadistrict[0]["idSpatial"]

    if districtID in centralDistricts:
        if input_json['database'] == 0:
            distance = 750
        elif input_json['database'] == 1:
            distance = 1500
        elif input_json['database'] == 3:
            distance = 500
        else:
            distance = 500
    else:
        if input_json['database'] == 0:
            distance = 500
        elif input_json['database'] == 1:
            distance = 1500
        elif input_json['database'] == 3:
            distance = 300
        else:
            distance = 500
    input_json["distance"] = distance
    input_json["database"] = 2
    r = requests.post("http://connector:8000/nearcoordinatesfullinfo", json=input_json)
    if r.text == '[]':
        return '[]' 
    datadistricts = json.loads(r.text)
    #return datadistricts
    return {"data":makegeojson(data=datadistricts), "radius": distance}


def create_hexagons(data, hexagone_size):
        polylines_list = []
        sub_geoJson = data['geometry']
        hexagons = []
        #hexagons = [h3.polyfill(shapely.geometry.mapping(x)) for x in list(shapely.geometry.loads(sub_geoJson), hexagone_size)]
        if sub_geoJson['type'] == 'Polygon':
            hexagons = list(h3.polyfill(sub_geoJson, hexagone_size))
        else:
            for i in sub_geoJson['coordinates']:
                sub_sub = {"type": "Polygon", "coordinates": i}
                hexagons.extend(list(h3.polyfill(sub_sub, hexagone_size)))

        polylines = []
        for hex in hexagons:
            polygons = h3.h3_set_to_multi_polygon([hex], geo_json=False)
            outlines = [loop for polygon in polygons for loop in polygon]
            polyline = [outline + [outline[0]] for outline in outlines][0]
            polylines.append(polyline)

            polylines_list.append(polylines)
        
        return hexagons

#Функция для отрисовки гексагонов на карте в пределах выбранных районов
def print_hexagones(data, hexagone_size):
    polylines_list = []
    #maps, polygons_hex, polylines = self.create_hexagons(maps, df_target_borders.iloc[0]['geometry'])
    for i in range(len(data['features'])):
        polylinet = create_hexagons(data['features'][i],
                                    hexagone_size=hexagone_size)
        polylines_list.extend(polylinet)
    return polylines_list

    #print('list_ken', len(self.big_polygons_hex_list_regions), len(self.big_polygons_hex_list_district))


@app.route('/hexForDistricts', methods=['POST'])
def hexForDistricts():
    input_json = request.get_json(force=True)
    r = requests.post("http://connector:8000/districtsfullinfo", json=input_json)
    datadistricts = json.loads(r.text)
    geojson = makegeojson(data=datadistricts)
    return print_hexagones(geojson, hexagone_size=input_json['hexagone_size'])

'''
{
    "IDsource": ["район Ивановское", "Бабушкинский район"],
  	"hexagone_size": 9
}
'''

def change_schools_workload(dist_school_number, dist_school_load, old_number, old_capacity, new_number, new_capacity):
    total_workload = dist_school_number * dist_school_load
    school_old_workload = (old_number / old_capacity * 100)
    without_one_school_workload = total_workload - school_old_workload
    school_new_workload = ((old_number + new_number) / (old_capacity +new_capacity) * 100)
    total_workload = (without_one_school_workload + school_new_workload) / dist_school_number
    return total_workload

def get_provision_flag(type_t, districi_id, min_ob_index):
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

    zone_3 = ['relation/181288', 'relation/380702', 'relation/380703', 'relation/380704', 'relation/380705',
              'relation/380706', 'relation/380707', 'relation/380708', 'relation/445275', 'relation/445278',
              'relation/445284', 'relation/445285', 'relation/446082', 'relation/446083', 'relation/446084',
              'relation/446085', 'relation/446116', 'relation/446117', 'relation/455203', 'relation/455208',
              'relation/455451', 'relation/531264', 'relation/531287', 'relation/548619', 'relation/574667',
              'relation/950639', 'relation/950658', 'relation/951336', 'relation/1255563', 'relation/1255576',
              'relation/1255577', 'relation/1255602', 'relation/1257403', 'relation/1257455', 'relation/1320371',
              'relation/1320424', 'relation/1320510', 'relation/1320566', 'relation/1320570', 'relation/1668007',
              'relation/1693596', 'relation/1693661', 'relation/1693667', 'relation/1693672', 'relation/1703093',
              'relation/1703095', 'relation/2092922', 'relation/2092924', 'relation/2092925', 'relation/2092927',
              'relation/2092928', 'relation/2092929', 'relation/2092931']

    school_zone_1 = 105
    school_zone_2 = 112
    school_zone_3 = 124
    kinder_zone_1 = 46
    kinder_zone_2 = 55
    kinder_zone_3 = 63

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

    if is_min_ob == 1:
        return True
    else:
        return False

def change_district_statistic(districts_json):

    dist_list = []
    for i in districts_json:
        object_dist = districts_json[i]['dist']
        old_district_school_capacity = object_dist['schoolprovisionindex'] * object_dist['residentsnumber'] / 1000
        old_district_kinder_capacity = object_dist['kindergartenprovisionindex'] * object_dist['residentsnumber'] / 1000
        old_P = object_dist['actualprovisionindicator']
        old_N = object_dist['residentsnumber']
        old_Q = object_dist['schoolprovisionindex']
        old_D = old_P - (old_N * old_Q) / 1000
        new_district_school_capacity = old_district_school_capacity + districts_json[i].get('school_delta', 0)
        new_district_kinder_capacity = old_district_kinder_capacity + districts_json[i].get('kinder_delta', 0)
        object_dist['residentsnumber'] = object_dist['residentsnumber'] + districts_json[i].get('residents_delta', 0)
        new_schoolprovisionindex = new_district_school_capacity / object_dist['residentsnumber'] * 1000
        new_kindergartenprovisionindex = new_district_kinder_capacity / object_dist['residentsnumber'] * 1000
        schoolprovision = get_provision_flag('s', i, new_schoolprovisionindex)
        kindergartenprovision = get_provision_flag('k', i, new_kindergartenprovisionindex)
        new_N = object_dist['residentsnumber']
        new_D = old_D + districts_json[i].get('students_delta', 0) - districts_json[i].get('school_delta', 0)
        new_Q = int(new_schoolprovisionindex)
        new_P = (new_N * new_Q) / 1000 + new_D
        object_dist['schoolprovisionindex'] = new_schoolprovisionindex
        object_dist['kindergartenprovisionindex'] = new_kindergartenprovisionindex
        object_dist['schoolprovision'] = schoolprovision
        object_dist['kindergartenprovision'] = kindergartenprovision
        object_dist['actualprovisionindicator'] = new_P
        dist_list.append(object_dist)

    return dist_list

@app.route('/sort')
def sort_stat():
    sort_type = ''
    for i in request.values.items():
        sort_type = i[1]

    return stat(sort_type=sort_type)

def get_sorted_key(sort_type):
    if sort_type == "schools":
        return 'Количество школ'
    elif sort_type == 'kinder':
        return 'Количество детских садов'
    elif sort_type == 'medicine':
        return 'Количество мед учреждений'
    elif sort_type == 'residents':
        return 'Количество жителей'
    elif sort_type == 'year':
        return 'Средний год постройки зданий'
    elif sort_type == 'area':
        return 'Площадь (м2)'
    elif sort_type == 'school_index':
        return 'Процент домов,находящихся вне установленной зоны пешей доступности от школ'
    elif sort_type == 'kinder_index':
        return 'Процент домов,находящихся вне установленной зоны пешей доступности от детских садов'
    elif sort_type == 'medicine_index':
        return 'Процент домов,находящихся вне установленной зоны пешей доступности от медицинских учреждений'
    elif sort_type == 'workload':
        return 'Средняя загруженность школ(в процентах)'

#Преобразование данных по районам и округам в папке additional_code ноутбук preparation_for_statistic
@app.route('/stat', methods=['POST', 'GET'])
def stat(dist_list=[], sort_type=''):
    models = {}
    map_for_sorting = {}
    if len(dist_list) > 0:
        for i in dist_list:
            territories = i['namedistrict']
            area = i['area']
            schools_number = i['schoolnumber']
            schools_workload = i['schoolload']
            kindergartens_number = i['kindergartennumber']
            medicine_number = i['medicinenumber']
            buildings_number = i['livingnumber']
            residents_number = i['residentsnumber']
            avg_year = i['avgyear']
            without_schools = i['withoutschools']
            without_kindergartens = i['withoutkindergartens']
            without_medicine = i['withoutmedicine']
            schools_index = i['schoolprovisionindex']
            is_schools_obespech = i['schoolprovision']
            if is_schools_obespech == False:
                is_schools_obespech = 'Нет'
            elif is_schools_obespech == True:
                is_schools_obespech = 'Да'
            kinder_index = i['kindergartenprovisionindex']
            is_kinder_obespech = i['kindergartenprovision']
            if is_kinder_obespech == False:
                is_kinder_obespech = 'Нет'
            elif is_kinder_obespech == True:
                is_kinder_obespech = 'Да'

            min_school_obespech = i['targetprovisionindicator']
            current_school_obespech = i['actualprovisionindicator']
            density = i['density']

            models[territories] = {'Площадь (м2)': area,
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
                                      'Удовлетворяет ли количество мест детских садах нормативам': is_kinder_obespech,
                                      'Целевой показатель минимально допустимого уровня обеспеченности населения школами': min_school_obespech,
                                      'Фактический показатель минимально допустимого уровня обеспеченности населения школами': current_school_obespech,
                                      'Плотность жилой застройки': density}

            if sort_type != '':
                sorted_key = get_sorted_key(sort_type)
                map_for_sorting[territories] = models[territories][sorted_key]

    else:
        models['Список выбранных территорий'] = 'Территории не выбраны'

    if sort_type != '':
        sorted_models = {}
        map_for_sorting = dict(sorted(map_for_sorting.items(), key=lambda x: x[1]))
        for i in map_for_sorting:
            sorted_models[i] = models[i]
        models = sorted_models
    print(models['район Вешняки'])
    models = json2html.convert(json=models)

    return render_template('stat.html', json_obj=models)

@app.route('/checkchanges', methods=['POST'])
def changes():
    #input_json = request.get_json(force=True)
    input_json = [
        {
            "id": 1,
            "type": "Школа",
            "Номинальная вместимость": -200,
            "Количество учеников": 888
        },
        {
            "id": 768,
            "type": "Школа",
            "Номинальная вместимость": 25000000,
            "Количество учеников": 50
        },
        {
            "id": 456,
            "type": "Жилое",
            "Количество свободных школ": 1,
            "Количество взрослых": 111,
        },
        {
            "id": 3,
            "type": "Детский сад",
            "Номинальная вместимость": 111,
        }
 ]
    schools_list_id = []
    schools_json = []
    buildings_list_id = []
    buildings_json = []
    kinder_list_id = []
    kinder_json = []
    for i in input_json:
        if i['type'] == 'Школа':
            schools_list_id.append(i['id'])
            schools_json.append(i)
        if i['type'] == 'Жилое':
            buildings_list_id.append(i['id'])
            buildings_json.append(i)
        if i['type'] == 'Детский сад':
            kinder_list_id.append(i['id'])
            kinder_json.append(i)
    print(schools_list_id, buildings_list_id, kinder_list_id)
    schools_post_json = {
    "database": 0,
    "arrayID" : schools_list_id
}
    districts_dict = {}
    #Обрабатываем все школы
    schools_object = requests.post("http://127.0.0.1:8008/buildingID", json=schools_post_json).json()
    for i in range(len(schools_object)):
        object_dist_id = schools_object[i]['iddistrict']
        if object_dist_id in districts_dict:
            object_dist = districts_dict[object_dist_id]['dist']
            school_total_capacity_delta = districts_dict[object_dist_id]['school_delta']
            school_total_students_delta = districts_dict[object_dist_id]['students_delta']
        else:
            post_json_dist = {'IDsource': [object_dist_id]}
            object_dist = requests.post("http://127.0.0.1:8008/districtsID", json=post_json_dist).json()[0]
            school_total_capacity_delta = 0
            school_total_students_delta = 0
            districts_dict[object_dist_id] = {}

        object_dist['schoolload'] = change_schools_workload(object_dist['schoolnumber'], object_dist['schoolload'],
                                schools_object[i]['currentworkload'], schools_object[i]['calculatedworkload'],
                                schools_json[i].get("Количество учеников", 0), schools_json[i].get("Номинальная вместимость", 0))
        school_total_capacity_delta += schools_json[i].get("Номинальная вместимость", 0)
        school_total_students_delta += schools_json[i].get("Количество учеников", 0)


        districts_dict[object_dist_id]['dist'] = object_dist
        districts_dict[object_dist_id]['school_delta'] = school_total_capacity_delta


    #Обрабатываем все детские сады
    kinder_post_json = {
            "database": 3,
            "arrayID": kinder_list_id
        }
    kinder_object = requests.post("http://127.0.0.1:8008/buildingID", json=kinder_post_json).json()
    for i in range(len(kinder_object)):
        object_dist_id = kinder_object[i]['iddistrict']
        if object_dist_id in districts_dict:
            object_dist = districts_dict[object_dist_id]['dist']
            kinder_total_capacity_delta = districts_dict[object_dist_id].get('kinder_delta', 0)
        else:
            post_json_dist = {'IDsource': [object_dist_id]}
            object_dist = requests.post("http://127.0.0.1:8008/districtsID", json=post_json_dist).json()[0]
            kinder_total_capacity_delta = 0
            districts_dict[object_dist_id] = {}

        kinder_total_capacity_delta += kinder_json[i].get("Номинальная вместимость", 0)
        districts_dict[object_dist_id]['dist'] = object_dist
        districts_dict[object_dist_id]['kinder_delta'] = kinder_total_capacity_delta



    #Обрабатываем все жилые здания
    building_post_json = {
            "database": 2,
            "arrayID": buildings_list_id
        }
    building_object = requests.post("http://127.0.0.1:8008/buildingID", json=building_post_json).json()
    for i in range(len(building_object)):
        object_dist_id = building_object[i]['iddistrict']
        if object_dist_id in districts_dict:
            object_dist = districts_dict[object_dist_id]['dist']
            residents_total_capacity_delta = districts_dict[object_dist_id].get('residents_delta', 0)
        else:
            post_json_dist = {'IDsource': [object_dist_id]}
            object_dist = requests.post("http://127.0.0.1:8008/districtsID", json=post_json_dist).json()[0]
            districts_dict[object_dist_id] = {}
            residents_total_capacity_delta = 0

        building_object[i]['freeschools'] += buildings_json[i]['Количество свободных школ']
        residents_total_capacity_delta += buildings_json[i]["Количество взрослых"]
        districts_dict[object_dist_id]['dist'] = object_dist
        districts_dict[object_dist_id]['residents_delta'] = residents_total_capacity_delta

    #print(districts_dict)
    dist_list = change_district_statistic(districts_dict)
    stat(dist_list)

    return 1

'''
[
{
    "adress":"Российская Федерация, город Москва, внутригородская территория муниципальный округ Зябликово, улица Мусы Джалиля, дом 29, корпус 2",
    "spec": true,
    "type": "Школа",
    "Номинальная вместимость": 7696
 },
 {
    "adress": "Российская Федерация, город Москва, внутригородская территория муниципальный округ Зябликово, улица Мусы Джалиля, дом 6, корпус 3",
    "spec": false,
    "type":"Школа",
    "Количество учеников":3934},
 {
    "adress": "Российская Федерация, город Москва, внутригородская территория муниципальный округ Орехово-Борисово Северное, Борисовский проезд, дом 13",
    "type":"Школа",
    "Номинальная вместимость":-1
 }
  {
    "adress": "Российская Федерация, город Москва, внутригородская территория муниципальный округ Орехово-Борисово Северное, Борисовский проезд, дом 13",
    "type":"Жилое",
    "Свободных школ в радиусе доступности":-1
 }
 ]
'''

if __name__ == '__main__':
    #app.run(debug=True, host='0.0.0.0')
    changes()