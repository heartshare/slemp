# coding:utf-8

import sys
import io
import os
import time
import shutil
import uuid

reload(sys)
sys.setdefaultencoding('utf-8')


from datetime import timedelta

from flask import Flask
from flask import render_template
from flask import make_response
from flask import Response
from flask import session
from flask import request
from flask import redirect
from flask import url_for
from flask_caching import Cache
from flask_session import Session

sys.path.append(os.getcwd() + "/class/core")
sys.path.append("/usr/local/lib/python2.7/site-packages")

import db
import slemp
import config_api

app = Flask(__name__, template_folder='templates/default')
app.config.version = config_api.config_api().getVersion()

cache = Cache(config={'CACHE_TYPE': 'simple'})
cache.init_app(app, config={'CACHE_TYPE': 'simple'})

try:
    from flask_sqlalchemy import SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/slemp_session.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app.config['SESSION_TYPE'] = 'sqlalchemy'
    app.config['SESSION_SQLALCHEMY'] = sdb
    app.config['SESSION_SQLALCHEMY_TABLE'] = 'session'
    sdb = SQLAlchemy(app)
    sdb.create_all()
except:
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = '/tmp/py_slemp_session_' + \
        str(sys.version_info[0])
    app.config['SESSION_FILE_THRESHOLD'] = 1024
    app.config['SESSION_FILE_MODE'] = 384
    slemp.execShell("pip install flask_sqlalchemy &")

app.secret_key = uuid.UUID(int=uuid.getnode()).hex[-12:]
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'SLEMP_:'
app.config['SESSION_COOKIE_NAME'] = "SLEMP_VER_1"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)
# Session(app)

# socketio
from flask_socketio import SocketIO, emit, send
socketio = SocketIO()
socketio.init_app(app)


# debug macosx dev
if slemp.isAppleSystem():
    app.debug = True
    app.config.version = app.config.version + str(time.time())


import common
common.init()


def funConvert(fun):
    block = fun.split('_')
    func = block[0]
    for x in range(len(block) - 1):
        suf = block[x + 1].title()
        func += suf
    return func


def isLogined():
    # print('isLogined', session)
    if 'login' in session and 'username' in session and session['login'] == True:
        return True

    if os.path.exists('data/api_login.txt'):
        content = slemp.readFile('data/api_login.txt')
        session['login'] = True
        session['username'] = content
        os.remove('data/api_login.txt')
    return False


def publicObject(toObject, func, action=None, get=None):
    name = funConvert(func) + 'Api'
    try:
        if hasattr(toObject, name):
            efunc = 'toObject.' + name + '()'
            data = eval(efunc)
            return data
    except Exception as e:
        data = {'msg': 'Access exception:' + str(e) + '!', "status": False}
        return slemp.getJson(data)


@app.route("/test")
def test():
    print sys.version_info
    print session
    os = slemp.getOs()
    print os
    return slemp.getLocalIp()


@app.route('/close')
def close():
    if not os.path.exists('data/close.pl'):
        return redirect('/')
    data = {}
    data['cmd'] = 'rm -rf ' + slemp.getRunDir() + '/data/close.pl'
    return render_template('close.html', data=data)


@app.route("/code")
def code():
    import vilidate
    vie = vilidate.vieCode()
    codeImage = vie.GetCodeImage(80, 4)
    try:
        from cStringIO import StringIO
    except:
        from StringIO import StringIO

    out = StringIO()
    codeImage[0].save(out, "png")

    session['code'] = slemp.md5(''.join(codeImage[1]).lower())

    img = Response(out.getvalue(), headers={'Content-Type': 'image/png'})
    return make_response(img)


@app.route("/check_login", methods=['POST'])
def checkLogin():
    if isLogined():
        return "true"
    return "false"


@app.route("/login")
def login():
    # print session
    dologin = request.args.get('dologin', '')
    if dologin == 'True':
        session.clear()
        return redirect('/login')

    if isLogined():
        return redirect('/')
    return render_template('login.html')


@app.route("/do_login", methods=['POST'])
def doLogin():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    code = request.form.get('code', '').strip()

    if session.has_key('code'):
        if session['code'] != slemp.md5(code):
            return slemp.returnJson(False, 'The verification code is wrong, please re-enter!')

    userInfo = slemp.M('users').where(
        "id=?", (1,)).field('id,username,password').find()

    password = slemp.md5(password)
    login_cache_count = 5
    login_cache_limit = cache.get('login_cache_limit')
    filename = 'data/close.pl'
    if os.path.exists(filename):
        return slemp.returnJson(False, 'Panel is closed!')

    if userInfo['username'] != username or userInfo['password'] != password:
        msg = "<a style='color: red'>Incorrect password</a>, account: {1}, password: {2}, login IP: {3}", ((
            '****', '******', request.remote_addr))

        if login_cache_limit == None:
            login_cache_limit = 1
        else:
            login_cache_limit = int(login_cache_limit) + 1

        if login_cache_limit >= login_cache_count:
            slemp.writeFile(filename, 'True')
            return slemp.returnJson(False, 'Panel is closed!')

        cache.set('login_cache_limit', login_cache_limit, timeout=10000)
        login_cache_limit = cache.get('login_cache_limit')
        slemp.writeLog('User login', slemp.getInfo(msg))
        return slemp.returnJson(False, slemp.getInfo("Incorrect username or password, you can try [{1}] more times!", (str(login_cache_count - login_cache_limit))))

    cache.delete('login_cache_limit')
    session['login'] = True
    session['username'] = userInfo['username']
    #print('do_login', session)

    # When fix jumps, the data disappears, which may be a cross-domain problem
    slemp.writeFile('data/api_login.txt', userInfo['username'])
    return slemp.returnJson(True, 'Login successful, redirect...')


@app.route('/<reqClass>/<reqAction>', methods=['POST', 'GET'])
@app.route('/<reqClass>/', methods=['POST', 'GET'])
@app.route('/<reqClass>', methods=['POST', 'GET'])
@app.route('/', methods=['POST', 'GET'])
def index(reqClass=None, reqAction=None, reqData=None):
    comReturn = common.local()
    if comReturn:
        return comReturn

    if (reqClass == None):
        reqClass = 'index'
    classFile = ('config', 'control', 'crontab', 'files', 'firewall',
                 'index', 'plugins', 'login', 'system', 'site', 'ssl', 'task', 'soft')
    if not reqClass in classFile:
        return redirect('/')

    if reqAction == None:
        if not isLogined():
            return redirect('/login')

        # if reqClass == 'config':
        import config_api
        data = config_api.config_api().get()
        return render_template(reqClass + '.html', data=data)
        # else:
        #     return render_template(reqClass + '.html')

    className = reqClass + '_api'

    eval_str = "__import__('" + className + "')." + className + '()'
    newInstance = eval(eval_str)
    return publicObject(newInstance, reqAction)

ssh = None
shell = None
try:
    import paramiko
    ssh = paramiko.SSHClient()
except:
    slemp.execShell('pip install paramiko==2.0.2 &')


def create_rsa():
    slemp.execShell("rm -f /root/.ssh/*")
    slemp.execShell('ssh-keygen -q -t rsa -P "" -f /root/.ssh/id_rsa')
    slemp.execShell('cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys')
    slemp.execShell('chmod 600 /root/.ssh/authorized_keys')


def clear_ssh():
    sh = '''
#!/bin/bash
PLIST=`who | grep localhost | awk '{print $2}'`
for i in $PLIST
do
    ps -t /dev/$i |grep -v TTY |awk '{print $1}' | xargs kill -9
done
'''
    if not slemp.isAppleSystem():
        info = slemp.execShell(sh)
        print info[0], info[1]


def connect_ssh():
    # print 'connect_ssh ....'
    clear_ssh()
    global shell, ssh
    if not os.path.exists('/root/.ssh/authorized_keys') or not os.path.exists('/root/.ssh/id_rsa') or not os.path.exists('/root/.ssh/id_rsa.pub'):
        create_rsa()

    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect('localhost', slemp.getSSHPort())
    except Exception as e:
        if slemp.getSSHStatus():
            try:
                ssh.connect('127.0.0.1', slemp.getSSHPort())
            except:
                return False
        ssh.connect('127.0.0.1', slemp.getSSHPort())
    shell = ssh.invoke_shell(term='xterm', width=83, height=21)
    shell.setblocking(0)
    return True


# get data object
def get_input_data(data):
    pdata = common.dict_obj()
    for key in data.keys():
        pdata[key] = str(data[key])
    return pdata


@socketio.on('webssh')
def webssh(msg):
    # print 'webssh ...'
    if not isLogined():
        emit('server_response', {'data': 'Session lost, please re-login to the panel!\r\n'})
        return None
    global shell, ssh
    ssh_success = True
    if not shell:
        ssh_success = connect_ssh()
    if not shell:
        emit('server_response', {'data': 'Failed to connect to SSH service!\r\n'})
        return
    if shell.exit_status_ready():
        ssh_success = connect_ssh()
    if not ssh_success:
        emit('server_response', {'data': 'Failed to connect to SSH service!\r\n'})
        return
    shell.send(msg)
    try:
        time.sleep(0.005)
        recv = shell.recv(4096)
        emit('server_response', {'data': recv.decode("utf-8")})
    except Exception as ex:
        pass
        # print 'webssh:' + str(ex)


@socketio.on('connect_event')
def connected_msg(msg):
    if not isLogined():
        emit('server_response', {'data': 'Session lost, please re-login to the panel!\r\n'})
        return None
    global shell, ssh
    ssh_success = True
    if not shell:
        ssh_success = connect_ssh()
    if not ssh_success:
        emit('server_response', {'data': 'Failed to connect to SSH service!\r\n'})
        return
    try:
        recv = shell.recv(8192)
        # print recv.decode("utf-8")
        emit('server_response', {'data': recv.decode("utf-8")})
    except Exception as e:
        pass
        # print 'connected_msg:' + str(e)
