import psycopg2
import psycopg2.extras
import os

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
        

    def getCounts(self):
        self.__cur.execute("""SELECT namecount, area, schoolnumber, schoolload,
            kindergartennumber, medicinenumber, livingnumber, residentsnumber, avgyear, withoutschools,
            withoutkindergartens, withoutmedicine from counts ORDER BY namecount""")
        return self._returnDict()
       
    def getDistricts(self):
        self.__cur.execute("""SELECT d.namedistrict, c.namecount, d.area, d.schoolnumber, d.schoolload,
            d.kindergartennumber, d.medicinenumber, d.livingnumber, d.residentsnumber, d.avgyear, d.withoutschools,
            d.withoutkindergartens, d.withoutmedicine, d.schoolProvisionIndex, 
            d.kindergartenProvisionIndex, d.schoolProvision, d.kindergartenProvision from counts c, districts d where c.idCount = d.idCount
            order by c.namecount, d.namedistrict""")
        return self._returnDict()
        
    def getInCount(self, count, database, selecttype = ''):
        SQLquery = """SELECT t.* from """ + database + """ t, districts d
            where d.iddistrict = t.iddistrict and d.idcount = %s """ + selecttype + """ ORDER BY idSpatial"""
        self.__cur.execute(SQLquery, (count, ))
        return self._returnDict()
        
    def getInDistrict(self, district, database, selecttype = ''):
        SQLquery = """SELECT t.* from """ + database + """ t, districts d
            where d.iddistrict = t.iddistrict and d.nameDistrict in %s """ + selecttype + """ ORDER BY idSpatial"""
        self.__cur.execute(SQLquery, (tuple(district), ))
        return self._returnDict()
        
    def getByID(self, arrayID, database):
        SQLquery = """SELECT t.* from """ + database + """ t
            where t.buildid in %s ORDER BY idSpatial"""
        self.__cur.execute(SQLquery, (tuple(arrayID), ))
        return self._returnDict()
    
    def getCountsByID(self, nameID):
        SQLquery = """SELECT namedistrict, area, idspatial,schoolnumber, schoolload,
            kindergartennumber, medicinenumber, livingnumber, residentsnumber, avgyear, withoutschools,
            withoutkindergartens, withoutmedicine, schoolProvisionIndex, 
            kindergartenProvisionIndex, schoolProvision, kindergartenProvision from districts where nameDistrict in %s ORDER BY idSpatial"""
        self.__cur.execute(SQLquery, (tuple(nameID), ))
        return self._returnDict()