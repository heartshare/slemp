# coding: utf-8

import re
import os
import sys

sys.path.append("/usr/local/lib/python2.7/site-packages")


class mysqlDb:
    __DB_PASS = None
    __DB_USER = 'root'
    __DB_PORT = 3306
    __DB_HOST = 'localhost'
    __DB_CONN = None
    __DB_CUR = None
    __DB_ERR = None
    __DB_CNF = '/etc/my.cnf'

    def __Conn(self):
        '''Connect to MYSQL database'''
        try:
            import slemp
            socket = '/tmp/mysql.sock'
            try:
                import MySQLdb
            except Exception, ex:
                self.__DB_ERR = ex
                return False
            try:
                myconf = slemp.readFile(self.__DB_CNF)
                rep = "port\s*=\s*([0-9]+)"
                self.__DB_PORT = int(re.search(rep, myconf).groups()[0])
            except:
                self.__DB_PORT = 3306
            # print self.__DB_PASS
            #self.__DB_PASS = slemp.M('config').where('id=?', (1,)).getField('mysql_root')
            try:
                self.__DB_CONN = MySQLdb.connect(host=self.__DB_HOST, user=self.__DB_USER, passwd=self.__DB_PASS,
                                                 port=self.__DB_PORT, charset="utf8", connect_timeout=1, unix_socket=socket)
            except MySQLdb.Error, e:
                self.__DB_HOST = '127.0.0.1'
                self.__DB_CONN = MySQLdb.connect(host=self.__DB_HOST, user=self.__DB_USER, passwd=self.__DB_PASS,
                                                 port=self.__DB_PORT, charset="utf8", connect_timeout=1, unix_socket=socket)
            self.__DB_CUR = self.__DB_CONN.cursor()
            return True
        except MySQLdb.Error, e:
            self.__DB_ERR = e
            return False

    def setDbConf(self, conf):
        self.__DB_CNF = conf

    def setPwd(self, pwd):
        self.__DB_PASS = pwd

    def getPwd(self):
        return self.__DB_PASS

    def execute(self, sql):
        # Execute the SQL statement to return the affected rows
        if not self.__Conn():
            return self.__DB_ERR
        try:
            result = self.__DB_CUR.execute(sql)
            self.__DB_CONN.commit()
            self.__Close()
            return result
        except Exception, ex:
            return ex

    def query(self, sql):
        # Execute the SQL statement to return the dataset
        if not self.__Conn():
            return self.__DB_ERR
        try:
            self.__DB_CUR.execute(sql)
            result = self.__DB_CUR.fetchall()
            # Convert tuple to list
            data = map(list, result)
            self.__Close()
            return data
        except Exception, ex:
            return ex

    # close the connection
    def __Close(self):
        self.__DB_CUR.close()
        self.__DB_CONN.close()
