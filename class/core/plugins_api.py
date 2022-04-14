# coding: utf-8

import psutil
import time
import os
import slemp
import re
import json

import sys
reload(sys)
sys.setdefaultencoding('utf8')

import threading
import multiprocessing


from flask import request


class pa_thread(threading.Thread):

    def __init__(self, func, args, name=''):
        threading.Thread.__init__(self)
        self.name = name
        self.func = func
        self.args = args
        self.result = self.func(*self.args)

    def getResult(self):
        try:
            return self.result
        except Exception:
            return None


class plugins_api:
    __tasks = None
    __plugin_dir = 'plugins'
    __type = 'data/json/type.json'
    __index = 'data/json/index.json'
    setupPath = None

    def __init__(self):
        self.setupPath = 'server'

    ##### ----- start ----- ###
    def listApi(self):
        sType = request.args.get('type', '0')
        sPage = request.args.get('p', '1')
        # print sPage
        data = self.getPluginList(sType, int(sPage))
        return slemp.getJson(data)

    def fileApi(self):
        name = request.args.get('name', '')
        if name.strip() == '':
            return ''

        f = request.args.get('f', '')
        if f.strip() == '':
            return ''

        file = self.__plugin_dir + '/' + name + '/' + f
        if not os.path.exists(file):
            return ''

        c = slemp.readFile(file)
        return c

    def indexListApi(self):
        data = self.getIndexList()
        return slemp.getJson(data)

    def indexSortApi(self):
        sort = request.form.get('ssort', '')
        if sort.strip() == '':
            return slemp.returnJson(False, 'Sort data cannot be empty!')
        data = self.setIndexSort(sort)
        if data:
            return slemp.returnJson(True, 'Success!')
        return slemp.returnJson(False, 'Fail!')

    def installApi(self):
        rundir = slemp.getRunDir()
        name = request.form.get('name', '')
        version = request.form.get('version', '')

        mmsg = 'Install'
        if hasattr(request.form, 'upgrade'):
            mtype = 'update'
            mmsg = 'upgrade'

        if name.strip() == '':
            return slemp.returnJson(False, 'Missing plugin name!', ())

        if version.strip() == '':
            return slemp.returnJson(False, 'Missing version information!', ())

        infoJsonPos = self.__plugin_dir + '/' + name + '/' + 'info.json'
        # print infoJsonPos

        if not os.path.exists(infoJsonPos):
            return slemp.returnJson(False, 'Configuration file does not exist!', ())

        pluginInfo = json.loads(slemp.readFile(infoJsonPos))

        execstr = "cd " + os.getcwd() + "/plugins/" + \
            name + " && /bin/bash " + pluginInfo["shell"] \
            + " install " + version

        taskAdd = (None, mmsg + '[' + name + '-' + version + ']',
                   'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), execstr)

        slemp.M('tasks').add('id,name,type,status,addtime, execstr', taskAdd)
        return slemp.returnJson(True, 'Install task added to queue!')

    def uninstallOldApi(self):
        rundir = slemp.getRunDir()
        name = request.form.get('name', '')
        version = request.form.get('version', '')
        if name.strip() == '':
            return slemp.returnJson(False, "Missing plugin name!", ())

        if version.strip() == '':
            return slemp.returnJson(False, "Missing version information!", ())

        infoJsonPos = self.__plugin_dir + '/' + name + '/' + 'info.json'

        if not os.path.exists(infoJsonPos):
            return slemp.returnJson(False, "Configuration file does not exist!", ())

        pluginInfo = json.loads(slemp.readFile(infoJsonPos))

        execstr = "cd " + os.getcwd() + "/plugins/" + \
            name + " && /bin/bash " + pluginInfo["shell"] \
            + " uninstall " + version

        taskAdd = (None, 'uninstall [' + name + '-' + version + ']',
                   'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), execstr)

        slemp.M('tasks').add('id,name,type,status,addtime, execstr', taskAdd)
        return slemp.returnJson(True, 'Uninstall task added to queue!')

    # The uninstall time is short, and it is not added to the task...
    def uninstallApi(self):
        rundir = slemp.getRunDir()
        name = request.form.get('name', '')
        version = request.form.get('version', '')
        if name.strip() == '':
            return slemp.returnJson(False, "Missing plugin name!", ())

        if version.strip() == '':
            return slemp.returnJson(False, "Missing version information!", ())

        infoJsonPos = self.__plugin_dir + '/' + name + '/' + 'info.json'

        if not os.path.exists(infoJsonPos):
            return slemp.returnJson(False, "Configuration file does not exist!", ())

        pluginInfo = json.loads(slemp.readFile(infoJsonPos))

        execstr = "cd " + os.getcwd() + "/plugins/" + \
            name + " && /bin/bash " + pluginInfo["shell"] \
            + " uninstall " + version

        data = slemp.execShell(execstr)
        if slemp.isAppleSystem():
            print execstr
            print data[0], data[1]
        return slemp.returnJson(True, 'Uninstallation performed successfully!')
        # if data[1] == '':
        #     return slemp.returnJson(True, 'Uninstalled successfully!')
        # else:
        #     return slemp.returnJson(False, 'Uninstalling error message!' + data[1])

    def checkApi(self):
        name = request.form.get('name', '')
        if name.strip() == '':
            return slemp.returnJson(False, "Missing plugin name!", ())

        infoJsonPos = self.__plugin_dir + '/' + name + '/' + 'info.json'
        if not os.path.exists(infoJsonPos):
            return slemp.returnJson(False, "Configuration file does not exist!", ())
        return slemp.returnJson(True, "Plugin exists!", ())

    def setIndexApi(self):
        name = request.form.get('name', '')
        status = request.form.get('status', '0')
        version = request.form.get('version', '')
        if status == '1':
            return self.addIndex(name, version)
        return self.removeIndex(name, version)

    def settingApi(self):
        name = request.args.get('name', '')
        html = self.__plugin_dir + '/' + name + '/index.html'
        return slemp.readFile(html)

    def runApi(self):
        name = request.form.get('name', '')
        func = request.form.get('func', '')
        version = request.form.get('version', '')
        args = request.form.get('args', '')
        script = request.form.get('script', 'index')

        data = self.run(name, func, version, args, script)
        if data[1] == '':
            return slemp.returnJson(True, "OK", data[0].strip())
        return slemp.returnJson(False, data[1].strip())

    def callbackApi(self):
        name = request.form.get('name', '')
        func = request.form.get('func', '')
        args = request.form.get('args', '')
        script = request.form.get('script', 'index')

        data = self.callback(name, func, args, script)
        if data[0]:
            return slemp.returnJson(True, "OK", data[1])
        return slemp.returnJson(False, data[1])

    def updateZipApi(self):
        tmp_path = slemp.getRootDir() + '/temp'
        if not os.path.exists(tmp_path):
            os.makedirs(tmp_path)
        slemp.execShell("rm -rf " + tmp_path + '/*')

        tmp_file = tmp_path + '/plugin_tmp.zip'
        from werkzeug.utils import secure_filename
        from flask import request
        f = request.files['plugin_zip']
        if f.filename[-4:] != '.zip':
            return slemp.returnJson(False, 'Only zip files are supported!')
        f.save(tmp_file)
        slemp.execShell('cd ' + tmp_path + ' && unzip ' + tmp_file)
        os.remove(tmp_file)

        p_info = tmp_path + '/info.json'
        if not os.path.exists(p_info):
            d_path = None
            for df in os.walk(tmp_path):
                if len(df[2]) < 3:
                    continue
                if not 'info.json' in df[2]:
                    continue
                if not 'install.sh' in df[2]:
                    continue
                if not os.path.exists(df[0] + '/info.json'):
                    continue
                d_path = df[0]
            if d_path:
                tmp_path = d_path
                p_info = tmp_path + '/info.json'
        try:
            data = json.loads(slemp.readFile(p_info))
            data['size'] = slemp.getPathSize(tmp_path)
            if not 'author' in data:
                data['author'] = 'Unknown'
            if not 'home' in data:
                data['home'] = 'http://basoro.org/support'
            plugin_path = slemp.getPluginDir() + data['name'] + '/info.json'
            data['old_version'] = '0'
            data['tmp_path'] = tmp_path
            if os.path.exists(plugin_path):
                try:
                    old_info = json.loads(slemp.ReadFile(plugin_path))
                    data['old_version'] = old_info['versions']
                except:
                    pass
        except:
            slemp.execShell("rm -rf " + tmp_path)
            return slemp.returnJson(False, 'No plugin information found in the compressed package, please check the plugin package!')
        protectPlist = ('openresty', 'mysql', 'php', 'csvn', 'gogs', 'pureftp')
        if data['name'] in protectPlist:
            return slemp.returnJson(False, '[' + data['name'] + '], Important plugins cannot be modified!')
        return slemp.getJson(data)

    def inputZipApi(self):
        plugin_name = request.form.get('plugin_name', '')
        tmp_path = request.form.get('tmp_path', '')

        if not os.path.exists(tmp_path):
            return slemp.returnJson(False, 'The temporary file does not exist, please upload again!')
        plugin_path = slemp.getPluginDir() + '/' + plugin_name
        if not os.path.exists(plugin_path):
            print slemp.execShell('mkdir -p ' + plugin_path)
        slemp.execShell("\cp -rf " + tmp_path + '/* ' + plugin_path + '/')
        slemp.execShell('chmod -R 755 ' + plugin_path)
        p_info = slemp.readFile(plugin_path + '/info.json')
        if p_info:
            slemp.writeLog('Software management', 'Install third-party plugins [%s]' %
                        json.loads(p_info)['title'])
            return slemp.returnJson(True, 'Successful installation!')
        slemp.execShell("rm -rf " + plugin_path)
        return slemp.returnJson(False, 'Installation failed!')
    ##### ----- end ----- ###

    # does the process exist
    def processExists(self, pname, exe=None):
        try:
            if not self.pids:
                self.pids = psutil.pids()
            for pid in self.pids:
                try:
                    p = psutil.Process(pid)
                    if p.name() == pname:
                        if not exe:
                            return True
                        else:
                            if p.exe() == exe:
                                return True
                except:
                    pass
            return False
        except:
            return True

    # Check if it is installing
    def checkSetupTask(self, sName, sVer, sCoexist):
        if not self.__tasks:
            self.__tasks = slemp.M('tasks').where(
                "status!=?", ('1',)).field('status,name').select()
        isTask = '1'
        for task in self.__tasks:
            tmpt = slemp.getStrBetween('[', ']', task['name'])
            if not tmpt:
                continue
            tmp1 = tmpt.split('-')
            name1 = tmp1[0].lower()
            if sCoexist:
                if name1 == sName and tmp1[1] == sVer:
                    isTask = task['status']
            else:
                if name1 == sName:
                    isTask = task['status']
        return isTask

    def checkStatus(self, info):
        if not info['setup']:
            return False

        data = self.run(info['name'], 'status', info['setup_version'])
        if data[0] == 'start':
            return True
        return False

    def checkStatusProcess(self, info, i, return_dict):
        if not info['setup']:
            return_dict[i] = False
            return

        data = self.run(info['name'], 'status', info['setup_version'])
        if data[0] == 'start':
            return_dict[i] = True
        else:
            return_dict[i] = False

    def checkStatusThreads(self, info, i):
        if not info['setup']:
            return False
        data = self.run(info['name'], 'status', info['setup_version'])
        if data[0] == 'start':
            return True
        else:
            return False

    def checkStatusMThreads(self, plugins_info):
        try:
            threads = []
            ntmp_list = range(len(plugins_info))
            for i in ntmp_list:
                t = pa_thread(self.checkStatusThreads, (plugins_info[i], i))
                threads.append(t)

            for i in ntmp_list:
                threads[i].start()
            for i in ntmp_list:
                threads[i].join()

            for i in ntmp_list:
                t = threads[i].getResult()
                plugins_info[i]['status'] = t
        except Exception as e:
            print 'checkStatusMThreads:', str(e)

        return plugins_info

    def checkStatusMProcess(self, plugins_info):
        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        jobs = []
        for i in range(len(plugins_info)):
            p = multiprocessing.Process(
                target=self.checkStatusProcess, args=(plugins_info[i], i, return_dict))
            jobs.append(p)
            p.start()

        for proc in jobs:
            proc.join()

        returnData = return_dict.values()
        for i in ntmp_list:
            plugins_info[i]['status'] = returnData[i]

        return plugins_info

    def checkDisplayIndex(self, name, version):
        if not os.path.exists(self.__index):
            slemp.writeFile(self.__index, '[]')

        indexList = json.loads(slemp.readFile(self.__index))
        if type(version) == list:
            for index in range(len(version)):
                vname = name + '-' + version[index]
                if vname in indexList:
                    return True
        else:
            vname = name + '-' + version
            if vname in indexList:
                return True
        return False

    def getVersion(self, path):
        version_f = path + '/version.pl'
        if os.path.exists(version_f):
            return slemp.readFile(version_f).strip()
        return ''

     # Construct local plugin information
    def getPluginInfo(self, info):
        checks = ''
        path = ''
        coexist = False

        if info["checks"][0:1] == '/':
            checks = info["checks"]
        else:
            checks = slemp.getRootDir() + '/' + info['checks']

        if info.has_key('path'):
            path = info['path']

        if path[0:1] != '/':
            path = slemp.getRootDir() + '/' + path

        if info.has_key('coexist') and info['coexist']:
            coexist = True

        pInfo = {
            "id": 10000,
            "pid": info['pid'],
            "type": 1000,
            "name": info['name'],
            "title": info['title'],
            "ps": info['ps'],
            "dependnet": "",
            "mutex": "",
            "path": path,
            "install_checks": checks,
            "uninsatll_checks": checks,
            "coexist": coexist,
            "versions": info['versions'],
            # "updates": info['updates'],
            "display": False,
            "setup": False,
            "setup_version": "",
            "status": False,
        }

        if checks.find('VERSION') > -1:
            pInfo['install_checks'] = checks.replace(
                'VERSION', info['versions'])

        if path.find('VERSION') > -1:
            pInfo['path'] = path.replace(
                'VERSION', info['versions'])

        pInfo['task'] = self.checkSetupTask(
            pInfo['name'], info['versions'], coexist)
        pInfo['display'] = self.checkDisplayIndex(
            info['name'], pInfo['versions'])

        pInfo['setup'] = os.path.exists(pInfo['install_checks'])

        if coexist and pInfo['setup']:
            pInfo['setup_version'] = info['versions']
        else:
            pInfo['setup_version'] = self.getVersion(pInfo['install_checks'])
        # pluginInfo['status'] = self.checkStatus(pluginInfo)
        pInfo['status'] = False
        return pInfo

    def makeCoexist(self, data):
        plugins_info = []
        for index in range(len(data['versions'])):
            tmp = data.copy()
            tmp['title'] = tmp['title'] + \
                '-' + data['versions'][index]
            tmp['versions'] = data['versions'][index]
            pg = self.getPluginInfo(tmp)
            plugins_info.append(pg)

        return plugins_info

    def makeList(self, data, sType='0'):
        plugins_info = []

        if (data['pid'] == sType):
            if type(data['versions']) == list and data.has_key('coexist') and data['coexist']:
                tmp_data = self.makeCoexist(data)
                for index in range(len(tmp_data)):
                    plugins_info.append(tmp_data[index])
            else:
                pg = self.getPluginInfo(data)
                plugins_info.append(pg)
            return plugins_info

        if sType == '0':
            if type(data['versions']) == list and data.has_key('coexist') and data['coexist']:
                tmp_data = self.makeCoexist(data)
                for index in range(len(tmp_data)):
                    plugins_info.append(tmp_data[index])
            else:
                pg = self.getPluginInfo(data)
                plugins_info.append(pg)

        # print plugins_info, data
        return plugins_info

    def getAllList(self, sType='0'):
        plugins_info = []
        for dirinfo in os.listdir(self.__plugin_dir):
            if dirinfo[0:1] == '.':
                continue
            path = self.__plugin_dir + '/' + dirinfo
            if os.path.isdir(path):
                json_file = path + '/info.json'
                if os.path.exists(json_file):
                    try:
                        data = json.loads(slemp.readFile(json_file))
                        tmp_data = self.makeList(data, sType)
                        for index in range(len(tmp_data)):
                            plugins_info.append(tmp_data[index])
                    except Exception, e:
                        print e
        return plugins_info

    def getAllListPage(self, sType='0', page=1, pageSize=10):
        plugins_info = []
        for dirinfo in os.listdir(self.__plugin_dir):
            if dirinfo[0:1] == '.':
                continue
            path = self.__plugin_dir + '/' + dirinfo
            if os.path.isdir(path):
                json_file = path + '/info.json'
                if os.path.exists(json_file):
                    try:
                        data = json.loads(slemp.readFile(json_file))
                        tmp_data = self.makeList(data, sType)
                        for index in range(len(tmp_data)):
                            plugins_info.append(tmp_data[index])
                    except Exception, e:
                        print e

        start = (page - 1) * pageSize
        end = start + pageSize
        _plugins_info = plugins_info[start:end]

        _plugins_info = self.checkStatusMThreads(_plugins_info)
        return (_plugins_info, len(plugins_info))

    def makeListThread(self, data, sType='0'):
        plugins_info = []

        if (data['pid'] == sType):
            if type(data['versions']) == list and data.has_key('coexist') and data['coexist']:
                tmp_data = self.makeCoexist(data)
                for index in range(len(tmp_data)):
                    plugins_info.append(tmp_data[index])
            else:
                pg = self.getPluginInfo(data)
                plugins_info.append(pg)
            return plugins_info

        if sType == '0':
            if type(data['versions']) == list and data.has_key('coexist') and data['coexist']:
                tmp_data = self.makeCoexist(data)
                for index in range(len(tmp_data)):
                    plugins_info.append(tmp_data[index])
            else:
                pg = self.getPluginInfo(data)
                plugins_info.append(pg)

        # print plugins_info, data
        return plugins_info

    def getAllListThread(self, sType='0'):
        plugins_info = []
        tmp_list = []
        threads = []
        for dirinfo in os.listdir(self.__plugin_dir):
            if dirinfo[0:1] == '.':
                continue
            path = self.__plugin_dir + '/' + dirinfo
            if os.path.isdir(path):
                json_file = path + '/info.json'
                if os.path.exists(json_file):
                    data = json.loads(slemp.readFile(json_file))
                    if sType == '0':
                        tmp_list.append(data)

                    if (data['pid'] == sType):
                        tmp_list.append(data)

        ntmp_list = range(len(tmp_list))
        for i in ntmp_list:
            t = pa_thread(self.makeListThread, (tmp_list[i], sType))
            threads.append(t)
        for i in ntmp_list:
            threads[i].start()
        for i in ntmp_list:
            threads[i].join()

        for i in ntmp_list:
            t = threads[i].getResult()
            for index in range(len(t)):
                plugins_info.append(t[index])

        return plugins_info

    def makeListProcess(self, data, sType, i, return_dict):
        plugins_info = []

        if (data['pid'] == sType):
            if type(data['versions']) == list and data.has_key('coexist') and data['coexist']:
                tmp_data = self.makeCoexist(data)
                for index in range(len(tmp_data)):
                    plugins_info.append(tmp_data[index])
            else:
                pg = self.getPluginInfo(data)
                plugins_info.append(pg)
            # return plugins_info

        if sType == '0':
            if type(data['versions']) == list and data.has_key('coexist') and data['coexist']:
                tmp_data = self.makeCoexist(data)
                for index in range(len(tmp_data)):
                    plugins_info.append(tmp_data[index])
            else:
                pg = self.getPluginInfo(data)
                plugins_info.append(pg)

        return_dict[i] = plugins_info
        # return plugins_info

    def getAllListProcess(self, sType='0'):
        plugins_info = []
        tmp_list = []
        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        jobs = []
        for dirinfo in os.listdir(self.__plugin_dir):
            if dirinfo[0:1] == '.':
                continue
            path = self.__plugin_dir + '/' + dirinfo
            if os.path.isdir(path):
                json_file = path + '/info.json'
                if os.path.exists(json_file):
                    data = json.loads(slemp.readFile(json_file))
                    if sType == '0':
                        tmp_list.append(data)

                    if (data['pid'] == sType):
                        tmp_list.append(data)

        ntmp_list = range(len(tmp_list))
        for i in ntmp_list:
            p = multiprocessing.Process(
                target=self.makeListProcess, args=(tmp_list[i], sType, i, return_dict))
            jobs.append(p)
            p.start()

        for proc in jobs:
            proc.join()

        returnData = return_dict.values()
        for i in ntmp_list:
            for index in range(len(returnData[i])):
                plugins_info.append(returnData[i][index])

        return plugins_info

    def getPluginList(self, sType, sPage=1, sPageSize=10):
        # print sType, sPage, sPageSize

        ret = {}
        ret['type'] = json.loads(slemp.readFile(self.__type))
        # plugins_info = self.getAllListThread(sType)
        # plugins_info = self.getAllListProcess(sType)
        data = self.getAllListPage(sType, sPage, sPageSize)
        ret['data'] = data[0]

        args = {}
        args['count'] = data[1]
        args['p'] = sPage
        args['tojs'] = 'getSList'
        args['row'] = sPageSize

        ret['list'] = slemp.getPage(args)
        return ret

    def getIndexList(self):
        if not os.path.exists(self.__index):
            slemp.writeFile(self.__index, '[]')

        indexList = json.loads(slemp.readFile(self.__index))
        plist = []
        app = []
        for i in indexList:
            info = i.split('-')
            if not info[0] in app:
                app.append(info[0])
            path = self.__plugin_dir + '/' + info[0]
            if os.path.isdir(path):
                json_file = path + '/info.json'
                if os.path.exists(json_file):
                    try:
                        data = json.loads(slemp.readFile(json_file))
                        tmp_data = self.makeList(data)
                        for index in range(len(tmp_data)):
                            if tmp_data[index]['versions'] == info[1] or info[1] in tmp_data[index]['versions']:
                                tmp_data[index]['display'] = True
                                plist.append(tmp_data[index])
                                continue
                    except Exception, e:
                        print 'getIndexList:', e

        # Cannot use multiprocessing when using gevent mode
        # plist = self.checkStatusMProcess(plist)
        plist = self.checkStatusMThreads(plist)
        return plist

    def setIndexSort(self, sort):
        data = sort.split('|')
        slemp.writeFile(self.__index, json.dumps(data))
        return True

    def addIndex(self, name, version):
        if not os.path.exists(self.__index):
            slemp.writeFile(self.__index, '[]')

        indexList = json.loads(slemp.readFile(self.__index))
        vname = name + '-' + version

        if vname in indexList:
            return slemp.returnJson(False, 'Please don\'t add more!')
        if len(indexList) >= 12:
            return slemp.returnJson(False, 'The home page can only display up to 12 software!')

        indexList.append(vname)
        slemp.writeFile(self.__index, json.dumps(indexList))
        return slemp.returnJson(True, 'Added successfully!')

    def removeIndex(self, name, version):
        if not os.path.exists(self.__index):
            slemp.writeFile(self.__index, '[]')

        indexList = json.loads(slemp.readFile(self.__index))
        vname = name + '-' + version
        if not vname in indexList:
            return slemp.returnJson(True, 'Successfully deleted!')
        indexList.remove(vname)
        slemp.writeFile(self.__index, json.dumps(indexList))
        return slemp.returnJson(True, 'Successfully deleted!')

    # shell transfer
    def run(self, name, func, version, args='', script='index'):
        path = slemp.getRunDir() + '/' + self.__plugin_dir + \
            '/' + name + '/' + script + '.py'
        py = 'python ' + path

        if args == '':
            py_cmd = py + ' ' + func + ' ' + version
        else:
            py_cmd = py + ' ' + func + ' ' + version + ' ' + args

        if not os.path.exists(path):
            return ('', '')
        data = slemp.execShell(py_cmd)
        # data = os.popen(py_cmd).read()

        if slemp.isAppleSystem():
            print 'run', py_cmd
        # print os.path.exists(py_cmd)
        return (data[0].strip(), data[1].strip())

    # Map package calls
    def callback(self, name, func, args='', script='index'):
        package = slemp.getRunDir() + '/plugins/' + name
        if not os.path.exists(package):
            return (False, "Plugin does not exist!")

        sys.path.append(package)
        eval_str = "__import__('" + script + "')." + func + '(' + args + ')'
        newRet = eval(eval_str)
        if slemp.isAppleSystem():
            print 'callback', eval_str

        return (True, newRet)
