# coding:utf-8

import sys
import io
import os
import time
import re
import json
import shutil

reload(sys)
sys.setdefaultencoding('utf8')

sys.path.append(os.getcwd() + "/class/core")
sys.path.append("/usr/local/lib/python2.7/site-packages")

import slemp

app_debug = False
if slemp.isAppleSystem():
    app_debug = True


def getPluginName():
    return 'php'


def getPluginDir():
    return slemp.getPluginDir() + '/' + getPluginName()


def getServerDir():
    return slemp.getServerDir() + '/' + getPluginName()


def getInitDFile(version):
    if app_debug:
        return '/tmp/' + getPluginName()
    return '/etc/init.d/' + getPluginName() + version


def getArgs():
    args = sys.argv[3:]
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
            return (False, slemp.returnJson(False, '参数:(' + ck[i] + ')没有!'))
    return (True, slemp.returnJson(True, 'ok'))


def getConf(version):
    path = getServerDir() + '/' + version + '/etc/php.ini'
    return path


def status(version):
    cmd = "ps -ef|grep 'php/" + version + \
        "' |grep -v grep | grep -v python | awk '{print $2}'"
    data = slemp.execShell(cmd)
    if data[0] == '':
        return 'stop'
    return 'start'


def contentReplace(content, version):
    service_path = slemp.getServerDir()
    content = content.replace('{$ROOT_PATH}', slemp.getRootDir())
    content = content.replace('{$SERVER_PATH}', service_path)
    content = content.replace('{$PHP_VERSION}', version)
    content = content.replace('{$LOCAL_IP}', slemp.getLocalIp())

    if slemp.isAppleSystem():
        # user = slemp.execShell(
        #     "who | sed -n '2, 1p' |awk '{print $1}'")[0].strip()
        content = content.replace('{$PHP_USER}', 'nobody')
        content = content.replace('{$PHP_GROUP}', 'nobody')

        rep = 'listen.owner\s*=\s*(.+)\r?\n'
        val = ';listen.owner = nobody\n'
        content = re.sub(rep, val, content)

        rep = 'listen.group\s*=\s*(.+)\r?\n'
        val = ';listen.group = nobody\n'
        content = re.sub(rep, val, content)

        rep = 'user\s*=\s*(.+)\r?\n'
        val = ';user = nobody\n'
        content = re.sub(rep, val, content)

        rep = r'[^\.]group\s*=\s*(.+)\r?\n'
        val = ';group = nobody\n'
        content = re.sub(rep, val, content)

    else:
        content = content.replace('{$PHP_USER}', 'www')
        content = content.replace('{$PHP_GROUP}', 'www')
    return content


def makeOpenrestyConf():
    phpversions = ['00', '52', '53', '54', '55', '56',
                   '70', '71', '72', '73', '74', '80']
    if slemp.isInstalledWeb():
        sdir = slemp.getServerDir()
        d_pathinfo = sdir + '/openresty/nginx/conf/pathinfo.conf'
        if not os.path.exists(d_pathinfo):
            s_pathinfo = getPluginDir() + '/conf/pathinfo.conf'
            shutil.copyfile(s_pathinfo, d_pathinfo)

        info = getPluginDir() + '/info.json'
        content = slemp.readFile(info)
        content = json.loads(content)
        versions = content['versions']
        tpl = getPluginDir() + '/conf/enable-php.conf'
        tpl_content = slemp.readFile(tpl)
        for x in phpversions:
            dfile = sdir + '/openresty/nginx/conf/enable-php-' + x + '.conf'
            if not os.path.exists(dfile):
                if x == '00':
                    slemp.writeFile(dfile, '')
                else:
                    w_content = contentReplace(tpl_content, x)
                    slemp.writeFile(dfile, w_content)

        # php-fpm status
        for version in phpversions:
            dfile = sdir + '/openresty/nginx/conf/php_status/phpfpm_status_' + version + '.conf'
            tpl = getPluginDir() + '/conf/phpfpm_status.conf'
            if not os.path.exists(dfile):
                content = slemp.readFile(tpl)
                content = contentReplace(content, version)
                slemp.writeFile(dfile, content)
        slemp.restartWeb()


def phpPrependFile(version):
    app_start = getServerDir() + '/app_start.php'
    if not os.path.exists(app_start):
        tpl = getPluginDir() + '/conf/app_start.php'
        content = slemp.readFile(tpl)
        content = contentReplace(content, version)
        slemp.writeFile(app_start, content)


def phpFpmReplace(version):
    desc_php_fpm = getServerDir() + '/' + version + '/etc/php-fpm.conf'
    if not os.path.exists(desc_php_fpm):
        tpl_php_fpm = getPluginDir() + '/conf/php-fpm.conf'
        content = slemp.readFile(tpl_php_fpm)
        content = contentReplace(content, version)
        slemp.writeFile(desc_php_fpm, content)
    else:
        if version == '52':
            tpl_php_fpm = tpl_php_fpm = getPluginDir() + '/conf/php-fpm-52.conf'
            content = slemp.readFile(tpl_php_fpm)
            slemp.writeFile(desc_php_fpm, content)


def phpFpmWwwReplace(version):
    service_php_fpm_dir = getServerDir() + '/' + version + '/etc/php-fpm.d/'

    if not os.path.exists(service_php_fpm_dir):
        os.mkdir(service_php_fpm_dir)

    service_php_fpslempww = service_php_fpm_dir + '/www.conf'
    if not os.path.exists(service_php_fpslempww):
        tpl_php_fpslempww = getPluginDir() + '/conf/www.conf'
        content = slemp.readFile(tpl_php_fpslempww)
        content = contentReplace(content, version)
        slemp.writeFile(service_php_fpslempww, content)


def makePhpIni(version):
    d_ini = slemp.getServerDir() + '/php/' + version + '/etc/php.ini'
    if not os.path.exists(d_ini):
        s_ini = getPluginDir() + '/conf/php' + version[0:1] + '.ini'
        # shutil.copyfile(s_ini, d_ini)
        content = slemp.readFile(s_ini)
        if version == '52':
            content = content + "auto_prepend_file=/home/slemp/server/php/app_start.php"
        slemp.writeFile(d_ini, content)


def initReplace(version):
    makeOpenrestyConf()
    makePhpIni(version)

    initD_path = getServerDir() + '/init.d'
    if not os.path.exists(initD_path):
        os.mkdir(initD_path)

    file_bin = initD_path + '/php' + version
    if not os.path.exists(file_bin):
        file_tpl = getPluginDir() + '/init.d/php.tpl'

        if version == '52':
            file_tpl = getPluginDir() + '/init.d/php52.tpl'

        content = slemp.readFile(file_tpl)
        content = contentReplace(content, version)

        slemp.writeFile(file_bin, content)
        slemp.execShell('chmod +x ' + file_bin)

    phpPrependFile(version)
    phpFpmWwwReplace(version)
    phpFpmReplace(version)

    session_path = '/tmp/session'
    if not os.path.exists(session_path):
        os.mkdir(session_path)
        if not slemp.isAppleSystem():
            slemp.execShell('chown -R www:www ' + session_path)

    upload_path = '/tmp/upload'
    if not os.path.exists(upload_path):
        os.mkdir(upload_path)
        if not slemp.isAppleSystem():
            slemp.execShell('chown -R www:www ' + upload_path)
    return file_bin


def phpOp(version, method):
    file = initReplace(version)
    data = slemp.execShell(file + ' ' + method)
    if data[1] == '':
        return 'ok'
    return data[1]


def start(version):
    return phpOp(version, 'start')


def stop(version):
    return phpOp(version, 'stop')


def restart(version):
    return phpOp(version, 'restart')


def reload(version):
    return phpOp(version, 'reload')


def initdStatus(version):
    if not app_debug:
        if slemp.isAppleSystem():
            return "Apple Computer does not support"
    initd_bin = getInitDFile(version)
    if os.path.exists(initd_bin):
        return 'ok'
    return 'fail'


def initdInstall(version):
    import shutil
    if not app_debug:
        if slemp.isAppleSystem():
            return "Apple Computer does not support"

    source_bin = initReplace(version)
    initd_bin = getInitDFile(version)
    shutil.copyfile(source_bin, initd_bin)
    slemp.execShell('chmod +x ' + initd_bin)
    slemp.execShell('chkconfig --add ' + getPluginName() + version)
    return 'ok'


def initdUinstall(version):
    if not app_debug:
        if slemp.isAppleSystem():
            return "Apple Computer does not support"

    slemp.execShell('chkconfig --del ' + getPluginName())
    initd_bin = getInitDFile(version)
    os.remove(initd_bin)
    return 'ok'


def fpmLog(version):
    return getServerDir() + '/' + version + '/var/log/php-fpm.log'


def fpmSlowLog(version):
    return getServerDir() + '/' + version + '/var/log/www-slow.log'


def getPhpConf(version):
    gets = [
        {'name': 'short_open_tag', 'type': 1, 'ps': 'Short tag support'},
        {'name': 'asp_tags', 'type': 1, 'ps': 'ASP tag support'},
        {'name': 'max_execution_time', 'type': 2, 'ps': 'Maximum script run time'},
        {'name': 'max_input_time', 'type': 2, 'ps': 'Maximum input time'},
        {'name': 'memory_limit', 'type': 2, 'ps': 'Script memory limit'},
        {'name': 'post_max_size', 'type': 2, 'ps': 'POST data maximum size'},
        {'name': 'file_uploads', 'type': 1, 'ps': 'Whether to allow uploading of files'},
        {'name': 'upload_max_filesize', 'type': 2, 'ps': 'Maximum size allowed to upload files'},
        {'name': 'max_file_uploads', 'type': 2, 'ps': 'Maximum number of files allowed to be uploaded at the same time'},
        {'name': 'default_socket_timeout', 'type': 2, 'ps': 'Socket timeout'},
        {'name': 'error_reporting', 'type': 3, 'ps': 'Error level'},
        {'name': 'display_errors', 'type': 1, 'ps': 'Whether to output detailed error information'},
        {'name': 'cgi.fix_pathinfo', 'type': 0, 'ps': 'Whether to enable pathinfo'},
        {'name': 'date.timezone', 'type': 3, 'ps': 'Time zone'}
    ]
    phpini = slemp.readFile(getServerDir() + '/' + version + '/etc/php.ini')
    result = []
    for g in gets:
        rep = g['name'] + '\s*=\s*([0-9A-Za-z_& ~]+)(\s*;?|\r?\n)'
        tmp = re.search(rep, phpini)
        if not tmp:
            continue
        g['value'] = tmp.groups()[0]
        result.append(g)
    return slemp.getJson(result)


def submitPhpConf(version):
    gets = ['display_errors', 'cgi.fix_pathinfo', 'date.timezone', 'short_open_tag',
            'asp_tags', 'max_execution_time', 'max_input_time', 'memory_limit',
            'post_max_size', 'file_uploads', 'upload_max_filesize', 'max_file_uploads',
            'default_socket_timeout', 'error_reporting']
    args = getArgs()
    filename = getServerDir() + '/' + version + '/etc/php.ini'
    phpini = slemp.readFile(filename)
    for g in gets:
        if g in args:
            rep = g + '\s*=\s*(.+)\r?\n'
            val = g + ' = ' + args[g] + '\n'
            phpini = re.sub(rep, val, phpini)
    slemp.writeFile(filename, phpini)
    slemp.execShell(getServerDir() + '/init.d/php' + version + ' reload')
    return slemp.returnJson(True, 'Set successfully')


def getLimitConf(version):
    fileini = getServerDir() + "/" + version + "/etc/php.ini"
    phpini = slemp.readFile(fileini)
    filefpm = getServerDir() + "/" + version + "/etc/php-fpm.conf"
    phpfpm = slemp.readFile(filefpm)

    # print fileini, filefpm
    data = {}
    try:
        rep = "upload_max_filesize\s*=\s*([0-9]+)M"
        tmp = re.search(rep, phpini).groups()
        data['max'] = tmp[0]
    except:
        data['max'] = '50'

    try:
        rep = "request_terminate_timeout\s*=\s*([0-9]+)\n"
        tmp = re.search(rep, phpfpm).groups()
        data['maxTime'] = tmp[0]
    except:
        data['maxTime'] = 0

    try:
        rep = r"\n;*\s*cgi\.fix_pathinfo\s*=\s*([0-9]+)\s*\n"
        tmp = re.search(rep, phpini).groups()

        if tmp[0] == '1':
            data['pathinfo'] = True
        else:
            data['pathinfo'] = False
    except:
        data['pathinfo'] = False

    return slemp.getJson(data)


def setMaxTime(version):
    args = getArgs()
    data = checkArgs(args, ['time'])
    if not data[0]:
        return data[1]

    time = args['time']
    if int(time) < 30 or int(time) > 86400:
        return slemp.returnJson(False, 'Please fill in the value between 30-86400!')

    filefpm = getServerDir() + "/" + version + "/etc/php-fpm.conf"
    conf = slemp.readFile(filefpm)
    rep = "request_terminate_timeout\s*=\s*([0-9]+)\n"
    conf = re.sub(rep, "request_terminate_timeout = " + time + "\n", conf)
    slemp.writeFile(filefpm, conf)

    fileini = getServerDir() + "/" + version + "/etc/php.ini"
    phpini = slemp.readFile(fileini)
    rep = "max_execution_time\s*=\s*([0-9]+)\r?\n"
    phpini = re.sub(rep, "max_execution_time = " + time + "\n", phpini)
    rep = "max_input_time\s*=\s*([0-9]+)\r?\n"
    phpini = re.sub(rep, "max_input_time = " + time + "\n", phpini)
    slemp.writeFile(fileini, phpini)
    return slemp.returnJson(True, 'Set successfully!')


def setMaxSize(version):
    args = getArgs()
    if not 'max' in args:
        return 'missing time args!'
    max = args['max']
    if int(max) < 2:
        return slemp.returnJson(False, 'Upload size limit cannot be less than 2MB!')

    path = getServerDir() + '/' + version + '/etc/php.ini'
    conf = slemp.readFile(path)
    rep = u"\nupload_max_filesize\s*=\s*[0-9]+M"
    conf = re.sub(rep, u'\nupload_max_filesize = ' + max + 'M', conf)
    rep = u"\npost_max_size\s*=\s*[0-9]+M"
    conf = re.sub(rep, u'\npost_max_size = ' + max + 'M', conf)
    slemp.writeFile(path, conf)

    msg = slemp.getInfo('Set PHP-{1} maximum upload size to [{2}MB]!', (version, max,))
    slemp.writeLog('Plugin Management [PHP]', msg)
    return slemp.returnJson(True, 'Set successfully!')


def getFpmConfig(version):

    filefpm = getServerDir() + '/' + version + '/etc/php-fpm.d/www.conf'
    conf = slemp.readFile(filefpm)
    data = {}
    rep = "\s*pm.max_children\s*=\s*([0-9]+)\s*"
    tmp = re.search(rep, conf).groups()
    data['max_children'] = tmp[0]

    rep = "\s*pm.start_servers\s*=\s*([0-9]+)\s*"
    tmp = re.search(rep, conf).groups()
    data['start_servers'] = tmp[0]

    rep = "\s*pm.min_spare_servers\s*=\s*([0-9]+)\s*"
    tmp = re.search(rep, conf).groups()
    data['min_spare_servers'] = tmp[0]

    rep = "\s*pm.max_spare_servers \s*=\s*([0-9]+)\s*"
    tmp = re.search(rep, conf).groups()
    data['max_spare_servers'] = tmp[0]

    rep = "\s*pm\s*=\s*(\w+)\s*"
    tmp = re.search(rep, conf).groups()
    data['pm'] = tmp[0]
    return slemp.getJson(data)


def setFpmConfig(version):
    args = getArgs()
    # if not 'max' in args:
    #     return 'missing time args!'

    version = args['version']
    max_children = args['max_children']
    start_servers = args['start_servers']
    min_spare_servers = args['min_spare_servers']
    max_spare_servers = args['max_spare_servers']
    pm = args['pm']

    file = getServerDir() + '/' + version + '/etc/php-fpm.d/www.conf'
    conf = slemp.readFile(file)

    rep = "\s*pm.max_children\s*=\s*([0-9]+)\s*"
    conf = re.sub(rep, "\npm.max_children = " + max_children, conf)

    rep = "\s*pm.start_servers\s*=\s*([0-9]+)\s*"
    conf = re.sub(rep, "\npm.start_servers = " + start_servers, conf)

    rep = "\s*pm.min_spare_servers\s*=\s*([0-9]+)\s*"
    conf = re.sub(rep, "\npm.min_spare_servers = " +
                  min_spare_servers, conf)

    rep = "\s*pm.max_spare_servers \s*=\s*([0-9]+)\s*"
    conf = re.sub(rep, "\npm.max_spare_servers = " +
                  max_spare_servers + "\n", conf)

    rep = "\s*pm\s*=\s*(\w+)\s*"
    conf = re.sub(rep, "\npm = " + pm + "\n", conf)

    slemp.writeFile(file, conf)
    reload(version)

    msg = slemp.getInfo('Set PHP-{1} concurrency settings,max_children={2},start_servers={3},min_spare_servers={4},max_spare_servers={5}', (version, max_children,
                                                                                                                      start_servers, min_spare_servers, max_spare_servers,))
    slemp.writeLog('Plugin management [PHP]', msg)
    return slemp.returnJson(True, 'Set successfully!')


def checkFpmStatusFile(version):
    if slemp.isInstalledWeb():
        sdir = slemp.getServerDir()
        dfile = sdir + '/openresty/nginx/conf/php_status/phpfpm_status_' + version + '.conf'
        if not os.path.exists(dfile):
            tpl = getPluginDir() + '/conf/phpfpm_status.conf'
            content = slemp.readFile(tpl)
            content = contentReplace(content, version)
            slemp.writeFile(dfile, content)
            slemp.restartWeb()


def getFpmStatus(version):
    checkFpmStatusFile(version)
    result = slemp.httpGet(
        'http://127.0.0.1/phpfpm_status_' + version + '?json')
    tmp = json.loads(result)
    fTime = time.localtime(int(tmp['start time']))
    tmp['start time'] = time.strftime('%Y-%m-%d %H:%M:%S', fTime)
    return slemp.getJson(tmp)


def getDisableFunc(version):
    filename = slemp.getServerDir() + '/php/' + version + '/etc/php.ini'
    if not os.path.exists(filename):
        return slemp.returnJson(False, 'The specified PHP version does not exist!')

    phpini = slemp.readFile(filename)
    data = {}
    rep = "disable_functions\s*=\s{0,1}(.*)\n"
    tmp = re.search(rep, phpini).groups()
    data['disable_functions'] = tmp[0]
    return slemp.getJson(data)


def setDisableFunc(version):
    filename = slemp.getServerDir() + '/php/' + version + '/etc/php.ini'
    if not os.path.exists(filename):
        return slemp.returnJson(False, 'The specified PHP version does not exist!')

    args = getArgs()
    disable_functions = args['disable_functions']

    phpini = slemp.readFile(filename)
    rep = "disable_functions\s*=\s*.*\n"
    phpini = re.sub(rep, 'disable_functions = ' +
                    disable_functions + "\n", phpini)

    msg = slemp.getInfo('Modify the disabled function of PHP-{1} to [{2}]', (version, disable_functions,))
    slemp.writeLog('Plugin management [PHP]', msg)
    slemp.writeFile(filename, phpini)
    reload(version)
    return slemp.returnJson(True, 'Set successfully!')


def checkPhpinfoFile(v):
    if slemp.isInstalledWeb():
        sdir = slemp.getServerDir()
        dfile = sdir + '/openresty/nginx/conf/php_status/phpinfo_' + v + '.conf'
        if not os.path.exists(dfile):
            tpl = getPluginDir() + '/conf/phpinfo.conf'
            content = slemp.readFile(tpl)
            content = contentReplace(content, v)
            slemp.writeFile(dfile, content)
            slemp.restartWeb()


def getPhpinfo(v):
    checkPhpinfoFile(v)
    sPath = slemp.getRootDir() + '/phpinfo/' + v
    slemp.execShell("rm -rf " + slemp.getRootDir() + '/phpinfo')
    slemp.execShell("mkdir -p " + sPath)
    slemp.writeFile(sPath + '/phpinfo.php', '<?php phpinfo(); ?>')
    url = 'http://127.0.0.1/' + v + '/phpinfo.php'
    phpinfo = slemp.httpGet(url)
    os.system("rm -rf " + slemp.getRootDir() + '/phpinfo')
    return phpinfo


def get_php_info(args):
    return getPhpinfo(args['version'])


def getLibConf(version):
    fname = slemp.getServerDir() + '/php/' + version + '/etc/php.ini'
    if not os.path.exists(fname):
        return slemp.returnJson(False, 'The specified PHP version does not exist!')

    phpini = slemp.readFile(fname)

    libpath = getPluginDir() + '/versions/phplib.conf'
    phplib = json.loads(slemp.readFile(libpath))

    libs = []
    tasks = slemp.M('tasks').where(
        "status!=?", ('1',)).field('status,name').select()
    for lib in phplib:
        lib['task'] = '1'
        for task in tasks:
            tmp = slemp.getStrBetween('[', ']', task['name'])
            if not tmp:
                continue
            tmp1 = tmp.split('-')
            if tmp1[0].lower() == lib['name'].lower():
                lib['task'] = task['status']
                lib['phpversions'] = []
                lib['phpversions'].append(tmp1[1])
        if phpini.find(lib['check']) == -1:
            lib['status'] = False
        else:
            lib['status'] = True
        libs.append(lib)
    return slemp.returnJson(True, 'OK!', libs)


def installLib(version):
    args = getArgs()
    data = checkArgs(args, ['name'])
    if not data[0]:
        return data[1]

    name = args['name']
    execstr = "cd " + getPluginDir() + '/versions/' + version + " && /bin/bash " + \
        name + '.sh' + ' install ' + version

    rettime = time.strftime('%Y-%m-%d %H:%M:%S')
    insert_info = (None, 'Install [' + name + '-' + version + ']',
                   'execshell', '0', rettime, execstr)
    slemp.M('tasks').add('id,name,type,status,addtime,execstr', insert_info)
    return slemp.returnJson(True, 'Added download task to queue!')


def uninstallLib(version):
    args = getArgs()
    data = checkArgs(args, ['name'])
    if not data[0]:
        return data[1]

    name = args['name']
    execstr = "cd " + getPluginDir() + '/versions/' + version + " && /bin/bash " + \
        name + '.sh' + ' uninstall ' + version

    data = slemp.execShell(execstr)
    if data[0] == '' and data[1] == '':
        return slemp.returnJson(True, 'Uninstalled successfully!')
    else:
        return slemp.returnJson(False, 'Uninstall info! [Channel 0]:' + data[0] + "[Channel 0]:" + data[1])


def getConfAppStart():
    pstart = slemp.getServerDir() + '/php/app_start.php'
    return pstart

if __name__ == "__main__":

    if len(sys.argv) < 3:
        print 'missing parameters'
        exit(0)

    func = sys.argv[1]
    version = sys.argv[2]

    if func == 'status':
        print status(version)
    elif func == 'start':
        print start(version)
    elif func == 'stop':
        print stop(version)
    elif func == 'restart':
        print restart(version)
    elif func == 'reload':
        print reload(version)
    elif func == 'initd_status':
        print initdStatus(version)
    elif func == 'initd_install':
        print initdInstall(version)
    elif func == 'initd_uninstall':
        print initdUinstall(version)
    elif func == 'fpm_log':
        print fpmLog(version)
    elif func == 'fpm_slow_log':
        print fpmSlowLog(version)
    elif func == 'conf':
        print getConf(version)
    elif func == 'app_start':
        print getConfAppStart()
    elif func == 'get_php_conf':
        print getPhpConf(version)
    elif func == 'submit_php_conf':
        print submitPhpConf(version)
    elif func == 'get_limit_conf':
        print getLimitConf(version)
    elif func == 'set_max_time':
        print setMaxTime(version)
    elif func == 'set_max_size':
        print setMaxSize(version)
    elif func == 'get_fpm_conf':
        print getFpmConfig(version)
    elif func == 'set_fpm_conf':
        print setFpmConfig(version)
    elif func == 'get_fpm_status':
        print getFpmStatus(version)
    elif func == 'get_disable_func':
        print getDisableFunc(version)
    elif func == 'set_disable_func':
        print setDisableFunc(version)
    elif func == 'get_phpinfo':
        print getPhpinfo(version)
    elif func == 'get_lib_conf':
        print getLibConf(version)
    elif func == 'install_lib':
        print installLib(version)
    elif func == 'uninstall_lib':
        print uninstallLib(version)
    else:
        print "fail"
