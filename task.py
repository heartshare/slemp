# coding: utf-8

#------------------------------
# Scheduled Tasks
#------------------------------
import sys
import os
import json
import time
import threading
# print sys.path

sys.path.append("/usr/local/lib/python2.7/site-packages")
import psutil

sys.path.append(os.getcwd() + "/class/core")
reload(sys)
sys.setdefaultencoding('utf-8')
import db
import slemp


global pre, timeoutCount, logPath, isTask, oldEdate, isCheck
pre = 0
timeoutCount = 0
isCheck = 0
oldEdate = None

logPath = os.getcwd() + '/tmp/panelExec.log'
isTask = os.getcwd() + '/tmp/panelTask.pl'

if not os.path.exists(os.getcwd() + "/tmp"):
    os.system('mkdir -p ' + os.getcwd() + "/tmp")

if not os.path.exists(logPath):
    os.system("touch " + logPath)

if not os.path.exists(isTask):
    os.system("touch " + isTask)


def async(f):
    def wrapper(*args, **kwargs):
        thr = threading.Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper


@async
def restartSlemp():
    time.sleep(1)
    cmd = slemp.getRunDir() + '/scripts/init.d/slemp restart'
    slemp.execShell(cmd)


class MyBad():
    _msg = None

    def __init__(self, msg):
        self._msg = msg

    def __repr__(self):
        return self._msg


def execShell(cmdstring, cwd=None, timeout=None, shell=True):
    try:
        global logPath
        import shlex
        import datetime
        import subprocess
        import time

        if timeout:
            end_time = datetime.datetime.now() + datetime.timedelta(seconds=timeout)

        sub = subprocess.Popen(cmdstring + ' > ' + logPath + ' 2>&1',
                               cwd=cwd, stdin=subprocess.PIPE, shell=shell, bufsize=4096)

        while sub.poll() is None:
            time.sleep(0.1)

        return sub.returncode
    except:
        return None


def downloadFile(url, filename):
    # download file
    try:
        import urllib
        import socket
        socket.setdefaulttimeout(10)
        urllib.urlretrieve(url, filename=filename, reporthook=downloadHook)
        os.system('chown www.www ' + filename)
        writeLogs('done')
    except:
        writeLogs('done')


def downloadHook(count, blockSize, totalSize):
    # Download file progress callback
    global pre
    used = count * blockSize
    pre1 = int((100.0 * used / totalSize))
    if pre == pre1:
        return
    speed = {'total': totalSize, 'used': used, 'pre': pre}
    # print 'task downloadHook', speed
    writeLogs(json.dumps(speed))
    pre = pre1


def writeLogs(logMsg):
    # write output log
    try:
        global logPath
        fp = open(logPath, 'w+')
        fp.write(logMsg)
        fp.close()
    except:
        pass


def startTask():
    # task queue
    global isTask
    try:
        while True:
            try:
                if os.path.exists(isTask):
                    # print "run --- !"
                    sql = db.Sql()
                    sql.table('tasks').where(
                        "status=?", ('-1',)).setField('status', '0')
                    taskArr = sql.table('tasks').where("status=?", ('0',)).field(
                        'id,type,execstr').order("id asc").select()
                    # print sql
                    for value in taskArr:
                        # print value
                        start = int(time.time())
                        if not sql.table('tasks').where("id=?", (value['id'],)).count():
                            continue
                        sql.table('tasks').where("id=?", (value['id'],)).save(
                            'status,start', ('-1', start))
                        if value['type'] == 'download':
                            argv = value['execstr'].split('|slemp|')
                            downloadFile(argv[0], argv[1])
                        elif value['type'] == 'execshell':
                            execShell(value['execstr'])
                        end = int(time.time())
                        sql.table('tasks').where("id=?", (value['id'],)).save(
                            'status,end', ('1', end))
                        # if(sql.table('tasks').where("status=?", ('0')).count() < 1):
                        #     os.system('rm -f ' + isTask)
            except:
                pass
            # siteEdate()
            # mainSafe()
            time.sleep(2)
    except:
        print "ff"
        time.sleep(60)
        startTask()


def mainSafe():
    global isCheck
    try:
        if isCheck < 100:
            isCheck += 1
            return True
        isCheck = 0
        isStart = slemp.execShell(
            "ps aux |grep 'python main.py'|grep -v grep|awk '{print $2}'")[0]
        if not isStart:
            os.system('/etc/init.d/bt start')
            isStart = slemp.execShell(
                "ps aux |grep 'python main.py'|grep -v grep|awk '{print $2}'")[0]
            slemp.writeLog('Daemon', 'SLEMP Panel service program started successfully -> PID: ' + isStart)
    except:
        time.sleep(30)
        mainSafe()


def siteEdate():
    # Website Expiration Handling
    global oldEdate
    try:
        if not oldEdate:
            oldEdate = slemp.readFile('data/edate.pl')
        if not oldEdate:
            oldEdate = '0000-00-00'
        mEdate = time.strftime('%Y-%m-%d', time.localtime())
        if oldEdate == mEdate:
            return False
        edateSites = slemp.M('sites').where('edate>? AND edate<? AND (status=? OR status=?)',
                                         ('0000-00-00', mEdate, 1, u'running')).field('id,name').select()
        import panelSite
        siteObject = panelSite.panelSite()
        for site in edateSites:
            get = MyBad('')
            get.id = site['id']
            get.name = site['name']
            siteObject.SiteStop(get)
        oldEdate = mEdate
        slemp.writeFile('data/edate.pl', mEdate)
    except:
        pass


def systemTask():
    # System monitoring tasks
    try:
        import system_api
        import psutil
        import time
        sm = system_api.system_api()
        filename = 'data/control.conf'

        sql = db.Sql().dbfile('system')
        csql = slemp.readFile('data/sql/system.sql')
        csql_list = csql.split(';')
        for index in range(len(csql_list)):
            sql.execute(csql_list[index], ())

        cpuIo = cpu = {}
        cpuCount = psutil.cpu_count()
        used = count = 0
        reloadNum = 0
        network_up = network_down = diskio_1 = diskio_2 = networkInfo = cpuInfo = diskInfo = None
        while True:
            if not os.path.exists(filename):
                time.sleep(10)
                continue

            day = 30
            try:
                day = int(slemp.readFile(filename))
                if day < 1:
                    time.sleep(10)
                    continue
            except:
                day = 30

            tmp = {}
            # Get the current CPU Io
            tmp['used'] = psutil.cpu_percent(interval=1)

            if not cpuInfo:
                tmp['mem'] = sm.getMemUsed()
                cpuInfo = tmp

            if cpuInfo['used'] < tmp['used']:
                tmp['mem'] = sm.getMemUsed()
                cpuInfo = tmp

            # Get the current network Io
            networkIo = psutil.net_io_counters()[:4]
            if not network_up:
                network_up = networkIo[0]
                network_down = networkIo[1]
            tmp = {}
            tmp['upTotal'] = networkIo[0]
            tmp['downTotal'] = networkIo[1]
            tmp['up'] = round(float((networkIo[0] - network_up) / 1024), 2)
            tmp['down'] = round(float((networkIo[1] - network_down) / 1024), 2)
            tmp['downPackets'] = networkIo[3]
            tmp['upPackets'] = networkIo[2]

            network_up = networkIo[0]
            network_down = networkIo[1]

            if not networkInfo:
                networkInfo = tmp
            if (tmp['up'] + tmp['down']) > (networkInfo['up'] + networkInfo['down']):
                networkInfo = tmp
            # Fetch disk Io
            # if os.path.exists('/proc/diskstats'):
            diskio_2 = psutil.disk_io_counters()
            if not diskio_1:
                diskio_1 = diskio_2
            tmp = {}
            tmp['read_count'] = diskio_2.read_count - diskio_1.read_count
            tmp['write_count'] = diskio_2.write_count - diskio_1.write_count
            tmp['read_bytes'] = diskio_2.read_bytes - diskio_1.read_bytes
            tmp['write_bytes'] = diskio_2.write_bytes - diskio_1.write_bytes
            tmp['read_time'] = diskio_2.read_time - diskio_1.read_time
            tmp['write_time'] = diskio_2.write_time - diskio_1.write_time

            if not diskInfo:
                diskInfo = tmp
            else:
                diskInfo['read_count'] += tmp['read_count']
                diskInfo['write_count'] += tmp['write_count']
                diskInfo['read_bytes'] += tmp['read_bytes']
                diskInfo['write_bytes'] += tmp['write_bytes']
                diskInfo['read_time'] += tmp['read_time']
                diskInfo['write_time'] += tmp['write_time']
            diskio_1 = diskio_2

            # print diskInfo
            if count >= 12:
                try:
                    addtime = int(time.time())
                    deltime = addtime - (day * 86400)

                    data = (cpuInfo['used'], cpuInfo['mem'], addtime)
                    sql.table('cpuio').add('pro,mem,addtime', data)
                    sql.table('cpuio').where("addtime<?", (deltime,)).delete()

                    data = (networkInfo['up'] / 5, networkInfo['down'] / 5, networkInfo['upTotal'], networkInfo[
                            'downTotal'], networkInfo['downPackets'], networkInfo['upPackets'], addtime)
                    sql.table('network').add(
                        'up,down,total_up,total_down,down_packets,up_packets,addtime', data)
                    sql.table('network').where(
                        "addtime<?", (deltime,)).delete()
                    # if os.path.exists('/proc/diskstats'):
                    data = (diskInfo['read_count'], diskInfo['write_count'], diskInfo['read_bytes'], diskInfo[
                            'write_bytes'], diskInfo['read_time'], diskInfo['write_time'], addtime)
                    sql.table('diskio').add(
                        'read_count,write_count,read_bytes,write_bytes,read_time,write_time,addtime', data)
                    sql.table('diskio').where(
                        "addtime<?", (deltime,)).delete()

                    # LoadAverage
                    load_average = sm.getLoadAverage()
                    lpro = round(
                        (load_average['one'] / load_average['max']) * 100, 2)
                    if lpro > 100:
                        lpro = 100
                    sql.table('load_average').add('pro,one,five,fifteen,addtime', (lpro, load_average[
                        'one'], load_average['five'], load_average['fifteen'], addtime))

                    lpro = None
                    load_average = None
                    cpuInfo = None
                    networkInfo = None
                    diskInfo = None
                    count = 0
                    reloadNum += 1
                    if reloadNum > 1440:
                        reloadNum = 0
                        restartSlemp()
                except Exception, ex:
                    print str(ex)

            del(tmp)
            time.sleep(5)
            count += 1
    except Exception, ex:
        print str(ex)
        import time
        time.sleep(30)
        systemTask()


# -------------------------------------- PHP Monitoring start --------------------------------------------- #
# 502 error checking thread
def check502Task():
    try:
        while True:
            if os.path.exists(slemp.getRunDir() + '/data/502Task.pl'):
                check502()
            time.sleep(30)
    except:
        time.sleep(30)
        check502Task()


def check502():
    try:
        phpversions = ['53', '54', '55', '56', '70', '71', '72', '73', '74']
        for version in phpversions:
            sdir = slemp.getServerDir()
            php_path = sdir + '/php/' + version + '/sbin/php-fpm'
            if not os.path.exists(php_path):
                continue
            if checkPHPVersion(version):
                continue
            if startPHPVersion(version):
                print 'PHP detected-' + version + ' handling exceptions, automatically fixed!'
                slemp.writeLog('PHP Daemon', 'PHP detected-' + version + ' handling exceptions, automatically fixed!')
    except Exception as e:
        print str(e)


# Handle the specified PHP version
def startPHPVersion(version):
    sdir = slemp.getServerDir()
    try:
        fpm = sdir + '/php/init.d/php' + version
        php_path = sdir + '/php/' + version + '/sbin/php-fpm'
        if not os.path.exists(php_path):
            if os.path.exists(fpm):
                os.remove(fpm)
            return False

        if not os.path.exists(fpm):
            return False

        # try reloading the service
        os.system(fpm + ' reload')
        if checkPHPVersion(version):
            return True

        # try restarting the service
        cgi = '/tmp/php-cgi-' + version + '.sock'
        pid = sdir + '/php/' + version + '/var/run/php-fpm.pid'
        data = slemp.execShell("ps -ef | grep php/" + version +
                            " | grep -v grep|grep -v python |awk '{print $2}'")
        if data[0] != '':
            os.system("ps -ef | grep php/" + version +
                      " | grep -v grep|grep -v python |awk '{print $2}' | xargs kill ")
        time.sleep(0.5)
        if not os.path.exists(cgi):
            os.system('rm -f ' + cgi)
        if not os.path.exists(pid):
            os.system('rm -f ' + pid)
        os.system(fpm + ' start')
        if checkPHPVersion(version):
            return True

        # Check for proper startup
        if os.path.exists(cgi):
            return True
    except Exception as e:
        print str(e)
        return True


# Check the specified PHP version
def checkPHPVersion(version):
    try:
        url = 'http://127.0.0.1/phpfpm_status_' + version
        result = slemp.httpGet(url)
        # print version,result
        # check nginx
        if result.find('Bad Gateway') != -1:
            return False
        if result.find('HTTP Error 404: Not Found') != -1:
            return False

        # Check if the web service is started
        if result.find('Connection refused') != -1:
            global isTask
            if os.path.exists(isTask):
                isStatus = slemp.readFile(isTask)
                if isStatus == 'True':
                    return True
            filename = '/etc/init.d/openresty'
            if os.path.exists(filename):
                os.system(filename + ' start')
        return True
    except:
        return True

# --------------------------------------PHP Monitoring end--------------------------------------------- #

if __name__ == "__main__":

    t = threading.Thread(target=systemTask)
    t.setDaemon(True)
    t.start()

    p = threading.Thread(target=check502Task)
    p.setDaemon(True)
    p.start()

    startTask()
