# coding: utf-8

import time
import random
import os
import json
import re
import sys

sys.path.append(os.getcwd() + "/class/core")
import slemp

app_debug = False
if slemp.isAppleSystem():
    app_debug = True


def getPluginName():
    return 'rsyncd'


def getInitDTpl():
    path = getPluginDir() + "/init.d/" + getPluginName() + ".tpl"
    return path


def getPluginDir():
    return slemp.getPluginDir() + '/' + getPluginName()


def getServerDir():
    return slemp.getServerDir() + '/' + getPluginName()


def getInitDFile():
    if app_debug:
        return '/tmp/' + getPluginName()
    return '/etc/init.d/' + getPluginName()


def getArgs():
    args = sys.argv[2:]
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


def contentReplace(content):
    service_path = slemp.getServerDir()
    content = content.replace('{$SERVER_PATH}', service_path)
    return content


def status():
    data = slemp.execShell(
        "ps -ef|grep rsync |grep -v grep | grep -v python | awk '{print $2}'")
    if data[0] == '':
        return 'stop'
    return 'start'


def appConf():
    if slemp.isAppleSystem():
        return getServerDir() + '/rsyncd.conf'
    return '/etc/rsyncd.conf'


def appConfPwd():
    if slemp.isAppleSystem():
        return getServerDir() + '/rsyncd.passwd'
    return '/etc/rsyncd.passwd'


def getLog():
    conf_path = appConf()
    conf = slemp.readFile(conf_path)
    rep = 'log file\s*=\s*(.*)'
    tmp = re.search(rep, conf)
    if not tmp:
        return ''
    return tmp.groups()[0]


def initDreplace():
    conf_path = appConf()
    conf = slemp.readFile(conf_path)

    compile_sub = re.compile('^#(.*)', re.M)
    conf = compile_sub.sub('', conf)
    conf_tpl_path = getPluginDir() + '/conf/rsyncd.conf'
    if conf.strip() == '':
        content = slemp.readFile(conf_tpl_path)
        slemp.writeFile(conf_path, content)
    confpwd_path = appConfPwd()
    if not os.path.exists(confpwd_path):
        slemp.writeFile(confpwd_path, '')
        slemp.execShell('chmod 0600 ' + confpwd_path)

    initD_path = getServerDir() + '/init.d'
    if not os.path.exists(initD_path):
        os.mkdir(initD_path)
    file_bin = initD_path + '/' + getPluginName()

    file_tpl = getInitDTpl()
    # initd replace
    if not os.path.exists(file_bin):
        content = slemp.readFile(file_tpl)
        content = contentReplace(content)
        slemp.writeFile(file_bin, content)
        slemp.execShell('chmod +x ' + file_bin)

    if os.path.exists('/usr/lib/systemd/system/rsyncd.service'):
        slemp.execShell('rm -rf /usr/lib/systemd/system/rsyncd*')

    rlog = getLog()
    if os.path.exists(rlog):
        slemp.writeFile(rlog, '')
    return file_bin


def start():
    file = initDreplace()
    data = slemp.execShell(file + ' start')
    if data[1] == '':
        return 'ok'
    return 'fail'


def stop():
    file = initDreplace()
    data = slemp.execShell(file + ' stop')
    if data[1] == '':
        return 'ok'
    return 'fail'


def restart():
    if slemp.isAppleSystem():
        return "Apple Computer does not support"
    stop()
    start()
    return 'ok'


def reload():
    if slemp.isAppleSystem():
        return "Apple Computer does not support"

    # data = slemp.execShell('systemctl reload rsyncd.service')
    # if data[1] == '':
    #     return 'ok'
    # return 'fail'
    stop()
    start()
    return 'ok'


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

    p_bin = initDreplace()
    initd_bin = getInitDFile()
    shutil.copyfile(p_bin, initd_bin)
    slemp.execShell('chmod +x ' + initd_bin)
    slemp.execShell('chkconfig --add ' + getPluginName())
    return 'ok'


def initdUinstall():
    if not app_debug:
        if slemp.isAppleSystem():
            return "Apple Computer does not support"
    initd_bin = getInitDFile()
    os.remove(initd_bin)
    slemp.execShell('chkconfig --del ' + getPluginName())
    return 'ok'


def getRecListData():
    path = appConf()
    content = slemp.readFile(path)

    flist = re.findall("\[(.*)\]", content)
    flist_len = len(flist)
    ret_list = []
    for i in range(flist_len):
        tmp = {}
        tmp['name'] = flist[i]
        n = i + 1
        reg = ''
        if n == flist_len:
            reg = '\[' + flist[i] + '\](.*)\[?'
        else:
            reg = '\[' + flist[i] + '\](.*)\[' + flist[n] + '\]'

        t1 = re.search(reg, content, re.S)
        if t1:
            args = t1.groups()[0]
            # print 'args start', args, 'args_end'
            t2 = re.findall('\s*(.*)\s*=\s*(.*)', args, re.M)
            for i in range(len(t2)):
                tmp[t2[i][0].strip()] = t2[i][1]
        ret_list.append(tmp)
    return ret_list


def getRecList():
    ret_list = getRecListData()
    return slemp.returnJson(True, 'ok', ret_list)


def getUPwdList():
    pwd_path = appConfPwd()
    pwd_content = slemp.readFile(pwd_path)
    plist = pwd_content.strip().split('\n')
    plist_len = len(plist)
    data = {}
    for x in range(plist_len):
        tmp = plist[x].split(':')
        data[tmp[0]] = tmp[1]
    return data


def addRec():
    args = getArgs()
    data = checkArgs(args, ['name', 'path', 'pwd', 'ps'])
    if not data[0]:
        return data[1]

    args_name = args['name']
    args_pwd = args['pwd']
    args_path = args['path']
    args_ps = args['ps']

    pwd_path = appConfPwd()
    pwd_content = slemp.readFile(pwd_path)
    pwd_content += args_name + ':' + args_pwd + "\n"
    slemp.writeFile(pwd_path, pwd_content)

    path = appConf()
    content = slemp.readFile(path)

    con = "\n\n" + '[' + args_name + ']' + "\n"
    con += 'path = ' + args_path + "\n"
    con += 'comment = ' + args_ps + "\n"
    con += 'auth users = ' + args_name + "\n"
    con += 'read only = false'

    content = content + con
    slemp.writeFile(path, content)
    return slemp.returnJson(True, 'Added successfully')


def delRec():
    args = getArgs()
    data = checkArgs(args, ['name'])
    if not data[0]:
        return data[1]
    args_name = args['name']

    cmd = "sed -i '_bak' '/" + args_name + "/d' " + appConfPwd()
    slemp.execShell(cmd)

    try:

        path = appConf()
        content = slemp.readFile(path)

        ret_list = getRecListData()
        ret_list_len = len(ret_list)
        is_end = False
        next_name = ''
        for x in range(ret_list_len):
            tmp = ret_list[x]
            if tmp['name'] == args_name:
                if x + 1 == ret_list_len:
                    is_end = True
                else:
                    next_name = ret_list[x + 1]['name']
        reg = ''
        if is_end:
            reg = '\[' + args_name + '\]\s*(.*)'
        else:
            reg = '\[' + args_name + '\]\s*(.*)\s*\[' + next_name + '\]'

        conre = re.search(reg,  content, re.S)
        content = content.replace(
            "[" + args_name + "]\n" + conre.groups()[0], '')
        slemp.writeFile(path, content)
        return slemp.returnJson(True, 'Successfully deleted!')
    except Exception as e:
        return slemp.returnJson(False, 'Failed to delete!')


def cmdRec():
    args = getArgs()
    data = checkArgs(args, ['name'])
    if not data[0]:
        return data[1]

    an = args['name']
    pwd_list = getUPwdList()
    ip = slemp.getLocalIp()

    cmd = 'echo "' + pwd_list[an] + '" > /tmp/p.pass' + "<br>"
    cmd += 'chmod 600 /tmp/p.pass' + "<br>"
    cmd += 'rsync -arv --password-file=/tmp/p.pass --progress --delete  /project  ' + \
        an + '@' + ip + '::' + an
    return slemp.returnJson(True, 'OK!', cmd)

# rsyncdReceive
if __name__ == "__main__":
    func = sys.argv[1]
    if func == 'status':
        print status()
    elif func == 'start':
        print start()
    elif func == 'stop':
        print stop()
    elif func == 'restart':
        print restart()
    elif func == 'reload':
        print reload()
    elif func == 'initd_status':
        print initdStatus()
    elif func == 'initd_install':
        print initdInstall()
    elif func == 'initd_uninstall':
        print initdUinstall()
    elif func == 'conf':
        print appConf()
    elif func == 'conf_pwd':
        print appConfPwd()
    elif func == 'run_log':
        print getLog()
    elif func == 'rec_list':
        print getRecList()
    elif func == 'add_rec':
        print addRec()
    elif func == 'del_rec':
        print delRec()
    elif func == 'cmd_rec':
        print cmdRec()
    else:
        print 'error'
