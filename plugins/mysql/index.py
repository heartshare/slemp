# coding:utf-8

import sys
import io
import os
import time
import subprocess
import re
import json

reload(sys)
sys.setdefaultencoding('utf-8')

sys.path.append(os.getcwd() + "/class/core")
import slemp


app_debug = False
if slemp.isAppleSystem():
    app_debug = True


def getPluginName():
    return 'mysql'


def getPluginDir():
    return slemp.getPluginDir() + '/' + getPluginName()

sys.path.append(getPluginDir() + "/class")
import mysqlDb


def getServerDir():
    return slemp.getServerDir() + '/' + getPluginName()


def getInitDFile():
    if app_debug:
        return '/tmp/' + getPluginName()
    return '/etc/init.d/' + getPluginName()


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False


def getArgs():
    args = sys.argv[2:]

    # print(args)

    # if is_number(args):
    #     args = sys.argv[3:]

    tmp = {}
    args_len = len(args)

    if args_len == 1:
        t = args[0].strip('{').strip('}')
        t = t.split(':')
        tmp[t[0]] = t[1]
    elif args_len > 1:
        for i in range(len(args)):
            t = args[i].split(':')
            tmp[t[0]] = t[1]

    return tmp


def checkArgs(data, ck=[]):
    for i in range(len(ck)):
        if not ck[i] in data:
            return (False, slemp.returnJson(False, 'Parameter: (' + ck[i] + ') no!'))
    return (True, slemp.returnJson(True, 'ok'))


def getConf():
    path = getServerDir() + '/etc/my.cnf'
    return path


def getInitdTpl(version=''):
    path = getPluginDir() + '/init.d/mysql' + version + '.tpl'
    return path


def contentReplace(content):
    service_path = slemp.getServerDir()
    content = content.replace('{$ROOT_PATH}', slemp.getRootDir())
    content = content.replace('{$SERVER_PATH}', service_path)
    content = content.replace('{$SERVER_APP_PATH}', service_path + '/mysql')
    return content


def pSqliteDb(dbname='databases'):
    file = getServerDir() + '/mysql.db'
    name = 'mysql'
    if not os.path.exists(file):
        conn = slemp.M(dbname).dbPos(getServerDir(), name)
        csql = slemp.readFile(getPluginDir() + '/conf/mysql.sql')
        csql_list = csql.split(';')
        for index in range(len(csql_list)):
            conn.execute(csql_list[index], ())
    else:
        # 现有run
        # conn = slemp.M(dbname).dbPos(getServerDir(), name)
        # csql = slemp.readFile(getPluginDir() + '/conf/mysql.sql')
        # csql_list = csql.split(';')
        # for index in range(len(csql_list)):
        #     conn.execute(csql_list[index], ())
        conn = slemp.M(dbname).dbPos(getServerDir(), name)
    return conn


def pMysqlDb():
    db = mysqlDb.mysqlDb()
    db.__DB_CNF = getConf()
    db.setDbConf(getConf())
    db.setPwd(pSqliteDb('config').where(
        'id=?', (1,)).getField('mysql_root'))
    return db


def initDreplace(version=''):
    initd_tpl = getInitdTpl(version)

    initD_path = getServerDir() + '/init.d'
    if not os.path.exists(initD_path):
        os.mkdir(initD_path)

    file_bin = initD_path + '/' + getPluginName()
    if not os.path.exists(file_bin):
        content = slemp.readFile(initd_tpl)
        content = contentReplace(content)
        slemp.writeFile(file_bin, content)
        slemp.execShell('chmod +x ' + file_bin)

    mysql_conf_dir = getServerDir() + '/etc'
    if not os.path.exists(mysql_conf_dir):
        os.mkdir(mysql_conf_dir)

    mysql_conf = mysql_conf_dir + '/my.cnf'
    if not os.path.exists(mysql_conf):
        mysql_conf_tpl = getPluginDir() + '/conf/my' + version + '.cnf'
        content = slemp.readFile(mysql_conf_tpl)
        content = contentReplace(content)
        slemp.writeFile(mysql_conf, content)

    if slemp.getOs() != 'darwin':
        slemp.execShell('chown -R mysql mysql ' + getServerDir())
    return file_bin


def status(version=''):
    data = slemp.execShell(
        "ps -ef|grep mysqld |grep -v grep | grep -v python | awk '{print $2}'")
    if data[0] == '':
        return 'stop'
    return 'start'


def getDataDir():
    file = getConf()
    content = slemp.readFile(file)
    rep = 'datadir\s*=\s*(.*)'
    tmp = re.search(rep, content)
    return tmp.groups()[0].strip()


def binLog():
    args = getArgs()
    conf = getConf()
    con = slemp.readFile(conf)

    if con.find('#log-bin=mysql-bin') != -1:
        if args.has_key('status'):
            return slemp.returnJson(False, '0')
        con = con.replace('#log-bin=mysql-bin', 'log-bin=mysql-bin')
        con = con.replace('#binlog_format=mixed', 'binlog_format=mixed')
        slemp.execShell('sync')
        restart()
    else:
        path = getDataDir()
        if args.has_key('status'):
            dsize = 0
            for n in os.listdir(path):
                if len(n) < 9:
                    continue
                if n[0:9] == 'mysql-bin':
                    dsize += os.path.getsize(path + '/' + n)
            return slemp.returnJson(True, dsize)
        con = con.replace('log-bin=mysql-bin', '#log-bin=mysql-bin')
        con = con.replace('binlog_format=mixed', '#binlog_format=mixed')
        slemp.execShell('sync')
        restart()
        slemp.execShell('rm -f ' + path + '/mysql-bin.*')

    slemp.writeFile(conf, con)
    return slemp.returnJson(True, 'Set successfully!')


def setSkipGrantTables(v):
    '''
    Set whether to verify password
    '''
    conf = getConf()
    con = slemp.readFile(conf)
    if v:
        if con.find('#skip-grant-tables') != -1:
            con = con.replace('#skip-grant-tables', 'skip-grant-tables')
    else:
        con = con.replace('skip-grant-tables', '#skip-grant-tables')
    slemp.writeFile(conf, con)
    return True


def getErrorLog():
    args = getArgs()
    path = getDataDir()
    filename = ''
    for n in os.listdir(path):
        if len(n) < 5:
            continue
        if n == 'error.log':
            filename = path + '/' + n
            break
    # print filename
    if not os.path.exists(filename):
        return slemp.returnJson(False, 'The specified file does not exist!')
    if args.has_key('close'):
        slemp.writeFile(filename, '')
        return slemp.returnJson(False, 'Log cleared')
    info = slemp.getNumLines(filename, 18)
    return slemp.returnJson(True, 'OK', info)


def getShowLogFile():
    file = getConf()
    content = slemp.readFile(file)
    rep = 'slow-query-log-file\s*=\s*(.*)'
    tmp = re.search(rep, content)
    return tmp.groups()[0].strip()


def pGetDbUser():
    if slemp.isAppleSystem():
        user = slemp.execShell(
            "who | sed -n '2, 1p' |awk '{print $1}'")[0].strip()
        return user
    return 'mysql'


def initMysqlData():
    datadir = getDataDir()
    if not os.path.exists(datadir + '/mysql'):
        serverdir = getServerDir()
        user = pGetDbUser()
        cmd = 'cd ' + serverdir + ' && ./scripts/mysql_install_db --user=' + \
            user + ' --basedir=' + serverdir + ' --ldata=' + datadir + ' && chown -R mysql mysql ' + datadir
        slemp.execShell(cmd)
        return 0
    return 1


def initMysql8Data():
    datadir = getDataDir()
    if not os.path.exists(datadir + '/mysql'):
        serverdir = getServerDir()
        user = pGetDbUser()
        cmd = 'cd ' + serverdir + ' && ./bin/mysqld --basedir=' + serverdir + ' --datadir=' + \
            datadir + ' --initialize && chown -R mysql mysql ' + datadir
        slemp.execShell(cmd)
        return 0
    return 1


def initMysqlPwd():
    time.sleep(5)

    serverdir = getServerDir()

    pwd = slemp.getRandomString(16)
    cmd_pass = serverdir + '/bin/mysqladmin -uroot password ' + pwd
    pSqliteDb('config').where('id=?', (1,)).save('mysql_root', (pwd,))
    slemp.execShell(cmd_pass)
    return True


def initMysql8Pwd():
    time.sleep(6)

    import MySQLdb as mdb
    dbconn = mdb.connect('localhost', 'root', '', '')
    dbconn.autocommit(True)
    dbcurr = dbconn.cursor()
    dbcurr.execute('SET NAMES UTF8MB4')

    serverdir = getServerDir()
    pwd = slemp.getRandomString(16)

    # with mysql_native_password
    alter_root_pwd = "flush privileges;\n"
    alter_root_pwd = alter_root_pwd + \
        "alter user 'root'@'localhost' identified by '" + pwd + "';"

    r = dbcurr.execute(alter_root_pwd)

    # slemp.writeFile(tmp_file, alter_root_pwd)
    # cmd_pass = serverdir + '/bin/mysql -uroot -p < ' + tmp_file
    # print slemp.execShell(cmd_pass)
    pSqliteDb('config').where('id=?', (1,)).save('mysql_root', (pwd,))

    return True


def myOp(method):
    import commands
    init_file = initDreplace()
    cmd = init_file + ' ' + method
    try:
        initData = initMysqlData()
        subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True,
                         bufsize=4096, stderr=subprocess.PIPE)
        if initData == 0:
            initMysqlPwd()
        return 'ok'
    except Exception as e:
        return str(e)


def my8cmd(version, method):
    init_file = initDreplace(version)
    cmd = init_file + ' ' + method
    try:
        initData = initMysql8Data()
        if initData == 0:
            setSkipGrantTables(True)
            cmd_init_start = init_file + ' start'
            subprocess.Popen(cmd_init_start, stdout=subprocess.PIPE, shell=True,
                             bufsize=4096, stderr=subprocess.PIPE)
            initMysql8Pwd()

            cmd_init_stop = init_file + ' stop'
            subprocess.Popen(cmd_init_stop, stdout=subprocess.PIPE, shell=True,
                             bufsize=4096, stderr=subprocess.PIPE)
            setSkipGrantTables(False)

            my8cmd(version, method)
        else:
            subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True,
                             bufsize=4096, stderr=subprocess.PIPE)
        return 'ok'
    except Exception as e:
        print(e)

    return 'fail'


def appCMD(version, action):
    if version == '8.0' or version == '5.7':
        return my8cmd(version, action)
    return myOp(action)


def start(version=''):
    return appCMD(version, 'start')


def stop(version=''):
    return appCMD(version, 'stop')


def restart(version=''):
    return appCMD(version, 'restart')


def reload(version=''):
    return appCMD(version, 'reload')


def initdStatus():
    if not app_debug:
        if slemp.isAppleSystem():
            return "Apple Computer does not support"

    initd_bin = getInitDFile()
    if os.path.exists(initd_bin):
        return 'ok'
    return 'fail'


def initdInstall():
    import shutil
    if not app_debug:
        if slemp.isAppleSystem():
            return "Apple Computer does not support"

    mysql_bin = initDreplace()
    initd_bin = getInitDFile()
    shutil.copyfile(mysql_bin, initd_bin)
    slemp.execShell('chmod +x ' + initd_bin)
    slemp.execShell('chkconfig --add ' + getPluginName())
    return 'ok'


def initdUinstall():
    if not app_debug:
        if slemp.isAppleSystem():
            return "Apple Computer does not support"
    slemp.execShell('chkconfig --del ' + getPluginName())
    initd_bin = getInitDFile()
    os.remove(initd_bin)
    return 'ok'


def getMyDbPos():
    file = getConf()
    content = slemp.readFile(file)
    rep = 'datadir\s*=\s*(.*)'
    tmp = re.search(rep, content)
    return tmp.groups()[0].strip()


def setMyDbPos():
    args = getArgs()
    data = checkArgs(args, ['datadir'])
    if not data[0]:
        return data[1]

    s_datadir = getMyDbPos()
    t_datadir = args['datadir']
    if t_datadir == s_datadir:
        return slemp.returnJson(False, 'Same as current storage directory, cannot migrate files!')

    if not os.path.exists(t_datadir):
        slemp.execShell('mkdir -p ' + t_datadir)

    # slemp.execShell('/etc/init.d/mysqld stop')
    stop()
    slemp.execShell('cp -rf ' + s_datadir + '/* ' + t_datadir + '/')
    slemp.execShell('chown -R mysql mysql ' + t_datadir)
    slemp.execShell('chmod -R 755 ' + t_datadir)
    slemp.execShell('rm -f ' + t_datadir + '/*.pid')
    slemp.execShell('rm -f ' + t_datadir + '/*.err')

    path = getServerDir()
    myfile = path + '/etc/my.cnf'
    mycnf = slemp.readFile(myfile)
    slemp.writeFile(path + '/etc/my_backup.cnf', mycnf)

    mycnf = mycnf.replace(s_datadir, t_datadir)
    slemp.writeFile(myfile, mycnf)
    start()

    result = slemp.execShell(
        'ps aux|grep mysqld| grep -v grep|grep -v python')
    if len(result[0]) > 10:
        slemp.writeFile('data/datadir.pl', t_datadir)
        return slemp.returnJson(True, 'Storage directory migration succeeded!')
    else:
        slemp.execShell('pkill -9 mysqld')
        slemp.writeFile(myfile, slemp.readFile(path + '/etc/my_backup.cnf'))
        start()
        return slemp.returnJson(False, 'File migration failed!')


def getMyPort():
    file = getConf()
    content = slemp.readFile(file)
    rep = 'port\s*=\s*(.*)'
    tmp = re.search(rep, content)
    return tmp.groups()[0].strip()


def setMyPort():
    args = getArgs()
    data = checkArgs(args, ['port'])
    if not data[0]:
        return data[1]

    port = args['port']
    file = getConf()
    content = slemp.readFile(file)
    rep = "port\s*=\s*([0-9]+)\s*\n"
    content = re.sub(rep, 'port = ' + port + '\n', content)
    slemp.writeFile(file, content)
    restart()
    return slemp.returnJson(True, 'Edited successfully!')


def runInfo():
    db = pMysqlDb()
    data = db.query('show global status')
    gets = ['Max_used_connections', 'Com_commit', 'Com_rollback', 'Questions', 'Innodb_buffer_pool_reads', 'Innodb_buffer_pool_read_requests', 'Key_reads', 'Key_read_requests', 'Key_writes',
            'Key_write_requests', 'Qcache_hits', 'Qcache_inserts', 'Bytes_received', 'Bytes_sent', 'Aborted_clients', 'Aborted_connects',
            'Created_tmp_disk_tables', 'Created_tmp_tables', 'Innodb_buffer_pool_pages_dirty', 'Opened_files', 'Open_tables', 'Opened_tables', 'Select_full_join',
            'Select_range_check', 'Sort_merge_passes', 'Table_locks_waited', 'Threads_cached', 'Threads_connected', 'Threads_created', 'Threads_running', 'Connections', 'Uptime']

    try:
        # print data
        if data[0] == 1045 or data[0] == 2003:
            pwd = db.getPwd()
            return slemp.returnJson(False, 'mysql password error:' + pwd + '!')
    except Exception as e:
        pass

    result = {}
    for d in data:
        for g in gets:
            if d[0] == g:
                result[g] = d[1]
    result['Run'] = int(time.time()) - int(result['Uptime'])
    tmp = db.query('show master status')
    try:
        result['File'] = tmp[0][0]
        result['Position'] = tmp[0][1]
    except:
        result['File'] = 'OFF'
        result['Position'] = 'OFF'
    return slemp.getJson(result)


def myDbStatus():
    result = {}
    db = pMysqlDb()
    data = db.query('show variables')
    isError = isSqlError(data)
    if isError != None:
        return isError

    gets = ['table_open_cache', 'thread_cache_size', 'key_buffer_size', 'tmp_table_size', 'max_heap_table_size', 'innodb_buffer_pool_size',
            'innodb_additional_mem_pool_size', 'innodb_log_buffer_size', 'max_connections', 'sort_buffer_size', 'read_buffer_size', 'read_rnd_buffer_size', 'join_buffer_size', 'thread_stack', 'binlog_cache_size']
    result['mem'] = {}
    for d in data:
        for g in gets:
            if d[0] == g:
                result['mem'][g] = d[1]
    # if result['mem']['query_cache_type'] != 'ON':
    #     result['mem']['query_cache_size'] = '0'
    return slemp.getJson(result)


def setDbStatus():
    gets = ['key_buffer_size', 'tmp_table_size', 'max_heap_table_size', 'innodb_buffer_pool_size', 'innodb_log_buffer_size', 'max_connections',
            'table_open_cache', 'thread_cache_size', 'sort_buffer_size', 'read_buffer_size', 'read_rnd_buffer_size', 'join_buffer_size', 'thread_stack', 'binlog_cache_size']
    emptys = ['max_connections', 'thread_cache_size', 'table_open_cache']
    args = getArgs()
    conFile = getConf()
    content = slemp.readFile(conFile)
    n = 0
    for g in gets:
        s = 'M'
        if n > 5:
            s = 'K'
        if g in emptys:
            s = ''
        rep = '\s*' + g + '\s*=\s*\d+(M|K|k|m|G)?\n'
        c = g + ' = ' + args[g] + s + '\n'
        if content.find(g) != -1:
            content = re.sub(rep, '\n' + c, content, 1)
        else:
            content = content.replace('[mysqld]\n', '[mysqld]\n' + c)
        n += 1
    slemp.writeFile(conFile, content)
    return slemp.returnJson(True, '设置成功!')


def isSqlError(mysqlMsg):
    # Detect database execution errors
    mysqlMsg = str(mysqlMsg)
    if "MySQLdb" in mysqlMsg:
        return slemp.returnJson(False, 'The MySQLdb component is missing! <br>Enter the SSH command line and enter： pip install mysql-python')
    if "2002," in mysqlMsg:
        return slemp.returnJson(False, 'Database connection failed, please check whether the database service is started!')
    if "2003," in mysqlMsg:
        return slemp.returnJson(False, "Can't connect to MySQL server on '127.0.0.1' (61)")
    if "using password:" in mysqlMsg:
        return slemp.returnJson(False, 'Database management password error!')
    if "Connection refused" in mysqlMsg:
        return slemp.returnJson(False, 'Database connection failed, please check whether the database service is started!')
    if "1133" in mysqlMsg:
        return slemp.returnJson(False, 'Database user does not exist!')
    if "1007" in mysqlMsg:
        return slemp.returnJson(False, 'Database already exists!')
    return None


def mapToList(map_obj):
    # map to list
    try:
        if type(map_obj) != list and type(map_obj) != str:
            map_obj = list(map_obj)
        return map_obj
    except:
        return []


def __createUser(dbname, username, password, address):
    pdb = pMysqlDb()

    if username == 'root':
        dbname = '*'

    pdb.execute(
        "CREATE USER `%s`@`localhost` IDENTIFIED BY '%s'" % (username, password))
    pdb.execute(
        "grant all privileges on %s.* to `%s`@`localhost`" % (dbname, username))
    for a in address.split(','):
        pdb.execute(
            "CREATE USER `%s`@`%s` IDENTIFIED BY '%s'" % (username, a, password))
        pdb.execute(
            "grant all privileges on %s.* to `%s`@`%s`" % (dbname, username, a))
    pdb.execute("flush privileges")


def getDbBackupListFunc(dbname=''):
    bkDir = slemp.getRootDir() + '/backup/database'
    blist = os.listdir(bkDir)
    r = []

    bname = 'db_' + dbname
    blen = len(bname)
    for x in blist:
        fbstr = x[0:blen]
        if fbstr == bname:
            r.append(x)
    return r


def setDbBackup():
    args = getArgs()
    data = checkArgs(args, ['name'])
    if not data[0]:
        return data[1]

    scDir = slemp.getRunDir() + '/scripts/backup.py'

    cmd = 'python ' + scDir + ' database ' + args['name'] + ' 3'
    os.system(cmd)
    return slemp.returnJson(True, 'ok')


def importDbBackup():
    args = getArgs()
    data = checkArgs(args, ['file', 'name'])
    if not data[0]:
        return data[1]

    file = args['file']
    name = args['name']

    file_path = slemp.getRootDir() + '/backup/database/' + file
    file_path_sql = slemp.getRootDir() + '/backup/database/' + file.replace('.gz', '')

    if not os.path.exists(file_path_sql):
        cmd = 'cd ' + slemp.getRootDir() + '/backup/database && gzip -d ' + file
        slemp.execShell(cmd)

    pwd = pSqliteDb('config').where('id=?', (1,)).getField('mysql_root')

    mysql_cmd = slemp.getRootDir() + '/server/mysql/bin/mysql -uroot -p' + pwd + \
        ' ' + name + ' < ' + file_path_sql

    # print(mysql_cmd)
    os.system(mysql_cmd)
    return slemp.returnJson(True, 'ok')


def deleteDbBackup():
    args = getArgs()
    data = checkArgs(args, ['filename'])
    if not data[0]:
        return data[1]

    bkDir = slemp.getRootDir() + '/backup/database'

    os.remove(bkDir + '/' + args['filename'])
    return slemp.returnJson(True, 'ok')


def getDbBackupList():
    args = getArgs()
    data = checkArgs(args, ['name'])
    if not data[0]:
        return data[1]

    r = getDbBackupListFunc(args['name'])
    bkDir = slemp.getRootDir() + '/backup/database'
    rr = []
    for x in xrange(0, len(r)):
        p = bkDir + '/' + r[x]
        data = {}
        data['name'] = r[x]

        rsize = os.path.getsize(p)
        data['size'] = slemp.toSize(rsize)

        t = os.path.getctime(p)
        t = time.localtime(t)

        data['time'] = time.strftime('%Y-%m-%d %H:%M:%S', t)
        rr.append(data)

        data['file'] = p

    return slemp.returnJson(True, 'ok', rr)


def getDbList():
    args = getArgs()
    page = 1
    page_size = 10
    search = ''
    data = {}
    if 'page' in args:
        page = int(args['page'])

    if 'page_size' in args:
        page_size = int(args['page_size'])

    if 'search' in args:
        search = args['search']

    conn = pSqliteDb('databases')
    limit = str((page - 1) * page_size) + ',' + str(page_size)
    condition = ''
    if not search == '':
        condition = "name like '%" + search + "%'"
    field = 'id,pid,name,username,password,accept,ps,addtime'
    clist = conn.where(condition, ()).field(
        field).limit(limit).order('id desc').select()

    for x in xrange(0, len(clist)):
        dbname = clist[x]['name']
        blist = getDbBackupListFunc(dbname)
        # print(blist)
        clist[x]['is_backup'] = False
        if len(blist) > 0:
            clist[x]['is_backup'] = True

    count = conn.where(condition, ()).count()
    _page = {}
    _page['count'] = count
    _page['p'] = page
    _page['row'] = page_size
    _page['tojs'] = 'dbList'
    data['page'] = slemp.getPage(_page)
    data['data'] = clist

    info = {}
    info['root_pwd'] = pSqliteDb('config').where(
        'id=?', (1,)).getField('mysql_root')
    data['info'] = info

    return slemp.getJson(data)


def syncGetDatabases():
    pdb = pMysqlDb()
    psdb = pSqliteDb('databases')
    data = pdb.query('show databases')
    isError = isSqlError(data)
    if isError != None:
        return isError
    users = pdb.query(
        "select User,Host from mysql.user where User!='root' AND Host!='localhost' AND Host!=''")
    nameArr = ['information_schema', 'performance_schema', 'mysql', 'sys']
    n = 0
    for value in data:
        b = False
        for key in nameArr:
            if value[0] == key:
                b = True
                break
        if b:
            continue
        if psdb.where("name=?", (value[0],)).count():
            continue
        host = '127.0.0.1'
        for user in users:
            if value[0] == user[0]:
                host = user[1]
                break

        ps = slemp.getMsg('INPUT_PS')
        if value[0] == 'test':
            ps = slemp.getMsg('DATABASE_TEST')
        addTime = time.strftime('%Y-%m-%d %X', time.localtime())
        if psdb.add('name,username,password,accept,ps,addtime', (value[0], value[0], '', host, ps, addTime)):
            n += 1

    msg = slemp.getInfo('本次共从服务器获取了{1}个数据库!', (str(n),))
    return slemp.returnJson(True, msg)


def toDbBase(find):
    pdb = pMysqlDb()
    psdb = pSqliteDb('databases')
    if len(find['password']) < 3:
        find['username'] = find['name']
        find['password'] = slemp.md5(str(time.time()) + find['name'])[0:10]
        psdb.where("id=?", (find['id'],)).save(
            'password,username', (find['password'], find['username']))

    result = pdb.execute("create database `" + find['name'] + "`")
    if "using password:" in str(result):
        return -1
    if "Connection refused" in str(result):
        return -1

    password = find['password']
    __createUser(find['name'], find['username'], password, find['accept'])
    return 1


def syncToDatabases():
    args = getArgs()
    data = checkArgs(args, ['type', 'ids'])
    if not data[0]:
        return data[1]

    pdb = pMysqlDb()
    result = pdb.execute("show databases")
    isError = isSqlError(result)
    if isError:
        return isError

    stype = int(args['type'])
    psdb = pSqliteDb('databases')
    n = 0

    if stype == 0:
        data = psdb.field('id,name,username,password,accept').select()
        for value in data:
            result = toDbBase(value)
            if result == 1:
                n += 1
    else:
        data = json.loads(args['ids'])
        for value in data:
            find = psdb.where("id=?", (value,)).field(
                'id,name,username,password,accept').find()
            # print find
            result = toDbBase(find)
            if result == 1:
                n += 1
    msg = slemp.getInfo('本次共同步了{1}个数据库!', (str(n),))
    return slemp.returnJson(True, msg)


def setRootPwd():
    args = getArgs()
    data = checkArgs(args, ['password'])
    if not data[0]:
        return data[1]

    password = args['password']
    try:
        pdb = pMysqlDb()
        result = pdb.query("show databases")
        isError = isSqlError(result)
        if isError != None:
            return isError

        m_version = slemp.readFile(getServerDir() + '/version.pl')
        if m_version.find('5.7') == 0 or m_version.find('8.0') == 0:
            pdb.execute(
                "UPDATE mysql.user SET authentication_string='' WHERE user='root'")
            pdb.execute(
                "ALTER USER 'root'@'localhost' IDENTIFIED BY '%s'" % password)
            pdb.execute(
                "ALTER USER 'root'@'127.0.0.1' IDENTIFIED BY '%s'" % password)
        else:
            result = pdb.execute(
                "update mysql.user set Password=password('" + password + "') where User='root'")
        pdb.execute("flush privileges")
        pSqliteDb('config').where('id=?', (1,)).save('mysql_root', (password,))
        return slemp.returnJson(True, 'Database root password changed successfully!')
    except Exception as ex:
        return slemp.returnJson(False, 'Correct mistakes:' + str(ex))


def setUserPwd():
    args = getArgs()
    data = checkArgs(args, ['password', 'name'])
    if not data[0]:
        return data[1]

    newpassword = args['password']
    username = args['name']
    id = args['id']
    try:
        pdb = pMysqlDb()
        psdb = pSqliteDb('databases')
        name = psdb.where('id=?', (id,)).getField('name')

        m_version = slemp.readFile(getServerDir() + '/version.pl')
        if m_version.find('5.7') == 0 or m_version.find('8.0') == 0:
            tmp = pdb.query(
                "select Host from mysql.user where User='" + name + "' AND Host!='localhost'")
            accept = mapToList(tmp)
            pdb.execute(
                "update mysql.user set authentication_string='' where User='" + username + "'")
            result = pdb.execute(
                "ALTER USER `%s`@`localhost` IDENTIFIED BY '%s'" % (username, newpassword))
            for my_host in accept:
                pdb.execute("ALTER USER `%s`@`%s` IDENTIFIED BY '%s'" % (
                    username, my_host[0], newpassword))
        else:
            result = pdb.execute("update mysql.user set Password=password('" +
                                 newpassword + "') where User='" + username + "'")
        isError = isSqlError(result)
        if isError != None:
            return isError
        pdb.execute("flush privileges")
        psdb.where("id=?", (id,)).setField('password', newpassword)
        return slemp.returnJson(True, slemp.getInfo('Modify database [{1}] password successfully!', (name,)))
    except Exception as ex:
        # print str(ex)
        return slemp.returnJson(False, slemp.getInfo('Failed to modify database [{1}] password!', (name,)))


def setDbPs():
    args = getArgs()
    data = checkArgs(args, ['id', 'name', 'ps'])
    if not data[0]:
        return data[1]

    ps = args['ps']
    sid = args['id']
    name = args['name']
    try:
        psdb = pSqliteDb('databases')
        psdb.where("id=?", (sid,)).setField('ps', ps)
        return slemp.returnJson(True, slemp.getInfo('Modify database [{1}] remarks successfully!', (name,)))
    except Exception as e:
        return slemp.returnJson(True, slemp.getInfo('Failed to modify database [{1}] remarks!', (name,)))


def addDb():
    args = getArgs()
    data = checkArgs(args,
                     ['password', 'name', 'codeing', 'db_user', 'dataAccess', 'ps'])
    if not data[0]:
        return data[1]

    if not 'address' in args:
        address = ''
    else:
        address = args['address'].strip()

    dbname = args['name'].strip()
    dbuser = args['db_user'].strip()
    codeing = args['codeing'].strip()
    password = args['password'].strip()
    dataAccess = args['dataAccess'].strip()
    ps = args['ps'].strip()

    reg = "^[\w\.-]+$"
    if not re.match(reg, args['name']):
        return slemp.returnJson(False, 'Database name cannot have special symbols!')
    checks = ['root', 'mysql', 'test', 'sys', 'panel_logs']
    if dbuser in checks or len(dbuser) < 1:
        return slemp.returnJson(False, 'Database username is invalid!')
    if dbname in checks or len(dbname) < 1:
        return slemp.returnJson(False, 'Invalid database name!')

    if len(password) < 1:
        password = slemp.md5(time.time())[0:8]

    wheres = {
        'utf8':   'utf8_general_ci',
        'utf8mb4':   'utf8mb4_general_ci',
        'gbk':   'gbk_chinese_ci',
        'big5':   'big5_chinese_ci'
    }
    codeStr = wheres[codeing]

    pdb = pMysqlDb()
    psdb = pSqliteDb('databases')

    if psdb.where("name=? or username=?", (dbname, dbuser)).count():
        return slemp.returnJson(False, 'Database already exists!')

    result = pdb.execute("create database `" + dbname +
                         "` DEFAULT CHARACTER SET " + codeing + " COLLATE " + codeStr)
    # print result
    isError = isSqlError(result)
    if isError != None:
        return isError

    pdb.execute("drop user '" + dbuser + "'@'localhost'")
    for a in address.split(','):
        pdb.execute("drop user '" + dbuser + "'@'" + a + "'")

    __createUser(dbname, dbuser, password, address)

    addTime = time.strftime('%Y-%m-%d %X', time.localtime())
    psdb.add('pid,name,username,password,accept,ps,addtime',
             (0, dbname, dbuser, password, address, ps, addTime))
    return slemp.returnJson(True, 'Added successfully!')


def delDb():
    args = getArgs()
    data = checkArgs(args, ['id', 'name'])
    if not data[0]:
        return data[1]
    try:
        id = args['id']
        name = args['name']
        psdb = pSqliteDb('databases')
        pdb = pMysqlDb()
        find = psdb.where("id=?", (id,)).field(
            'id,pid,name,username,password,accept,ps,addtime').find()
        accept = find['accept']
        username = find['username']

        # delete MYSQL
        result = pdb.execute("drop database `" + name + "`")
        isError = isSqlError(result)
        if isError != None:
            return isError

        users = pdb.query(
            "select Host from mysql.user where User='" + username + "' AND Host!='localhost'")
        pdb.execute("drop user '" + username + "'@'localhost'")
        for us in users:
            pdb.execute("drop user '" + username + "'@'" + us[0] + "'")
        pdb.execute("flush privileges")

        # delete SQLITE
        psdb.where("id=?", (id,)).delete()
        return slemp.returnJson(True, 'Successfully deleted!')
    except Exception as ex:
        return slemp.returnJson(False, 'Failed to delete!' + str(ex))


def getDbAccess():
    args = getArgs()
    data = checkArgs(args, ['username'])
    if not data[0]:
        return data[1]
    username = args['username']
    pdb = pMysqlDb()

    users = pdb.query("select Host from mysql.user where User='" +
                      username + "' AND Host!='localhost'")
    isError = isSqlError(users)
    if isError != None:
        return isError

    users = mapToList(users)
    if len(users) < 1:
        return slemp.returnJson(True, "127.0.0.1")
    accs = []
    for c in users:
        accs.append(c[0])
    userStr = ','.join(accs)
    return slemp.returnJson(True, userStr)


def toSize(size):
    d = ('b', 'KB', 'MB', 'GB', 'TB')
    s = d[0]
    for b in d:
        if size < 1024:
            return str(size) + ' ' + b
        size = size / 1024
        s = b
    _size = round(size, 2)
    print size, _size
    return str(size) + ' ' + b


def setDbAccess():
    args = getArgs()
    data = checkArgs(args, ['username', 'access'])
    if not data[0]:
        return data[1]
    name = args['username']
    access = args['access']
    pdb = pMysqlDb()
    psdb = pSqliteDb('databases')

    dbname = psdb.where('username=?', (name,)).getField('name')

    if name == 'root':
        password = pSqliteDb('config').where(
            'id=?', (1,)).getField('mysql_root')
    else:
        password = psdb.where("username=?", (name,)).getField('password')
    users = pdb.query("select Host from mysql.user where User='" +
                      name + "' AND Host!='localhost'")
    for us in users:
        pdb.execute("drop user '" + name + "'@'" + us[0] + "'")

    __createUser(dbname, name, password, access)

    psdb.where('username=?', (name,)).save('accept', (access,))
    return slemp.returnJson(True, '设置成功!')


def getDbInfo():
    args = getArgs()
    data = checkArgs(args, ['name'])
    if not data[0]:
        return data[1]

    db_name = args['name']
    pdb = pMysqlDb()
    # print 'show tables from `%s`' % db_name
    table_res = pdb.query('show tables from `%s`' % db_name)
    isError = isSqlError(table_res)
    if isError != None:
        return isError

    tables = mapToList(table_res)

    ret = {}
    if type(tables) == list:
        try:
            data = mapToList(pdb.query(
                "select sum(DATA_LENGTH)+sum(INDEX_LENGTH) from information_schema.tables  where table_schema='%s'" % db_name))[0][0]
        except:
            data = 0

        if not data:
            data = 0
        ret['data_size'] = slemp.toSize(data)
        # print ret
        ret['database'] = db_name

        ret3 = []

        for i in tables:
            if i == 1049:
                return slemp.returnJson(False, 'The specified database does not exist!')
            table = mapToList(
                pdb.query("show table status from `%s` where name = '%s'" % (db_name, i[0])))
            if not table:
                continue
            try:
                ret2 = {}
                ret2['type'] = table[0][1]
                ret2['rows_count'] = table[0][4]
                ret2['collation'] = table[0][14]
                data_size = table[0][6] + table[0][8]
                ret2['data_byte'] = data_size
                ret2['data_size'] = slemp.toSize(data_size)
                ret2['table_name'] = i[0]
                ret3.append(ret2)
            except:
                continue
        ret['tables'] = (ret3)

    return slemp.getJson(ret)


def repairTable():
    args = getArgs()
    data = checkArgs(args, ['db_name', 'tables'])
    if not data[0]:
        return data[1]

    db_name = args['db_name']
    tables = json.loads(args['tables'])
    pdb = pMysqlDb()
    mysql_table = mapToList(pdb.query('show tables from `%s`' % db_name))
    ret = []
    if type(mysql_table) == list:
        if len(mysql_table) > 0:
            for i in mysql_table:
                for i2 in tables:
                    if i2 == i[0]:
                        ret.append(i2)
            if len(ret) > 0:
                for i in ret:
                    pdb.execute('REPAIR TABLE `%s`.`%s`' % (db_name, i))
                return slemp.returnJson(True, "Repair done!")
    return slemp.returnJson(False, "Repair failed!")


def optTable():
    args = getArgs()
    data = checkArgs(args, ['db_name', 'tables'])
    if not data[0]:
        return data[1]

    db_name = args['db_name']
    tables = json.loads(args['tables'])
    pdb = pMysqlDb()
    mysql_table = mapToList(pdb.query('show tables from `%s`' % db_name))
    ret = []
    if type(mysql_table) == list:
        if len(mysql_table) > 0:
            for i in mysql_table:
                for i2 in tables:
                    if i2 == i[0]:
                        ret.append(i2)
            if len(ret) > 0:
                for i in ret:
                    pdb.execute('OPTIMIZE TABLE `%s`.`%s`' % (db_name, i))
                return slemp.returnJson(True, "Optimization succeeded!")
    return slemp.returnJson(False, "Optimization failed or has been optimized!")


def alterTable():
    args = getArgs()
    data = checkArgs(args, ['db_name', 'tables'])
    if not data[0]:
        return data[1]

    db_name = args['db_name']
    tables = json.loads(args['tables'])
    table_type = args['table_type']
    pdb = pMysqlDb()
    mysql_table = mapToList(pdb.query('show tables from `%s`' % db_name))
    ret = []
    if type(mysql_table) == list:
        if len(mysql_table) > 0:
            for i in mysql_table:
                for i2 in tables:
                    if i2 == i[0]:
                        ret.append(i2)
            if len(ret) > 0:
                for i in ret:
                    pdb.execute('alter table `%s`.`%s` ENGINE=`%s`' %
                                (db_name, i, table_type))
                return slemp.returnJson(True, "Change succeeded!")
    return slemp.returnJson(False, "Change failed!")


def getTotalStatistics():
    st = status()
    data = {}
    if st == 'start':
        data['status'] = True
        data['count'] = pSqliteDb('databases').count()
        data['ver'] = slemp.readFile(getServerDir() + '/version.pl').strip()
        return slemp.returnJson(True, 'ok', data)
    else:
        data['status'] = False
        data['count'] = 0
        return slemp.returnJson(False, 'fail', data)


def findBinlogDoDb():
    conf = getConf()
    con = slemp.readFile(conf)
    rep = r"binlog-do-db\s*?=\s*?(.*)"
    dodb = re.findall(rep, con, re.M)
    return dodb


def findBinlogSlaveDoDb():
    conf = getConf()
    con = slemp.readFile(conf)
    rep = r"replicate-do-db\s*?=\s*?(.*)"
    dodb = re.findall(rep, con, re.M)
    return dodb


def getMasterDbList(version=''):
    args = getArgs()
    page = 1
    page_size = 10
    search = ''
    data = {}
    if 'page' in args:
        page = int(args['page'])

    if 'page_size' in args:
        page_size = int(args['page_size'])

    if 'search' in args:
        search = args['search']

    conn = pSqliteDb('databases')
    limit = str((page - 1) * page_size) + ',' + str(page_size)
    condition = ''
    dodb = findBinlogDoDb()
    data['dodb'] = dodb

    slave_dodb = findBinlogSlaveDoDb()

    if not search == '':
        condition = "name like '%" + search + "%'"
    field = 'id,pid,name,username,password,accept,ps,addtime'
    clist = conn.where(condition, ()).field(
        field).limit(limit).order('id desc').select()
    count = conn.where(condition, ()).count()

    for x in xrange(0, len(clist)):
        if clist[x]['name'] in dodb:
            clist[x]['master'] = 1
        else:
            clist[x]['master'] = 0

        if clist[x]['name'] in slave_dodb:
            clist[x]['slave'] = 1
        else:
            clist[x]['slave'] = 0

    _page = {}
    _page['count'] = count
    _page['p'] = page
    _page['row'] = page_size
    _page['tojs'] = 'dbList'
    data['page'] = slemp.getPage(_page)
    data['data'] = clist

    return slemp.getJson(data)


def setDbMaster(version):
    args = getArgs()
    data = checkArgs(args, ['name'])
    if not data[0]:
        return data[1]

    conf = getConf()
    con = slemp.readFile(conf)
    rep = r"(binlog-do-db\s*?=\s*?(.*))"
    dodb = re.findall(rep, con, re.M)

    isHas = False
    for x in xrange(0, len(dodb)):

        if dodb[x][1] == args['name']:
            isHas = True

            con = con.replace(dodb[x][0] + "\n", '')
            slemp.writeFile(conf, con)

    if not isHas:
        prefix = '#binlog-do-db'
        con = con.replace(
            prefix, prefix + "\nbinlog-do-db=" + args['name'])
        slemp.writeFile(conf, con)

    restart(version)
    time.sleep(4)
    return slemp.returnJson(True, 'Set successfully', [args, dodb])


def setDbSlave(version):
    args = getArgs()
    data = checkArgs(args, ['name'])
    if not data[0]:
        return data[1]

    conf = getConf()
    con = slemp.readFile(conf)
    rep = r"(replicate-do-db\s*?=\s*?(.*))"
    dodb = re.findall(rep, con, re.M)

    isHas = False
    for x in xrange(0, len(dodb)):
        if dodb[x][1] == args['name']:
            isHas = True

            con = con.replace(dodb[x][0] + "\n", '')
            slemp.writeFile(conf, con)

    if not isHas:
        prefix = '#replicate-do-db'
        con = con.replace(
            prefix, prefix + "\nreplicate-do-db=" + args['name'])
        slemp.writeFile(conf, con)

    restart(version)
    time.sleep(4)
    return slemp.returnJson(True, 'Set successfully', [args, dodb])


def getMasterStatus(version=''):
    conf = getConf()
    con = slemp.readFile(conf)
    master_status = False
    if con.find('#log-bin') == -1 and con.find('log-bin') > 1:
        dodb = findBinlogDoDb()
        if len(dodb) > 0:
            master_status = True
    data = {}
    data['status'] = master_status

    db = pMysqlDb()
    dlist = db.query('show slave status')
    if len(dlist) > 0 and (dlist[0][10] == 'Yes' or dlist[0][11] == 'Yes'):
        data['slave_status'] = True

    return slemp.returnJson(master_status, 'Set successfully', data)


def setMasterStatus(version=''):

    conf = getConf()
    con = slemp.readFile(conf)

    if con.find('#log-bin') != -1:
        return slemp.returnJson(False, 'Binary logging must be enabled')

    sign = 'slemp_ms_open'

    dodb = findBinlogDoDb()
    if not sign in dodb:
        prefix = '#binlog-do-db'
        con = con.replace(prefix, prefix + "\nbinlog-do-db=" + sign)
        slemp.writeFile(conf, con)
    else:
        con = con.replace("binlog-do-db=" + sign + "\n", '')
        rep = r"(binlog-do-db\s*?=\s*?(.*))"
        dodb = re.findall(rep, con, re.M)
        for x in xrange(0, len(dodb)):
            con = con.replace(dodb[x][0] + "\n", '')
        slemp.writeFile(conf, con)

    restart(version)
    time.sleep(2)
    return slemp.returnJson(True, 'Set successfully')


def getMasterRepSlaveList(version=''):
    args = getArgs()
    page = 1
    page_size = 10
    search = ''
    data = {}
    if 'page' in args:
        page = int(args['page'])

    if 'page_size' in args:
        page_size = int(args['page_size'])

    if 'search' in args:
        search = args['search']

    conn = pSqliteDb('master_replication_user')
    limit = str((page - 1) * page_size) + ',' + str(page_size)
    condition = ''

    if not search == '':
        condition = "name like '%" + search + "%'"
    field = 'id,username,password,accept,ps,addtime'
    clist = conn.where(condition, ()).field(
        field).limit(limit).order('id desc').select()
    count = conn.where(condition, ()).count()

    _page = {}
    _page['count'] = count
    _page['p'] = page
    _page['row'] = page_size
    _page['tojs'] = 'getMasterRepSlaveList'
    data['page'] = slemp.getPage(_page)
    data['data'] = clist

    return slemp.getJson(data)


def addMasterRepSlaveUser(version=''):
    args = getArgs()
    data = checkArgs(args,
                     ['username', 'password'])
    if not data[0]:
        return data[1]

    if not 'address' in args:
        address = ''
    else:
        address = args['address'].strip()

    username = args['username'].strip()
    password = args['password'].strip()
    # ps = args['ps'].strip()
    # address = args['address'].strip()
    # dataAccess = args['dataAccess'].strip()

    reg = "^[\w\.-]+$"
    if not re.match(reg, username):
        return slemp.returnJson(False, 'Username cannot contain special symbols!')
    checks = ['root', 'mysql', 'test', 'sys', 'panel_logs']
    if username in checks or len(username) < 1:
        return slemp.returnJson(False, 'Username is invalid!')
    if password in checks or len(password) < 1:
        return slemp.returnJson(False, 'Invalid password!')

    if len(password) < 1:
        password = slemp.md5(time.time())[0:8]

    pdb = pMysqlDb()
    psdb = pSqliteDb('master_replication_user')

    if psdb.where("username=?", (username)).count():
        return slemp.returnJson(False, 'User already exists!')

    result = pdb.execute("GRANT REPLICATION SLAVE ON *.* TO  '" +
                         username + "'@'%' identified by '" + password + "';FLUSH PRIVILEGES;")
    # print result
    isError = isSqlError(result)
    if isError != None:
        return isError

    addTime = time.strftime('%Y-%m-%d %X', time.localtime())
    psdb.add('username,password,accept,ps,addtime',
             (username, password, '%', '', addTime))
    return slemp.returnJson(True, 'Added successfully!')


def getMasterRepSlaveUserCmd(version):
    args = getArgs()
    data = checkArgs(args, ['username', 'db'])
    if not data[0]:
        return data[1]

    psdb = pSqliteDb('master_replication_user')
    f = 'username,password'
    if args['username'] == '':

        count = psdb.count()

        if count == 0:
            return slemp.returnJson(False, 'Please add a sync account!')

        clist = psdb.field(f).limit('1').order('id desc').select()
    else:
        clist = psdb.field(f).where("username=?", (args['username'],)).limit(
            '1').order('id desc').select()

    ip = slemp.getLocalIp()
    port = getMyPort()

    db = pMysqlDb()
    tmp = db.query('show master status')

    if len(tmp) == 0:
        return slemp.returnJson(False, 'Unopened!')

    sql = "CHANGE MASTER TO MASTER_HOST='" + ip + "', MASTER_PORT=" + port + ", MASTER_USER='" + \
        clist[0]['username']  + "', MASTER_PASSWORD='" + \
        clist[0]['password'] + \
        "', MASTER_LOG_FILE='" + tmp[0][0] + \
        "',MASTER_LOG_POS=" + str(tmp[0][1]) + ""

    # if args['db'] != '':
    #     replicate-do-table

    return slemp.returnJson(True, 'OK!', sql)


def delMasterRepSlaveUser(version=''):
    args = getArgs()
    data = checkArgs(args, ['username'])
    if not data[0]:
        return data[1]

    pdb = pMysqlDb()
    psdb = pSqliteDb('master_replication_user')
    pdb.execute("drop user '" + args['username'] + "'@'%'")
    psdb.where("username=?", (args['username'],)).delete()

    return slemp.returnJson(True, 'Successfully deleted!')


def updateMasterRepSlaveUser(version=''):
    args = getArgs()
    data = checkArgs(args, ['username', 'password'])
    if not data[0]:
        return data[1]

    pdb = pMysqlDb()
    psdb = pSqliteDb('master_replication_user')
    pdb.execute("drop user '" + args['username'] + "'@'%'")

    pdb.execute("GRANT REPLICATION SLAVE ON *.* TO  '" +
                args['username'] + "'@'%' identified by '" + args['password'] + "'")

    psdb.where("username=?", (args['username'],)).save(
        'password', args['password'])

    return slemp.returnJson(True, 'Update completed!')


def getSlaveList(version=''):

    db = pMysqlDb()
    dlist = db.query('show slave status')

    # print(dlist)
    ret = []
    for x in xrange(0, len(dlist)):
        tmp = {}
        tmp['Master_User'] = dlist[x][2]
        tmp['Master_Host'] = dlist[x][1]
        tmp['Master_Port'] = dlist[x][3]
        tmp['Master_Log_File'] = dlist[x][5]
        tmp['Slave_IO_Running'] = dlist[x][10]
        tmp['Slave_SQL_Running'] = dlist[x][11]
        ret.append(tmp)
    data = {}
    data['data'] = ret

    return slemp.getJson(data)


def setSlaveStatus(version=''):
    db = pMysqlDb()
    dlist = db.query('show slave status')

    if len(dlist) == 0:
        return slemp.returnJson(False, 'Need to manually add the main service sync command!')

    if len(dlist) > 0 and (dlist[0][10] == 'Yes' or dlist[0][11] == 'Yes'):
        db.query('stop slave')
    else:
        db.query('start slave')

    return slemp.returnJson(True, 'Set successfully!')


def deleteSlave(version=''):
    db = pMysqlDb()
    dlist = db.query('stop slave;reset slave all')
    return slemp.returnJson(True, 'Successfully deleted!')


def dumpMysqlData(version):

    args = getArgs()
    data = checkArgs(args, ['db'])
    if not data[0]:
        return data[1]

    pwd = pSqliteDb('config').where('id=?', (1,)).getField('mysql_root')
    if args['db'] == 'all' or args['db'] == 'ALL':
        dlist = findBinlogDoDb()
        cmd = getServerDir() + "/bin/mysqldump -uroot -p" + \
            pwd + " --databases " + ' '.join(dlist) + \
            " > /tmp/dump.sql"
    else:
        cmd = getServerDir() + "/bin/mysqldump -uroot -p" + pwd + \
            " --databases " + args['db'] + " > /tmp/dump.sql"

    ret = slemp.execShell(cmd)

    if ret[0] == '':
        return 'ok'
    return 'fail'


from threading import Thread
from time import sleep


def async(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper


def doFullSync():

    args = getArgs()
    data = checkArgs(args, ['db'])
    if not data[0]:
        return data[1]

    status_data = {}
    status_data['progress'] = 5

    db = pMysqlDb()

    dlist = db.query('show slave status')
    if len(dlist) == 0:
        status_data['code'] = -1
        status_data['msg'] = 'Does not start...'

    ip = dlist[0][1]
    print(ip)

    status_file = '/tmp/db_async_status.txt'

    status_data['code'] = 0
    status_data['msg'] = 'Running...'
    slemp.writeFile(status_file, json.dumps(status_data))

    import paramiko
    paramiko.util.log_to_file('paramiko.log')
    ssh = paramiko.SSHClient()

    SSH_PRIVATE_KEY = '/root/.ssh/id_rsa'

    if slemp.getOs() == 'darwin':
        user = slemp.execShell(
            "who | sed -n '2, 1p' |awk '{print $1}'")[0].strip()
        SSH_PRIVATE_KEY = '/Users/' + user + '/.ssh/id_rsa'

    print(SSH_PRIVATE_KEY)
    if not os.path.exists(SSH_PRIVATE_KEY):
        status_data['code'] = 0
        status_data['msg'] = 'No login required...'
        slemp.writeFile(status_file, json.dumps(status_data))
        return

    try:
        key = paramiko.RSAKey.from_private_key_file(SSH_PRIVATE_KEY)
        # ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=ip, port=22, username='root', pkey=key)
    except Exception as e:
        status_data['code'] = 0
        status_data['msg'] = 'No login required....'
        slemp.writeFile(status_file, json.dumps(status_data))
        return

    cmd = "cd /home/slemp/server/panel && python /home/slemp/server/panel/plugins/mysql/index.py dump_mysql_data {\"db\":'" + args[
        'db'] + "'}"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    result = stdout.read()
    result_err = stderr.read()

    if result == 'ok':
        status_data['code'] = 1
        status_data['msg'] = 'Primary server backup completed...'
        status_data['progress'] = 30
        slemp.writeFile(status_file, json.dumps(status_data))

    r = slemp.execShell('scp root@' + ip + ':/tmp/dump.sql /tmp')
    if r[0] == '':
        status_data['code'] = 2
        status_data['msg'] = 'Data synchronization is done locally...'
        status_data['progress'] = 40
        slemp.writeFile(status_file, json.dumps(status_data))

    cmd = 'cd /home/slemp/server/panel && python /home/slemp/server/panel/plugins/mysql/index.py get_master_rep_slave_user_cmd {"username":"","db":""}'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    result = stdout.read()
    result_err = stderr.read()
    cmd_data = json.loads(result)

    db.query('stop slave')
    status_data['code'] = 3
    status_data['msg'] = 'Stop completion from library...'
    status_data['progress'] = 45
    slemp.writeFile(status_file, json.dumps(status_data))

    dlist = db.query(cmd_data['data'])
    status_data['code'] = 4
    status_data['msg'] = 'Refresh library information complete...'
    status_data['progress'] = 50
    slemp.writeFile(status_file, json.dumps(status_data))

    pwd = pSqliteDb('config').where('id=?', (1,)).getField('mysql_root')
    cmd = getServerDir() + "/bin/mysql -uroot -p" + pwd + " < /tmp/dump.sql"
    print(slemp.execShell(cmd))
    status_data['code'] = 5
    status_data['msg'] = 'Sync data complete...'
    status_data['progress'] = 90
    slemp.writeFile(status_file, json.dumps(status_data))

    db.query('start slave')
    status_data['code'] = 6
    status_data['msg'] = 'Restart from the library completes...'
    status_data['progress'] = 100
    slemp.writeFile(status_file, json.dumps(status_data))

    return True


def fullSync(version=''):
    args = getArgs()
    data = checkArgs(args, ['db', 'begin'])
    if not data[0]:
        return data[1]

    status_file = '/tmp/db_async_status.txt'
    if args['begin'] == '1':
        cmd = 'cd ' + slemp.getRunDir() + ' && python ' + \
            getPluginDir() + \
            '/index.py do_full_sync {"db":"' + args['db'] + '"} &'
        slemp.execShell(cmd)
        return json.dumps({'code': 0, 'msg': 'Synchronizing data!', 'progress': 0})

    if os.path.exists(status_file):
        c = slemp.readFile(status_file)
        d = json.loads(c)

        if d['code'] == 6:
            os.remove(status_file)
        return c

    return json.dumps({'code': 0, 'msg': 'Click Start to start syncing!', 'progress': 0})

if __name__ == "__main__":
    func = sys.argv[1]
    version = sys.argv[2]
    if func == 'status':
        print(status(version))
    elif func == 'start':
        print(start(version))
    elif func == 'stop':
        print(stop(version))
    elif func == 'restart':
        print(restart(version))
    elif func == 'reload':
        print(reload(version))
    elif func == 'initd_status':
        print(initdStatus())
    elif func == 'initd_install':
        print(initdInstall())
    elif func == 'initd_uninstall':
        print(initdUinstall())
    elif func == 'run_info':
        print(runInfo())
    elif func == 'db_status':
        print(myDbStatus())
    elif func == 'set_db_status':
        print(setDbStatus())
    elif func == 'conf':
        print(getConf())
    elif func == 'bin_log':
        print(binLog())
    elif func == 'error_log':
        print(getErrorLog())
    elif func == 'show_log':
        print(getShowLogFile())
    elif func == 'my_db_pos':
        print(getMyDbPos())
    elif func == 'set_db_pos':
        print(setMyDbPos())
    elif func == 'my_port':
        print(getMyPort())
    elif func == 'set_my_port':
        print(setMyPort())
    elif func == 'init_pwd':
        print(initMysqlPwd())
    elif func == 'get_db_list':
        print(getDbList())
    elif func == 'set_db_backup':
        print(setDbBackup())
    elif func == 'import_db_backup':
        print(importDbBackup())
    elif func == 'delete_db_backup':
        print(deleteDbBackup())
    elif func == 'get_db_backup_list':
        print(getDbBackupList())
    elif func == 'add_db':
        print(addDb())
    elif func == 'del_db':
        print(delDb())
    elif func == 'sync_get_databases':
        print(syncGetDatabases())
    elif func == 'sync_to_databases':
        print(syncToDatabases())
    elif func == 'set_root_pwd':
        print(setRootPwd())
    elif func == 'set_user_pwd':
        print(setUserPwd())
    elif func == 'get_db_access':
        print(getDbAccess())
    elif func == 'set_db_access':
        print(setDbAccess())
    elif func == 'set_db_ps':
        print(setDbPs())
    elif func == 'get_db_info':
        print(getDbInfo())
    elif func == 'repair_table':
        print(repairTable())
    elif func == 'opt_table':
        print(optTable())
    elif func == 'alter_table':
        print(alterTable())
    elif func == 'get_total_statistics':
        print(getTotalStatistics())
    elif func == 'get_masterdb_list':
        print(getMasterDbList(version))
    elif func == 'get_master_status':
        print(getMasterStatus(version))
    elif func == 'set_master_status':
        print(setMasterStatus(version))
    elif func == 'set_db_master':
        print(setDbMaster(version))
    elif func == 'set_db_slave':
        print(setDbSlave(version))
    elif func == 'get_master_rep_slave_list':
        print(getMasterRepSlaveList(version))
    elif func == 'add_master_rep_slave_user':
        print(addMasterRepSlaveUser(version))
    elif func == 'del_master_rep_slave_user':
        print(delMasterRepSlaveUser(version))
    elif func == 'update_master_rep_slave_user':
        print(updateMasterRepSlaveUser(version))
    elif func == 'get_master_rep_slave_user_cmd':
        print(getMasterRepSlaveUserCmd(version))
    elif func == 'get_slave_list':
        print(getSlaveList(version))
    elif func == 'set_slave_status':
        print(setSlaveStatus(version))
    elif func == 'delete_slave':
        print(deleteSlave(version))
    elif func == 'full_sync':
        print(fullSync(version))
    elif func == 'do_full_sync':
        print(doFullSync())
    elif func == 'dump_mysql_data':
        print(dumpMysqlData(version))
    else:
        print('error')
