# coding: utf-8


import sqlite3
import os


class Sql():
    #------------------------------
    # Database operation class For sqlite3
    #------------------------------
    __DB_FILE = None              # database file
    __DB_CONN = None              # database connection object
    __DB_TABLE = ""               # The name of the table being manipulated
    __OPT_WHERE = ""              # where condition
    __OPT_LIMIT = ""              # limit condition
    __OPT_ORDER = ""              # order condition
    __OPT_FIELD = "*"             # field condition
    __OPT_PARAM = ()              # where value

    def __init__(self):
        self.__DB_FILE = 'data/default.db'

    def __GetConn(self):
        # get database object
        try:
            if self.__DB_CONN == None:
                self.__DB_CONN = sqlite3.connect(self.__DB_FILE)
        except Exception, ex:
            return "error: " + str(ex)

    def dbfile(self, name):
        self.__DB_FILE = 'data/' + name + '.db'
        return self

    def dbPos(self, path, name):
        self.__DB_FILE = path + '/' + name + '.db'
        return self

    def table(self, table):
        # set table name
        self.__DB_TABLE = table
        return self

    def where(self, where, param):
        # WHERE condition
        if where:
            self.__OPT_WHERE = " WHERE " + where
            self.__OPT_PARAM = param
        return self

    def order(self, order):
        # ORDER condition
        if len(order):
            self.__OPT_ORDER = " ORDER BY " + order
        return self

    def limit(self, limit):
        # LIMIT condition
        if len(limit):
            self.__OPT_LIMIT = " LIMIT " + limit
        return self

    def field(self, field):
        # FIELD condition
        if len(field):
            self.__OPT_FIELD = field
        return self

    def select(self):
        # query dataset
        self.__GetConn()
        try:
            sql = "SELECT " + self.__OPT_FIELD + " FROM " + self.__DB_TABLE + \
                self.__OPT_WHERE + self.__OPT_ORDER + self.__OPT_LIMIT
            result = self.__DB_CONN.execute(sql, self.__OPT_PARAM)
            data = result.fetchall()
            # Construct character song series
            if self.__OPT_FIELD != "*":
                field = self.__OPT_FIELD.split(',')
                tmp = []
                for row in data:
                    i = 0
                    tmp1 = {}
                    for key in field:
                        tmp1[key] = row[i]
                        i += 1
                    tmp.append(tmp1)
                    del(tmp1)
                data = tmp
                del(tmp)
            else:
                # Convert tuple to list
                tmp = map(list, data)
                data = tmp
                del(tmp)
            self.__close()
            return data
        except Exception, ex:
            return "error: " + str(ex)

    def getField(self, keyName):
        # Retrieve the specified field
        result = self.field(keyName).select()
        if len(result) == 1:
            return result[0][keyName]
        return result

    def setField(self, keyName, keyValue):
        # Update the specified field
        return self.save(keyName, (keyValue,))

    def find(self):
        # Take a row of data
        result = self.limit("1").select()
        if len(result) == 1:
            return result[0]
        return result

    def count(self):
        # Number of lines
        key = "COUNT(*)"
        data = self.field(key).select()
        try:
            return int(data[0][key])
        except:
            return 0

    def add(self, keys, param):
        # Insert data
        self.__GetConn()
        self.__DB_CONN.text_factory = str
        try:
            values = ""
            for key in keys.split(','):
                values += "?,"
            values = self.checkInput(values[0:len(values) - 1])
            sql = "INSERT INTO " + self.__DB_TABLE + \
                "(" + keys + ") " + "VALUES(" + values + ")"
            result = self.__DB_CONN.execute(sql, param)
            id = result.lastrowid
            self.__close()
            self.__DB_CONN.commit()
            return id
        except Exception, ex:
            return "error: " + str(ex)

    def checkInput(self, data):
        if not data:
            return data
        if type(data) != str:
            return data
        checkList = [
            {'d': '<', 'r': '＜'},
            {'d': '>', 'r': '＞'},
            {'d': '\'', 'r': '‘'},
            {'d': '"', 'r': '“'},
            {'d': '&', 'r': '＆'},
            {'d': '#', 'r': '＃'},
            {'d': '<', 'r': '＜'}
        ]
        for v in checkList:
            data = data.replace(v['d'], v['r'])
        return data

    def addAll(self, keys, param):
        # Insert data
        self.__GetConn()
        self.__DB_CONN.text_factory = str
        try:
            values = ""
            for key in keys.split(','):
                values += "?,"
            values = values[0:len(values) - 1]
            sql = "INSERT INTO " + self.__DB_TABLE + \
                "(" + keys + ") " + "VALUES(" + values + ")"
            result = self.__DB_CONN.execute(sql, param)
            return True
        except Exception, ex:
            return "error: " + str(ex)

    def commit(self):
        self.__close()
        self.__DB_CONN.commit()

    def save(self, keys, param):
        # Update data
        self.__GetConn()
        self.__DB_CONN.text_factory = str
        try:
            opt = ""
            for key in keys.split(','):
                opt += key + "=?,"
            opt = opt[0:len(opt) - 1]
            sql = "UPDATE " + self.__DB_TABLE + " SET " + opt + self.__OPT_WHERE

            import slemp
            slemp.writeFile('/tmp/test.pl', sql)

            # Handling splice WHERE and UPDATE parameters
            tmp = list(param)
            for arg in self.__OPT_PARAM:
                tmp.append(arg)
            self.__OPT_PARAM = tuple(tmp)
            result = self.__DB_CONN.execute(sql, self.__OPT_PARAM)
            self.__close()
            self.__DB_CONN.commit()
            return result.rowcount
        except Exception, ex:
            return "error: " + str(ex)

    def delete(self, id=None):
        # delete data
        self.__GetConn()
        try:
            if id:
                self.__OPT_WHERE = " WHERE id=?"
                self.__OPT_PARAM = (id,)
            sql = "DELETE FROM " + self.__DB_TABLE + self.__OPT_WHERE
            result = self.__DB_CONN.execute(sql, self.__OPT_PARAM)
            self.__close()
            self.__DB_CONN.commit()
            return result.rowcount
        except Exception, ex:
            return "error: " + str(ex)

    def execute(self, sql, param):
        # Execute the SQL statement to return the affected rows
        self.__GetConn()
        # print sql, param
        try:
            result = self.__DB_CONN.execute(sql, param)
            self.__DB_CONN.commit()
            return result.rowcount
        except Exception, ex:
            return "error: " + str(ex)

    def query(self, sql, param):
        # Execute the SQL statement to return the dataset
        self.__GetConn()
        try:
            result = self.__DB_CONN.execute(sql, param)
            # Convert tuple to list
            data = map(list, result)
            return data
        except Exception, ex:
            return "error: " + str(ex)

    def create(self, name):
        # Create data table
        self.__GetConn()
        import slemp
        script = slemp.readFile('data/' + name + '.sql')
        result = self.__DB_CONN.executescript(script)
        self.__DB_CONN.commit()
        return result.rowcount

    def fofile(self, filename):
        # execute script
        self.__GetConn()
        import slemp
        script = slemp.readFile(filename)
        result = self.__DB_CONN.executescript(script)
        self.__DB_CONN.commit()
        return result.rowcount

    def __close(self):
        # Cleanup condition properties
        self.__OPT_WHERE = ""
        self.__OPT_FIELD = "*"
        self.__OPT_ORDER = ""
        self.__OPT_LIMIT = ""
        self.__OPT_PARAM = ()

    def close(self):
        # release resources
        try:
            self.__DB_CONN.close()
            self.__DB_CONN = None
        except:
            pass
