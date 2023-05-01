
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from toPostgresDB import db_start
from toMongoDB import MongoDB

app = FastAPI()

dictDatabases = {
    0: 'eduBuildings',
    1: 'medBuildings',
    2: 'livingBuildings'
}
#id 1531 - жилой, удалить из обоих баз --удалено
def makeArrayIDspatial(data):
    return [i['idspatial'] for i in data]

@app.get("/counts")
async def read_root():
    t = db_start()
    return JSONResponse(content=t.getCounts(), status_code=200)

@app.get("/districts")
async def read_root():
    t = db_start()
    return t.getDistricts()

@app.post("/buildingin")
async def schoolsin(request: Request):
    jsonbody = await request.json()
    database = dictDatabases[jsonbody['database']]
    t = db_start()
    if jsonbody['isCount']:
        return JSONResponse(content=t.getInCount(jsonbody['IDsource'], database), status_code=200)
    else:
        return JSONResponse(content=t.getInDistrict(jsonbody['IDsource'], database), status_code=200)
'''
{
    "IDsource": "relation/1299013",
  	"isCount": false,
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
    database = dictDatabases[jsonbody['database']]
    t = db_start()
    if jsonbody['isCount']:
        table = t.getInCount(jsonbody['IDsource'], database)
    else:
        table = t.getInDistrict(jsonbody['IDsource'], database)
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
    "IDsource": "relation/1299013",
  	"isCount": false,
  	"database": 1
}
'''

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