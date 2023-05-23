import psycopg2
import psycopg2.extras
import os
def schooltype():
    return " and t.nameType = 'Школа' "

class MyError(Exception):
    def __init___(self, args):
        Exception.__init__(self, "my exception was raised with arguments {0}".format(args))
        self.args = args

class db_start(object):

    def __init__(self):
        #self.__conn = psycopg2.connect(database=os.environ['POSTGRES_DB'], user=os.environ['POSTGRES_USER'],
        #                       password=os.environ['POSTGRES_PASSWORD'], host='postgres', port=5432)
        self.__conn = psycopg2.connect(database='test', user='admin',
                                password='admin', host='postgres', port=5432)
        self.__cur = self.__conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

    def _returnDict(self):
        row=self.__cur.fetchall()
        if row is not None:
            return(row)
        else:
            raise MyError("no data in DB")
        

    def getCounties(self):
        self.__cur.execute("""SELECT namecounty, area, schoolnumber, schoolload,
            kindergartennumber, medicinenumber, livingnumber, residentsnumber, avgyear, withoutschools,
            withoutkindergartens, withoutmedicine from counties ORDER BY namecounty""")
        return self._returnDict()
       
    def getDistricts(self):
        self.__cur.execute("""SELECT d.namedistrict, c.namecounty, d.area, d.schoolnumber, d.schoolload,
            d.kindergartennumber, d.medicinenumber, d.livingnumber, d.residentsnumber, d.avgyear, d.withoutschools,
            d.withoutkindergartens, d.withoutmedicine, d.schoolProvisionIndex, 
            d.kindergartenProvisionIndex, d.schoolProvision, d.kindergartenProvision from counties c, districts d where c.idCount = d.idCount
            order by c.namecounty, d.namedistrict""")
        return self._returnDict()
        
    def getInCounty(self, county, database, selecttype = ''):
        SQLquery = """SELECT t.* from """ + database + """ t, districts d
            where d.iddistrict = t.iddistrict and d.idcount = %s """ + selecttype + """ ORDER BY idSpatial"""
        self.__cur.execute(SQLquery, (county, ))
        return self._returnDict()
        
    def getInDistrict(self, district, database, selecttype = ''):
        if database == 'eduBuildings' and selecttype == schooltype():
            SQLquery = """SELECT t.*, round(currentworkload::float/calculatedworkload * 100) stnumber from """ + database + """ t, districts d
                where d.iddistrict = t.iddistrict and d.nameDistrict in %s """ + selecttype + """ ORDER BY idSpatial"""
        else:
            SQLquery = """SELECT t.* from """ + database + """ t, districts d
                where d.iddistrict = t.iddistrict and d.nameDistrict in %s """ + selecttype + """ ORDER BY idSpatial"""
        self.__cur.execute(SQLquery, (tuple(district), ))
        return self._returnDict()
        
    def getBySpatialID(self, arrayID, database):
        SQLquery = """SELECT t.* from """ + database + """ t
            where t.buildid in %s ORDER BY idSpatial"""
        self.__cur.execute(SQLquery, (tuple(arrayID), ))
        return self._returnDict()
    
    def getCountiesByID(self, nameID):
        SQLquery = """SELECT namedistrict, area, idspatial,schoolnumber, schoolload,
            kindergartennumber, medicinenumber, livingnumber, residentsnumber, avgyear, withoutschools,
            withoutkindergartens, withoutmedicine, schoolProvisionIndex, 
            kindergartenProvisionIndex, schoolProvision, kindergartenProvision from districts where nameDistrict in %s ORDER BY idSpatial"""
        self.__cur.execute(SQLquery, (tuple(nameID), ))
        return self._returnDict()