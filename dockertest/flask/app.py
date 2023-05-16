from flask import Flask
from flask import render_template, request
import requests
from utils import dictfromdatabase, notUsedTypes
import json
import h3
app = Flask(__name__)

@app.route('/hello_sasha')
def hello_sasha():
    return 'Hello, Sasha! This is our diploma. CRY!'

@app.route('/hello_vanya')
def hello_vanya():
    return 'Hello, Vanya! The server is working. The reason you here is not I have dropped the server'

@app.route('/main_page')
def hello_world():
    return render_template('main_page.html', user="test")

@app.route('/')
def basic_page():
    return render_template('mainn.html')

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
    input_json["distance"] = 500
    input_json["database"] = 2
    r = requests.post("http://connector:8000/nearcoordinatesfullinfo", json=input_json)
    if r.text == '[]':
        return '[]' 
    datadistricts = json.loads(r.text)
    #return datadistricts
    return makegeojson(data=datadistricts)


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

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')