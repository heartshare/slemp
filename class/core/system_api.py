# coding: utf-8

import psutil
import time
import os
import re
import math
import json

from flask import Flask, session
from flask import request

import db
import slemp
import requests
import config_api


from threading import Thread
from time import sleep


def async(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper


class system_api:
    setupPath = None
    pids = None

    def __init__(self):
        self.setupPath = slemp.getServerDir()

    ##### ----- start ----- ###
    def networkApi(self):
        data = self.getNetWork()
        return slemp.getJson(data)

    def updateServerApi(self):
        stype = request.args.get('type', 'check')
        version = request.args.get('version', '')
        return self.updateServer(stype, version)

    def systemTotalApi(self):
        data = self.getSystemTotal()
        return slemp.getJson(data)

    def diskInfoApi(self):
        diskInfo = self.getDiskInfo()
        return slemp.getJson(diskInfo)

    def setControlApi(self):
        stype = request.form.get('type', '')
        day = request.form.get('day', '')
        data = self.setControl(stype, day)
        return data

    def getLoadAverageApi(self):
        start = request.args.get('start', '')
        end = request.args.get('end', '')
        data = self.getLoadAverageData(start, end)
        return slemp.getJson(data)

    def getCpuIoApi(self):
        start = request.args.get('start', '')
        end = request.args.get('end', '')
        data = self.getCpuIoData(start, end)
        return slemp.getJson(data)

    def getDiskIoApi(self):
        start = request.args.get('start', '')
        end = request.args.get('end', '')
        data = self.getDiskIoData(start, end)
        return slemp.getJson(data)

    def getNetworkIoApi(self):
        start = request.args.get('start', '')
        end = request.args.get('end', '')
        data = self.getNetWorkIoData(start, end)
        return slemp.getJson(data)

    def rememoryApi(self):
        os.system('sync')
        scriptFile = slemp.getRunDir() + '/script/rememory.sh'
        slemp.execShell("/bin/bash " + scriptFile)
        data = self.getMemInfo()
        return slemp.getJson(data)

    # restart panel
    def restartApi(self):
        self.restartSlemp()
        return slemp.returnJson(True, 'Panel has restarted!')

    def restartServerApi(self):
        if slemp.isAppleSystem():
            return slemp.returnJson(False, "The development environment cannot be restarted")
        self.restartServer()
        return slemp.returnJson(True, 'Restarting server!')
    ##### ----- end ----- ###

    @async
    def restartSlemp(self):
        sleep(0.3)
        # cmd = slemp.getRunDir() + '/scripts/init.d/slemp restart'
        # print cmd
        slemp.execShell('service slemp restart')

    @async
    def restartServer(self):
        if not slemp.isRestart():
            return slemp.returnJson(False, 'Please wait for all installation tasks to complete before executing!')
        slemp.execShell("sync && init 6 &")
        return slemp.returnJson(True, 'Command sent successfully!')

        # name PID
    def getPid(self, pname):
        try:
            if not self.pids:
                self.pids = psutil.pids()
            for pid in self.pids:
                if psutil.Process(pid).name() == pname:
                    return True
            return False
        except:
            return False

    # Check if the port is occupied
    def isOpen(self, port):
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(('127.0.0.1', int(port)))
            s.shutdown(2)
            return True
        except:
            return False

    # Check if the specified process is alive
    def checkProcess(self, pid):
        try:
            if not self.pids:
                self.pids = psutil.pids()
            if int(pid) in self.pids:
                return True
            return False
        except:
            return False

    def getPanelInfo(self, get=None):
        # Take the panel configuration
        address = slemp.GetLocalIp()
        try:
            try:
                port = web.ctx.host.split(':')[1]
            except:
                port = slemp.readFile('data/port.pl')
        except:
            port = '7200'
        domain = ''
        if os.path.exists('data/domain.conf'):
            domain = slemp.readFile('data/domain.conf')

        autoUpdate = ''
        if os.path.exists('data/autoUpdate.pl'):
            autoUpdate = 'checked'
        limitip = ''
        if os.path.exists('data/limitip.conf'):
            limitip = slemp.readFile('data/limitip.conf')

        templates = []
        for template in os.listdir('templates/'):
            if os.path.isdir('templates/' + template):
                templates.append(template)
        template = slemp.readFile('data/templates.pl')

        check502 = ''
        if os.path.exists('data/502Task.pl'):
            check502 = 'checked'
        return {'port': port, 'address': address, 'domain': domain, 'auto': autoUpdate, '502': check502, 'limitip': limitip, 'templates': templates, 'template': template}

    def getSystemTotal(self, interval=1):
        # Get system statistics
        data = self.getMemInfo()
        cpu = self.getCpuInfo(interval)
        data['cpuNum'] = cpu[1]
        data['cpuRealUsed'] = cpu[0]
        data['time'] = self.getBootTime()
        data['system'] = self.getSystemVersion()
        data['isuser'] = slemp.M('users').where(
            'username=?', ('admin',)).count()
        data['version'] = '0.0.1'
        return data

    def getLoadAverage(self):
        c = os.getloadavg()
        data = {}
        data['one'] = float(c[0])
        data['five'] = float(c[1])
        data['fifteen'] = float(c[2])
        data['max'] = psutil.cpu_count() * 2
        data['limit'] = data['max']
        data['safe'] = data['max'] * 0.75
        return data

    def getAllInfo(self, get):
        data = {}
        data['load_average'] = self.GetLoadAverage(get)
        data['title'] = self.GetTitle()
        data['network'] = self.GetNetWorkApi(get)
        data['panel_status'] = not os.path.exists(
            '/home/slemp/server/panel/data/close.pl')
        import firewalls
        ssh_info = firewalls.firewalls().GetSshInfo(None)
        data['enable_ssh_status'] = ssh_info['status']
        data['disable_ping_status'] = not ssh_info['ping']
        data['time'] = self.GetBootTime()
        # data['system'] = self.GetSystemVersion();
        # data['mem'] = self.GetMemInfo();
        data['version'] = web.ctx.session.version
        return data

    def getTitle(self):
        titlePl = 'data/title.pl'
        title = 'SLEMP Panel'
        if os.path.exists(titlePl):
            title = slemp.readFile(titlePl).strip()
        return title

    def getSystemVersion(self):
        # Get the OS version
        if slemp.getOs() == 'darwin':
            data = slemp.execShell('sw_vers')[0]
            data_list = data.strip().split("\n")
            mac_version = ''
            for x in data_list:
                mac_version += x.split("\t")[1] + ' '
            return mac_version

        version = slemp.readFile('/etc/redhat-release')
        if not version:
            version = slemp.readFile(
                '/etc/issue').strip().split("\n")[0].replace('\\n', '').replace('\l', '').strip()
        else:
            version = version.replace('release ', '').strip()
        return version

    def getBootTime(self):
        # Get system startup time
        start_time = psutil.boot_time()
        run_time = time.time() - start_time
        # conf = slemp.readFile('/proc/uptime').split()
        tStr = float(run_time)
        min = tStr / 60
        hours = min / 60
        days = math.floor(hours / 24)
        hours = math.floor(hours - (days * 24))
        min = math.floor(min - (days * 60 * 24) - (hours * 60))
        return slemp.getInfo('{1} Hari {2} Jam {3} Menit', (str(int(days)), str(int(hours)), str(int(min))))

    def getCpuInfo(self, interval=1):
        # Get CPU information
        cpuCount = psutil.cpu_count()
        used = psutil.cpu_percent(interval=interval)
        return used, cpuCount

    def getMemInfo(self):
        # Get memory information
        mem = psutil.virtual_memory()
        if slemp.getOs() == 'darwin':
            memInfo = {
                'memTotal': mem.total / 1024 / 1024
            }
            memInfo['memRealUsed'] = memInfo['memTotal'] * (mem.percent / 100)
        else:
            memInfo = {
                'memTotal': mem.total / 1024 / 1024,
                'memFree': mem.free / 1024 / 1024,
                'memBuffers': mem.buffers / 1024 / 1024,
                'memCached': mem.cached / 1024 / 1024
            }

            memInfo['memRealUsed'] = memInfo['memTotal'] - \
                memInfo['memFree'] - memInfo['memBuffers'] - \
                memInfo['memCached']
        return memInfo

    def getMemUsed(self):
        # fetch memory usage
        try:
            import psutil
            mem = psutil.virtual_memory()

            if slemp.getOs() == 'darwin':
                return mem.percent

            memInfo = {'memTotal': mem.total / 1024 / 1024, 'memFree': mem.free / 1024 / 1024,
                       'memBuffers': mem.buffers / 1024 / 1024, 'memCached': mem.cached / 1024 / 1024}
            tmp = memInfo['memTotal'] - memInfo['memFree'] - \
                memInfo['memBuffers'] - memInfo['memCached']
            tmp1 = memInfo['memTotal'] / 100
            return (tmp / tmp1)
        except Exception, ex:
            return 1

    def getDiskInfo(self, get=None):
        return self.getDiskInfo2()
        # Get disk partition information
        diskIo = psutil.disk_partitions()
        diskInfo = []

        for disk in diskIo:
            if disk[1] == '/mnt/cdrom':
                continue
            if disk[1] == '/boot':
                continue
            tmp = {}
            tmp['path'] = disk[1]
            tmp['size'] = psutil.disk_usage(disk[1])
            diskInfo.append(tmp)
        return diskInfo

    def getDiskInfo2(self):
        # Get disk partition information
        temp = slemp.execShell(
            "df -h -P|grep '/'|grep -v tmpfs | grep -v devfs")[0]
        tempInodes = slemp.execShell(
            "df -i -P|grep '/'|grep -v tmpfs | grep -v devfs")[0]
        temp1 = temp.split('\n')
        tempInodes1 = tempInodes.split('\n')
        diskInfo = []
        n = 0
        cuts = ['/mnt/cdrom', '/boot', '/boot/efi', '/dev',
                '/dev/shm', '/run/lock', '/run', '/run/shm', '/run/user']
        for tmp in temp1:
            n += 1
            inodes = tempInodes1[n - 1].split()
            disk = tmp.split()
            if len(disk) < 5:
                continue
            if disk[1].find('M') != -1:
                continue
            if disk[1].find('K') != -1:
                continue
            if len(disk[5].split('/')) > 4:
                continue
            if disk[5] in cuts:
                continue
            arr = {}
            arr['path'] = disk[5]
            tmp1 = [disk[1], disk[2], disk[3], disk[4]]
            arr['size'] = tmp1
            arr['inodes'] = [inodes[1], inodes[2], inodes[3], inodes[4]]
            if disk[5] == '/':
                bootLog = os.getcwd() + '/tmp/panelBoot.pl'
                if disk[2].find('M') != -1:
                    if os.path.exists(bootLog):
                        os.system('rm -f ' + bootLog)
                else:
                    if not os.path.exists(bootLog):
                        pass
            if inodes[2] != '0':
                diskInfo.append(arr)
        return diskInfo

    # Clean up system junk
    def clearSystem(self, get):
        count = total = 0
        tmp_total, tmp_count = self.ClearMail()
        count += tmp_count
        total += tmp_total
        tmp_total, tmp_count = self.ClearOther()
        count += tmp_count
        total += tmp_total
        return count, total

    # Clean up mail log
    def clearMail(self):
        rpath = '/var/spool'
        total = count = 0
        import shutil
        con = ['cron', 'anacron', 'mail']
        for d in os.listdir(rpath):
            if d in con:
                continue
            dpath = rpath + '/' + d
            time.sleep(0.2)
            num = size = 0
            for n in os.listdir(dpath):
                filename = dpath + '/' + n
                fsize = os.path.getsize(filename)
                size += fsize
                if os.path.isdir(filename):
                    shutil.rmtree(filename)
                else:
                    os.remove(filename)
                print '\t\033[1;32m[OK]\033[0m'
                num += 1
            total += size
            count += num
        return total, count

    # clean up other
    def clearOther(self):
        clearPath = [
            {'path': '/home/slemp/server/panel', 'find': 'testDisk_'},
            {'path': '/home/slemp/wwwlogs', 'find': 'log'},
            {'path': '/tmp', 'find': 'panelBoot.pl'},
            {'path': '/home/slemp/server/panel/install', 'find': '.rpm'}
        ]

        total = count = 0
        for c in clearPath:
            for d in os.listdir(c['path']):
                if d.find(c['find']) == -1:
                    continue
                filename = c['path'] + '/' + d
                fsize = os.path.getsize(filename)
                total += fsize
                if os.path.isdir(filename):
                    shutil.rmtree(filename)
                else:
                    os.remove(filename)
                count += 1
        slemp.serviceReload()
        os.system('echo > /tmp/panelBoot.pl')
        return total, count

    def getNetWork(self):
        # return self.GetNetWorkApi(get);
        # Get network traffic information
        try:
            # Get network traffic information
            networkIo = psutil.net_io_counters()[:4]
            if not "otime" in session:
                session['up'] = networkIo[0]
                session['down'] = networkIo[1]
                session['otime'] = time.time()

            ntime = time.time()
            networkInfo = {}
            networkInfo['upTotal'] = networkIo[0]
            networkInfo['downTotal'] = networkIo[1]
            networkInfo['up'] = round(float(
                networkIo[0] - session['up']) / 1024 / (ntime - session['otime']), 2)
            networkInfo['down'] = round(
                float(networkIo[1] - session['down']) / 1024 / (ntime - session['otime']), 2)
            networkInfo['downPackets'] = networkIo[3]
            networkInfo['upPackets'] = networkIo[2]

            # print networkIo[1], session['down'], ntime, session['otime']
            session['up'] = networkIo[0]
            session['down'] = networkIo[1]
            session['otime'] = time.time()

            networkInfo['cpu'] = self.getCpuInfo()
            networkInfo['load'] = self.getLoadAverage()
            networkInfo['mem'] = self.getMemInfo()

            return networkInfo
        except Exception, e:
            print e
            return None

    def getNetWorkApi(self):
        # Get network traffic information
        try:
            tmpfile = 'data/network.temp'
            networkIo = psutil.net_io_counters()[:4]

            if not os.path.exists(tmpfile):
                slemp.writeFile(tmpfile, str(
                    networkIo[0]) + '|' + str(networkIo[1]) + '|' + str(int(time.time())))

            lastValue = slemp.readFile(tmpfile).split('|')

            ntime = time.time()
            networkInfo = {}
            networkInfo['upTotal'] = networkIo[0]
            networkInfo['downTotal'] = networkIo[1]
            networkInfo['up'] = round(
                float(networkIo[0] - int(lastValue[0])) / 1024 / (ntime - int(lastValue[2])), 2)
            networkInfo['down'] = round(
                float(networkIo[1] - int(lastValue[1])) / 1024 / (ntime - int(lastValue[2])), 2)
            networkInfo['downPackets'] = networkIo[3]
            networkInfo['upPackets'] = networkIo[2]

            slemp.writeFile(tmpfile, str(
                networkIo[0]) + '|' + str(networkIo[1]) + '|' + str(int(time.time())))

            # networkInfo['cpu'] = self.GetCpuInfo(0.1)
            return networkInfo
        except:
            return None

    def getNetWorkIoData(self, start, end):
        # Get the network Io of the specified time period
        data = slemp.M('network').dbfile('system').where("addtime>=? AND addtime<=?", (start, end)).field(
            'id,up,down,total_up,total_down,down_packets,up_packets,addtime').order('id asc').select()
        return self.toAddtime(data)

    def getDiskIoData(self, start, end):
        # Get the disk Io of the specified time period
        data = slemp.M('diskio').dbfile('system').where("addtime>=? AND addtime<=?", (start, end)).field(
            'id,read_count,write_count,read_bytes,write_bytes,read_time,write_time,addtime').order('id asc').select()
        return self.toAddtime(data)

    def getCpuIoData(self, start, end):
        # Get the CpuIo of the specified time period
        data = slemp.M('cpuio').dbfile('system').where("addtime>=? AND addtime<=?",
                                                    (start, end)).field('id,pro,mem,addtime').order('id asc').select()
        return self.toAddtime(data, True)

    def getLoadAverageData(self, start, end):
        data = slemp.M('load_average').dbfile('system').where("addtime>=? AND addtime<=?", (
            start, end)).field('id,pro,one,five,fifteen,addtime').order('id asc').select()
        return self.toAddtime(data)

    # format the addtime column
    def toAddtime(self, data, tomem=False):
        import time
        if tomem:
            import psutil
            mPre = (psutil.virtual_memory().total / 1024 / 1024) / 100
        length = len(data)
        he = 1
        if length > 100:
            he = 1
        if length > 1000:
            he = 3
        if length > 10000:
            he = 15
        if he == 1:
            for i in range(length):
                data[i]['addtime'] = time.strftime(
                    '%m/%d %H:%M', time.localtime(float(data[i]['addtime'])))
                if tomem and data[i]['mem'] > 100:
                    data[i]['mem'] = data[i]['mem'] / mPre

            return data
        else:
            count = 0
            tmp = []
            for value in data:
                if count < he:
                    count += 1
                    continue
                value['addtime'] = time.strftime(
                    '%m/%d %H:%M', time.localtime(float(value['addtime'])))
                if tomem and value['mem'] > 100:
                    value['mem'] = value['mem'] / mPre
                tmp.append(value)
                count = 0
            return tmp

    def setControl(self, stype, day):

        filename = 'data/control.conf'

        if stype == '0':
            slemp.execShell("rm -f " + filename)
        elif stype == '1':
            _day = int(day)
            if _day < 1:
                return slemp.returnJson(False, "Setup failed!")
            slemp.writeFile(filename, day)
        elif stype == 'del':
            if not slemp.isRestart():
                return slemp.returnJson(False, 'Please wait for all installation tasks to complete before executing')
            os.remove("data/system.db")

            sql = db.Sql().dbfile('system')
            csql = slemp.readFile('data/sql/system.sql')
            csql_list = csql.split(';')
            for index in range(len(csql_list)):
                sql.execute(csql_list[index], ())
            return slemp.returnJson(True, "Monitoring service is down")
        else:
            data = {}
            if os.path.exists(filename):
                try:
                    data['day'] = int(slemp.readFile(filename))
                except:
                    data['day'] = 30
                data['status'] = True
            else:
                data['day'] = 30
                data['status'] = False
            return slemp.getJson(data)

        return slemp.returnJson(True, "Set up successfully!")

    def versionDiff(self, old, new):
        '''
            test test
            new  new version
            none no new version
        '''
        new_list = new.split('.')
        if len(new_list) > 3:
            return 'test'

        old_list = old.split('.')
        ret = 'none'

        isHasNew = True
        if int(new_list[0]) == int(old_list[0]) and int(new_list[1]) == int(old_list[1]) and int(new_list[2]) == int(old_list[2]):
            isHasNew = False

        if isHasNew:
            return 'new'
        return ret

    def getServerInfo(self):
        upAddr = 'https://raw.githubusercontent.com/basoro/slemp/main/version/info.json'
        try:
            requests.adapters.DEFAULT_RETRIES = 2
            r = requests.get(upAddr, verify=False)
            version = json.loads(r.content)
            return version[0]
        except Exception as e:
            print 'getServerInfo', e
        return {}

    def updateServer(self, stype, version=''):
        # Update service
        try:
            if not slemp.isRestart():
                return slemp.returnJson(False, 'Please wait for all installation tasks to complete before executing!')

            if stype == 'check':
                version_now = config_api.config_api().getVersion()
                version_new_info = self.getServerInfo()
                if not 'version' in version_new_info:
                    return slemp.returnJson(False, 'There is a problem with the server data or network!')

                diff = self.versionDiff(
                    version_now, version_new_info['version'])
                if diff == 'new':
                    return slemp.returnJson(True, 'There is a new version!', version_new_info['version'])
                elif diff == 'test':
                    return slemp.returnJson(True, 'There is a beta version!', version_new_info['version'])
                else:
                    return slemp.returnJson(False, 'Already up to date, no need to update!')

            if stype == 'info':
                version_new_info = self.getServerInfo()
                version_now = config_api.config_api().getVersion()

                if not 'version' in version_new_info:
                    return slemp.returnJson(False, 'There is a problem with the server data!')
                diff = self.versionDiff(
                    version_now, version_new_info['version'])
                return slemp.returnJson(True, 'Update information!', version_new_info)

            if stype == 'update':
                if version == '':
                    return slemp.returnJson(False, 'Missing version information!')

                v_new_info = self.getServerInfo()
                if v_new_info['version'] != version:
                    return slemp.returnJson(False, 'Update failed, please try again!')

                if not 'path' in v_new_info or v_new_info['path'] == '':
                    return slemp.returnJson(False, 'The download address does not exist!')

                newUrl = v_new_info['path']
                toPath = slemp.getRootDir() + '/temp'
                if not os.path.exists(toPath):
                    slemp.execShell('mkdir -p ' + toPath)

                slemp.execShell('wget -O ' + toPath + '/slemp.zip ' + newUrl)

                slemp.execShell('unzip -o ' + toPath + '/slemp.zip' + ' -d ./')
                slemp.execShell('unzip -o slemp.zip -d ./')
                slemp.execShell('rm -f slemp.zip')
                return slemp.returnJson(True, 'The update is installed successfully, you need to restart yourself!')

            return slemp.returnJson(False, 'Already up to date, no need to update!')
        except Exception as ex:
            print 'updateServer', ex
            return slemp.returnJson(False, "Connection failure!")

    # Repair panel
    def repPanel(self, get):
        updateAddr = 'https://raw.githubusercontent.com/basoro/slemp/main'
        #vp = ''
        #if slemp.readFile('/home/slemp/server/panel/class/common.py').find('checkSafe') != -1:
        #    vp = '_pro'
        #slemp.ExecShell("wget -O update.sh " + slemp.get_url() +
        #             "/install/update" + vp + ".sh && bash update.sh")
        #if hasattr(web.ctx.session, 'getCloudPlugin'):
        #    del(web.ctx.session['getCloudPlugin'])
        slemp.ExecShell("wget -O update.sh " + updateAddr +
                     "/scripts/update.sh && bash update.sh")
        return True
