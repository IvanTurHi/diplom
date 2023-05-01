import psycopg2
import psycopg2.extras
import os

class MyError(Exception):
    def __init___(self, args):
        Exception.__init__(self, "my exception was raised with arguments {0}".format(args))
        self.args = args

class db_start(object):

    def __init__(self):
        self.__conn = psycopg2.connect(database=os.environ['POSTGRES_DB'], user=os.environ['POSTGRES_USER'],
                                password=os.environ['POSTGRES_PASSWORD'], host='postgres', port=5432)
        #self.__conn = psycopg2.connect(database='test', user='admin',
        #                        password='admin', host='postgres', port=5432)
        self.__cur = self.__conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

    def _returnDict(self):
        row=self.__cur.fetchall()
        if row is not None:
            return(row)
        else:
            raise MyError("no data in DB")
        

    def getCounts(self):
        self.__cur.execute("select * from counts")
        return self._returnDict()
       
    def getDistricts(self):
        self.__cur.execute("select * from districts")
        return self._returnDict()
        
    def getInCount(self, count, database):
        SQLquery = """select t.* from """ + database + """ t, districts d
            where d.iddistrict = t.iddistrict and d.idcount = %s order by buildID"""
        self.__cur.execute(SQLquery, (count, ))
        return self._returnDict()
        
    def getInDistrict(self, district, database):
        SQLquery = """select t.* from """ + database + """ t
            where t.iddistrict = %s order by buildID"""
        self.__cur.execute(SQLquery, (district, ))
        return self._returnDict()
        
    def getByID(self, arrayID, database):
        SQLquery = """select t.* from """ + database + """ t
            where t.buildid in %s"""
        self.__cur.execute(SQLquery, (tuple(arrayID), ))
        return self._returnDict()