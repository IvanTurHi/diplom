
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from toPostgresDB import db_start
from toMongoDB import MongoDB
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dictDatabases = {
    0: 'eduBuildings', #Школы
    1: 'medBuildings',
    2: 'livingBuildings',
    3: 'eduBuildings' #Детские сады
}
dictfields = {
    0: 'schoolnumber', #Школы
    1: 'medicineNumber',
    2: 'livingNumber',
    3: 'kindergartenNumber' #Детские сады
}

#id 1531 - жилой, удалить из обоих баз --удалено
def makeArrayIDspatial(data):
    return [i['idspatial'] for i in data]

def schooltype():
    return " and t.nameType = 'Школа' "

def kindergartentype():
    return " and t.nameType = 'Детский сад' "

@app.get("/counties")
async def counties():
    t = db_start()
    return JSONResponse(content=t.getCounties(), status_code=200)

@app.get("/countiesname")
async def countiesname():
    t = db_start()
    return [x['namecounty'] for x in t.getCounties()]

@app.get("/districts")
async def districts():
    t = db_start()
    return t.getDistricts()

@app.get("/districtsname")
async def districtsname():
    t = db_start()
    return {x['namedistrict']:x['namedistrict'] for x in t.getDistricts()}

@app.get("/districtcountyname")
async def districtcountyname():
    t = db_start()
    result = {}
    for i in t.getDistricts():
        if i['namecounty'] not in result.keys():
            result[i['namecounty']] = [i['namedistrict']]
        else:
            result[i['namecounty']].append(i['namedistrict'])
    return result

@app.post("/buildingin")
async def schoolsin(request: Request):
    jsonbody = await request.json()
    selecttype = ''
    if jsonbody['database'] == 0:
        selecttype = schooltype()
    elif jsonbody['database'] == 3:
        selecttype = kindergartentype()
    database = dictDatabases[jsonbody['database']]
    t = db_start()
    if jsonbody['isCounty']:
        return JSONResponse(content=t.getInCounty(jsonbody['IDsource'], database, selecttype), status_code=200)
    else:
        return JSONResponse(content=t.getInDistrict(jsonbody['IDsource'], database, selecttype), status_code=200)
'''
{
    "IDsource": "relation/1299013",
  	"isCounty": false,
  	"database": 1
}
'''
@app.post("/buildingID")
async def schoolsin(request: Request):
    jsonbody = await request.json()
    database = dictDatabases[jsonbody['database']]
    t = db_start()
    return JSONResponse(content=t.getByID(jsonbody['arrayID'], database), status_code=200)
'''
{
  	"database": 1,
  	"arrayID" : [1,2,3]
}
'''

@app.post("/buildingfullinfo")
async def schoolsfull(request: Request):
    jsonbody = await request.json()
    selecttype = ''
    if jsonbody['database'] == 0:
        selecttype = schooltype()
    elif jsonbody['database'] == 3:
        selecttype = kindergartentype()
    database = dictDatabases[jsonbody['database']]
    t = db_start()
    if jsonbody['isCounty']:
        table = t.getInCounty(jsonbody['IDsource'], database, selecttype)
    else:
        table = t.getInDistrict(jsonbody['IDsource'], database, selecttype)
    listID = makeArrayIDspatial(table)
    t = MongoDB()
    tableMongo = t.getCentroidAndDAtaByID(listID, database)
    result = []
    for p, m in zip(table, tableMongo):
        res = dict(p, **m)
        result.append(res)
    
    return JSONResponse(content=result, status_code=200)
'''
{
    "IDsource": ["район Ивановское"],
  	"isCounty": false,
  	"database": 1
}
'''

@app.post("/districtsfullinfo")
async def schoolsfull(request: Request):
    jsonbody = await request.json()
    t = db_start()
    table = t.getCountiesByID(jsonbody['IDsource'])
    listID = makeArrayIDspatial(table)
    t = MongoDB()
    tableMongo = t.getCentroidAndDAtaByID(listID, 'districts')
    result = []
    for p, m in zip(table, tableMongo):
        res = dict(p, **m)
        result.append(res)
    return JSONResponse(content=result, status_code=200)

@app.post("/mongolist")
async def mongolist(request: Request):
    jsonbody = await request.json()
    database = dictDatabases[jsonbody['database']]
    listID = jsonbody['listID']
    t = MongoDB()
    return JSONResponse(content=t.getCentroidAndDAtaByID(listID, database), status_code=200)
'''
{
	"database": 0,
	"listID": [1, 2]
}
'''

@app.get("/mongocollections")
async def mongocollections():
    t = MongoDB()
    return JSONResponse(content=t.getAllCollections(), status_code=200)

@app.post("/incoordinates")
async def incoordinates(request: Request):
    jsonbody = await request.json()
    database = dictDatabases[jsonbody['database']]
    Slat = jsonbody['Slat']
    Nlat = jsonbody['Nlat']
    Wlon = jsonbody['Wlon']
    Elon = jsonbody['Elon']
    poly = { "type" : "Polygon", "coordinates" : [[
        [Elon, Slat],
        [Elon, Nlat],
        [Wlon, Nlat],
        [Wlon, Slat],
        [Elon, Slat]]] }
    t = MongoDB()
    return JSONResponse(content=t.getwithincoordinates(poly, database), status_code=200)

'''
{
    "Wlon": 37.93,
    "Elon": 37.95,
    "Nlat": 55.69,
    "Slat": 55.74,
    "database": 1
}
'''

@app.post("/nearcoordinates")
async def nearcoordinates(request: Request):
    jsonbody = await request.json()
    database = dictDatabases[jsonbody['database']]
    lat = jsonbody['lat']
    lon = jsonbody['lon']
    distance = jsonbody['distance']
    poly = { "type" : "Point", "coordinates" : [lon, lat] }
    t = MongoDB()
    return JSONResponse(content=t.getnearcoordinates(poly, distance, database), status_code=200)
'''
{
    "lon": 37.93,
    "lat": 55.7,
 	"distance": 100,
    "database": 1
}
'''
@app.post("/nearcoordinatesdistance")
async def nearcoordinatesdistance(request: Request):
    jsonbody = await request.json()
    database = dictDatabases[jsonbody['database']]
    lat = jsonbody['lat']
    lon = jsonbody['lon']
    distance = jsonbody.get('distance', 1000)
    poly = { "type" : "Point", "coordinates" : [lon, lat] }
    t = MongoDB()
    return JSONResponse(content=t.getnearcoordinateswithdistance(poly, distance, database), status_code=200)
'''
{
    "lon": 37.93,
    "lat": 55.7,
 	"distance": 1000,
    "database": 2
}
distance is optional and equal to 1000 m dy default
'''

@app.post("/nearcoordinatesfullinfo")
async def nearcoordinates(request: Request):
    jsonbody = await request.json()
    database = dictDatabases[jsonbody['database']]
    lat = jsonbody['lat']
    lon = jsonbody['lon']
    distance = jsonbody['distance']
    poly = { "type" : "Point", "coordinates" : [lon, lat] }
    t = MongoDB()
    spatialInfo = t.getnearcoordinates(poly, distance, database)
    arrayID = [i['idSpatial'] for i in spatialInfo]
    db = db_start()
    table = db.getBySpatialID(arrayID, database)
    result = []
    for p, m in zip(table, spatialInfo):
        res = dict(p, **m)
        result.append(res)
    return JSONResponse(content=result, status_code=200)