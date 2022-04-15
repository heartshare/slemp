# coding: utf-8

import time
import os
import sys
import slemp
import re
import json
import pwd
import shutil
sys.path.append("/usr/local/lib/python2.7/site-packages")
sys.path.append("/usr/lib64/python2.7/site-packages")

import psutil

from flask import request


class site_api:
    siteName = None  # website name
    sitePath = None  # Root directory
    sitePort = None  # port
    phpVersion = None  # PHP version

    setupPath = None  # installation path
    vhostPath = None
    logsPath = None
    passPath = None
    rewritePath = None
    sslDir = None  # ssl directory

    def __init__(self):
        # nginx conf
        self.setupPath = slemp.getServerDir() + '/web_conf'
        self.vhostPath = vh = self.setupPath + '/nginx/vhost'
        if not os.path.exists(vh):
            slemp.execShell("mkdir -p " + vh + " && chmod -R 755 " + vh)
        self.rewritePath = rw = self.setupPath + '/nginx/rewrite'
        if not os.path.exists(rw):
            slemp.execShell("mkdir -p " + rw + " && chmod -R 755 " + rw)
        self.passPath = self.setupPath + '/nginx/pass'
        # if not os.path.exists(pp):
        #     slemp.execShell("mkdir -p " + rw + " && chmod -R 755 " + rw)

        self.logsPath = slemp.getRootDir() + '/wwwlogs'
        # ssl conf
        if slemp.isAppleSystem():
            self.sslDir = self.setupPath + '/letsencrypt/'
        else:
            self.sslDir = '/etc/letsencrypt/live/'

    ##### ----- start ----- ###
    def listApi(self):
        limit = request.form.get('limit', '').encode('utf-8')
        p = request.form.get('p', '').encode('utf-8')
        type_id = request.form.get('type_id', '').encode('utf-8')

        start = (int(p) - 1) * (int(limit))

        siteM = slemp.M('sites')
        if type_id != '' and type_id == '-1' and type_id == '0':
            siteM.where('type_id=?', (type_id))

        _list = siteM.field('id,name,path,status,ps,addtime,edate').limit(
            (str(start)) + ',' + limit).order('id desc').select()

        for i in range(len(_list)):
            _list[i]['backup_count'] = slemp.M('backup').where(
                "pid=? AND type=?", (_list[i]['id'], 0)).count()

        _ret = {}
        _ret['data'] = _list

        count = siteM.count()
        _page = {}
        _page['count'] = count
        _page['tojs'] = 'getWeb'
        _page['p'] = p
        _page['row'] = limit

        _ret['page'] = slemp.getPage(_page)
        return slemp.getJson(_ret)

    def setDefaultSiteApi(self):
        name = request.form.get('name', '').encode('utf-8')
        import time
        # clean up the old
        defaultSite = slemp.readFile('data/defaultSite.pl')
        if defaultSite:
            path = self.getHostConf(defaultSite)
            if os.path.exists(path):
                conf = slemp.readFile(path)
                rep = "listen\s+80.+;"
                conf = re.sub(rep, 'listen 80;', conf, 1)
                rep = "listen\s+443.+;"
                conf = re.sub(rep, 'listen 443 ssl;', conf, 1)
                slemp.writeFile(path, conf)

        path = self.getHostConf(name)
        if os.path.exists(path):
            conf = slemp.readFile(path)
            rep = "listen\s+80\s*;"
            conf = re.sub(rep, 'listen 80 default_server;', conf, 1)
            rep = "listen\s+443\s*ssl\s*\w*\s*;"
            conf = re.sub(rep, 'listen 443 ssl default_server;', conf, 1)
            slemp.writeFile(path, conf)

        slemp.writeFile('data/defaultSite.pl', name)
        slemp.restartWeb()
        return slemp.returnJson(True, '设置成功!')

    def getDefaultSiteApi(self):
        data = {}
        data['sites'] = slemp.M('sites').field(
            'name').order('id desc').select()
        data['defaultSite'] = slemp.readFile('data/defaultSite.pl')
        return slemp.getJson(data)

    def setPsApi(self):
        mid = request.form.get('id', '').encode('utf-8')
        ps = request.form.get('ps', '').encode('utf-8')
        if slemp.M('sites').where("id=?", (mid,)).setField('ps', ps):
            return slemp.returnJson(True, 'Successfully modified!')
        return slemp.returnJson(False, 'Fail to edit!')

    def stopApi(self):
        mid = request.form.get('id', '').encode('utf-8')
        name = request.form.get('name', '').encode('utf-8')
        path = self.setupPath + '/stop'

        if not os.path.exists(path):
            os.makedirs(path)
            slemp.writeFile(path + '/index.html',
                         'The website has been closed!!!')

        binding = slemp.M('binding').where('pid=?', (mid,)).field(
            'id,pid,domain,path,port,addtime').select()
        for b in binding:
            bpath = path + '/' + b['path']
            if not os.path.exists(bpath):
                slemp.execShell('mkdir -p ' + bpath)
                slemp.execShell('ln -sf ' + path +
                             '/index.html ' + bpath + '/index.html')

        sitePath = slemp.M('sites').where("id=?", (mid,)).getField('path')

        # nginx
        file = self.getHostConf(name)
        conf = slemp.readFile(file)
        if conf:
            conf = conf.replace(sitePath, path)
            slemp.writeFile(file, conf)

        slemp.M('sites').where("id=?", (mid,)).setField('status', '0')
        slemp.restartWeb()
        msg = slemp.getInfo('Site [{1}] has been disabled!', (name,))
        slemp.writeLog('Website management', msg)
        return slemp.returnJson(True, 'Site is down!')

    def startApi(self):
        mid = request.form.get('id', '').encode('utf-8')
        name = request.form.get('name', '').encode('utf-8')
        path = self.setupPath + '/stop'
        sitePath = slemp.M('sites').where("id=?", (mid,)).getField('path')

        # nginx
        file = self.getHostConf(name)
        conf = slemp.readFile(file)
        if conf:
            conf = conf.replace(path, sitePath)
            slemp.writeFile(file, conf)

        slemp.M('sites').where("id=?", (mid,)).setField('status', '1')
        slemp.restartWeb()
        msg = slemp.getInfo('Site [{1}] has been activated!', (name,))
        slemp.writeLog('website management', msg)
        return slemp.returnJson(True, 'Site is enabled!')

    def getBackupApi(self):
        limit = request.form.get('limit', '').encode('utf-8')
        p = request.form.get('p', '').encode('utf-8')
        mid = request.form.get('search', '').encode('utf-8')

        find = slemp.M('sites').where("id=?", (mid,)).field(
            "id,name,path,status,ps,addtime,edate").find()

        start = (int(p) - 1) * (int(limit))
        _list = slemp.M('backup').where('pid=?', (mid,)).field('id,type,name,pid,filename,size,addtime').limit(
            (str(start)) + ',' + limit).order('id desc').select()
        _ret = {}
        _ret['data'] = _list

        count = slemp.M('backup').where("id=?", (mid,)).count()
        info = {}
        info['count'] = count
        info['tojs'] = 'getBackup'
        info['p'] = p
        info['row'] = limit
        _ret['page'] = slemp.getPage(info)
        _ret['site'] = find
        return slemp.getJson(_ret)

    def toBackupApi(self):
        mid = request.form.get('id', '').encode('utf-8')
        find = slemp.M('sites').where(
            "id=?", (mid,)).field('name,path,id').find()
        fileName = find['name'] + '_' + \
            time.strftime('%Y%m%d_%H%M%S', time.localtime()) + '.zip'
        backupPath = slemp.getBackupDir() + '/site'
        zipName = backupPath + '/' + fileName
        if not (os.path.exists(backupPath)):
            os.makedirs(backupPath)
        tmps = slemp.getRunDir() + '/tmp/panelExec.log'
        execStr = "cd '" + find['path'] + "' && zip '" + \
            zipName + "' -r ./* > " + tmps + " 2>&1"
        # print execStr
        slemp.execShell(execStr)

        if os.path.exists(zipName):
            fsize = os.path.getsize(zipName)
        else:
            fsize = 0
        sql = slemp.M('backup').add('type,name,pid,filename,size,addtime',
                                 (0, fileName, find['id'], zipName, fsize, slemp.getDate()))

        msg = slemp.getInfo('Backup site [{1}] succeeded!', (find['name'],))
        slemp.writeLog('Website management', msg)
        return slemp.returnJson(True, 'Backup successful!')

    def delBackupApi(self):
        mid = request.form.get('id', '').encode('utf-8')
        filename = slemp.M('backup').where(
            "id=?", (mid,)).getField('filename')
        if os.path.exists(filename):
            os.remove(filename)
        name = slemp.M('backup').where("id=?", (mid,)).getField('name')
        msg = slemp.getInfo('Deleting backup [{2}] of website [{1}] succeeded!', (name, filename))
        slemp.writeLog('Website management', msg)
        slemp.M('backup').where("id=?", (mid,)).delete()
        return slemp.returnJson(True, 'Site deleted successfully!')

    def getPhpVersionApi(self):
        return self.getPhpVersion()

    def setPhpVersionApi(self):
        siteName = request.form.get('siteName', '').encode('utf-8')
        version = request.form.get('version', '').encode('utf-8')

        # nginx
        file = self.getHostConf(siteName)
        conf = slemp.readFile(file)
        if conf:
            rep = "enable-php-([0-9]{2,3})\.conf"
            tmp = re.search(rep, conf).group()
            conf = conf.replace(tmp, 'enable-php-' + version + '.conf')
            slemp.writeFile(file, conf)

        slemp.restartWeb()
        msg = slemp.getInfo('The PHP version of the website [{1}] was successfully switched to PHP-{2}', (siteName, version))
        slemp.writeLog("Website management", msg)
        return slemp.returnJson(True, msg)

    def getDomainApi(self):
        pid = request.form.get('pid', '').encode('utf-8')
        return self.getDomain(pid)

    # Get all domain names of a site
    def getSiteDomainsApi(self):
        pid = request.form.get('id', '').encode('utf-8')

        data = {}
        domains = slemp.M('domain').where(
            'pid=?', (pid,)).field('name,id').select()
        binding = slemp.M('binding').where(
            'pid=?', (pid,)).field('domain,id').select()
        if type(binding) == str:
            return binding
        for b in binding:
            tmp = {}
            tmp['name'] = b['domain']
            tmp['id'] = b['id']
            domains.append(tmp)
        data['domains'] = domains
        data['email'] = slemp.M('users').getField('email')
        if data['email'] == 'dentix.id@gmail.com':
            data['email'] = ''
        return slemp.returnJson(True, 'OK', data)

    def getDirBindingApi(self):
        mid = request.form.get('id', '').encode('utf-8')

        path = slemp.M('sites').where('id=?', (mid,)).getField('path')
        if not os.path.exists(path):
            checks = ['/', '/usr', '/etc']
            if path in checks:
                data = {}
                data['dirs'] = []
                data['binding'] = []
                return slemp.returnJson(True, 'OK', data)
            os.system('mkdir -p ' + path)
            os.system('chmod 755 ' + path)
            os.system('chown www:www ' + path)
            siteName = slemp.M('sites').where(
                'id=?', (get.id,)).getField('name')
            slemp.writeLog(
                'Website management', 'Site [' + siteName + '], root directory [' + path + '] does not exist, recreated!')

        dirnames = []
        for filename in os.listdir(path):
            try:
                filePath = path + '/' + filename
                if os.path.islink(filePath):
                    continue
                if os.path.isdir(filePath):
                    dirnames.append(filename)
            except:
                pass

        data = {}
        data['dirs'] = dirnames
        data['binding'] = slemp.M('binding').where('pid=?', (mid,)).field(
            'id,pid,domain,path,port,addtime').select()
        return slemp.returnJson(True, 'OK', data)

    def getDirUserIniApi(self):
        mid = request.form.get('id', '').encode('utf-8')

        path = slemp.M('sites').where('id=?', (mid,)).getField('path')
        name = slemp.M('sites').where("id=?", (mid,)).getField('name')
        data = {}
        data['logs'] = self.getLogsStatus(name)
        data['userini'] = False
        if os.path.exists(path + '/.user.ini'):
            data['userini'] = True
        data['runPath'] = self.getSiteRunPath(mid)
        data['pass'] = self.getHasPwd(name)
        data['path'] = path
        return slemp.returnJson(True, 'OK', data)

    def setDirUserIniApi(self):
        path = request.form.get('path', '').encode('utf-8')
        filename = path + '/.user.ini'
        self.delUserInI(path)
        if os.path.exists(filename):
            slemp.execShell("which chattr && chattr -i " + filename)
            os.remove(filename)
            return slemp.returnJson(True, 'Anti-cross-site settings cleared!')
        slemp.writeFile(filename, 'open_basedir=' + path + '/:/tmp/:/proc/')
        slemp.execShell("which chattr && chattr +i " + filename)
        return slemp.returnJson(True, 'Anti-cross-site settings turned on!')

    def logsOpenApi(self):
        mid = request.form.get('id', '').encode('utf-8')
        name = slemp.M('sites').where("id=?", (mid,)).getField('name')

        # NGINX
        filename = self.getHostConf(name)
        if os.path.exists(filename):
            conf = slemp.readFile(filename)
            rep = self.logsPath + "/" + name + ".log"
            if conf.find(rep) != -1:
                conf = conf.replace(rep, "off")
            else:
                conf = conf.replace('access_log  off', 'access_log  ' + rep)
            slemp.writeFile(filename, conf)

        slemp.restartWeb()
        return slemp.returnJson(True, 'Successful operation!')

    def getCertListApi(self):
        try:
            vpath = self.sslDir
            if not os.path.exists(vpath):
                os.system('mkdir -p ' + vpath)
            data = []
            for d in os.listdir(vpath):
                mpath = vpath + '/' + d + '/info.json'
                if not os.path.exists(mpath):
                    continue
                tmp = slemp.readFile(mpath)
                if not tmp:
                    continue
                tmp1 = json.loads(tmp)
                data.append(tmp1)
            return slemp.returnJson(True, 'OK', data)
        except:
            return slemp.returnJson(True, 'OK', [])

    def getSslApi(self):
        siteName = request.form.get('siteName', '').encode('utf-8')

        path = self.sslDir + siteName
        csrpath = path + "/fullchain.pem"  # Generate certificate path
        keypath = path + "/privkey.pem"  # key file path
        key = slemp.readFile(keypath)
        csr = slemp.readFile(csrpath)

        file = self.getHostConf(siteName)
        conf = slemp.readFile(file)

        keyText = 'ssl_certificate'
        status = True
        stype = 0
        if(conf.find(keyText) == -1):
            status = False
            stype = -1

        toHttps = self.isToHttps(siteName)
        id = slemp.M('sites').where("name=?", (siteName,)).getField('id')
        domains = slemp.M('domain').where(
            "pid=?", (id,)).field('name').select()
        data = {'status': status, 'domain': domains, 'key': key,
                'csr': csr, 'type': stype, 'httpTohttps': toHttps}
        return slemp.returnJson(True, 'OK', data)

    def setSslApi(self):
        siteName = request.form.get('siteName', '').encode('utf-8')
        key = request.form.get('key', '').encode('utf-8')
        csr = request.form.get('csr', '').encode('utf-8')

        path = self.sslDir + siteName
        if not os.path.exists(path):
            slemp.execShell('mkdir -p ' + path)

        csrpath = path + "/fullchain.pem"  # 生成证书路径
        keypath = path + "/privkey.pem"  # key file path

        if(key.find('KEY') == -1):
            return slemp.returnJson(False, 'The key is wrong, please check!')
        if(csr.find('CERTIFICATE') == -1):
            return slemp.returnJson(False, 'Certificate error, please check!')

        slemp.writeFile('/tmp/cert.pl', csr)
        if not slemp.checkCert('/tmp/cert.pl'):
            return slemp.returnJson(False, 'Certificate error, please paste the correct PEM format certificate!')

        slemp.execShell('\\cp -a ' + keypath + ' /tmp/backup1.conf')
        slemp.execShell('\\cp -a ' + csrpath + ' /tmp/backup2.conf')

        # Clean up old certificate chains
        if os.path.exists(path + '/README'):
            slemp.execShell('rm -rf ' + path)
            slemp.execShell('rm -rf ' + path + '-00*')
            slemp.execShell('rm -rf /etc/letsencrypt/archive/' + siteName)
            slemp.execShell(
                'rm -rf /etc/letsencrypt/archive/' + siteName + '-00*')
            slemp.execShell(
                'rm -f /etc/letsencrypt/renewal/' + siteName + '.conf')
            slemp.execShell('rm -rf /etc/letsencrypt/renewal/' +
                         siteName + '-00*.conf')
            slemp.execShell('rm -rf ' + path + '/README')
            slemp.execShell('mkdir -p ' + path)

        slemp.writeFile(keypath, key)
        slemp.writeFile(csrpath, csr)

        # write configuration file
        result = self.setSslConf(siteName)
        # print result['msg']
        if not result['status']:
            return slemp.getJson(result)

        isError = slemp.checkWebConfig()
        if(type(isError) == str):
            slemp.execShell('\\cp -a /tmp/backup1.conf ' + keypath)
            slemp.execShell('\\cp -a /tmp/backup2.conf ' + csrpath)
            return slemp.returnJson(False, 'ERROR: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

        slemp.restartWeb()
        slemp.writeLog('Website management', 'Certificate saved!')
        return slemp.returnJson(True, 'Certificate saved!')

    def setCertToSiteApi(self):
        certName = request.form.get('certName', '').encode('utf-8')
        siteName = request.form.get('siteName', '').encode('utf-8')
        try:
            path = self.sslDir + siteName
            if not os.path.exists(path):
                return slemp.returnJson(False, 'Certificate does not exist!')

            result = self.setSslConf(siteName)
            if not result['status']:
                return slemp.getJson(result)

            slemp.restartWeb()
            slemp.writeLog('Website management', 'Certificate deployed!')
            return slemp.returnJson(True, 'Certificate deployed!')
        except Exception as ex:
            return slemp.returnJson(False, 'Wrong settings, ' + str(ex))

    def removeCertApi(self):
        certName = request.form.get('certName', '').encode('utf-8')
        try:
            path = self.sslDir + certName
            if not os.path.exists(path):
                return slemp.returnJson(False, 'Certificate no longer exists!')
            os.system("rm -rf " + path)
            return slemp.returnJson(True, '证书已删除!')
        except:
            return slemp.returnJson(False, 'Failed to delete!')

    def closeSslConfApi(self):
        siteName = request.form.get('siteName', '').encode('utf-8')

        file = self.getHostConf(siteName)
        conf = slemp.readFile(file)

        if conf:
            rep = "\n\s*#HTTP_TO_HTTPS_START(.|\n){1,300}#HTTP_TO_HTTPS_END"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_certificate\s+.+;\s+ssl_certificate_key\s+.+;"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_protocols\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_ciphers\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_prefer_server_ciphers\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_session_cache\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_session_timeout\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_ecdh_curve\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_session_tickets\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_stapling\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_stapling_verify\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+add_header\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+add_header\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl\s+on;"
            conf = re.sub(rep, '', conf)
            rep = "\s+error_page\s497.+;"
            conf = re.sub(rep, '', conf)
            rep = "\s+if.+server_port.+\n.+\n\s+\s*}"
            conf = re.sub(rep, '', conf)
            rep = "\s+listen\s+443.*;"
            conf = re.sub(rep, '', conf)
            slemp.writeFile(file, conf)

        msg = slemp.getInfo('Website [{1}] turned off SSL successfully!', (siteName,))
        slemp.writeLog('Website management', msg)
        slemp.restartWeb()
        return slemp.returnJson(True, 'SSL is off!')

    def createLetApi(self):
        siteName = request.form.get('siteName', '').encode('utf-8')
        updateOf = request.form.get('updateOf', '')
        domains = request.form.get('domains', '').encode('utf-8')
        force = request.form.get('force', '').encode('utf-8')
        renew = request.form.get('renew', '').encode('utf-8')
        email_args = request.form.get('email', '').encode('utf-8')

        domains = json.loads(domains)
        email = slemp.M('users').getField('email')
        if email_args.strip() != '':
            slemp.M('users').setField('email', email_args)
            email = email_args

        if not len(domains):
            return slemp.returnJson(False, 'Please select a domain name')

        file = self.getHostConf(siteName)
        if os.path.exists(file):
            siteConf = slemp.readFile(file)
            if siteConf.find('301-START') != -1:
                return slemp.returnJson(False, 'Detected that your site has set 301 redirection, please turn off redirection first!')

        letpath = self.sslDir + siteName
        csrpath = letpath + "/fullchain.pem"  # Generate certificate path
        keypath = letpath + "/privkey.pem"  # key file path

        actionstr = updateOf
        siteInfo = slemp.M('sites').where(
            'name=?', (siteName,)).field('id,name,path').find()
        path = self.getSitePath(siteName)
        srcPath = siteInfo['path']

        # Check if acem is installed
        if slemp.isAppleSystem():
            user = slemp.execShell(
                "who | sed -n '2, 1p' |awk '{print $1}'")[0].strip()
            acem = '/Users/' + user + '/.acme.sh/acme.sh'
        else:
            acem = '/root/.acme.sh/acme.sh'
        if not os.path.exists(acem):
            acem = '/.acme.sh/acme.sh'
        if not os.path.exists(acem):
            try:
                slemp.execShell("curl -sS curl https://get.acme.sh | sh")
            except:
                return slemp.returnJson(False, 'Attempt to install ACME automatically failed, please try to install manually by the following command <p> install command: curl https://get.acme.sh | sh</p>' + acem)
        if not os.path.exists(acem):
            return slemp.returnJson(False, 'Attempt to install ACME automatically failed, please try to install manually by the following command <p> install command: curl https://get.acme.sh | sh</p>' + acem)

        force_bool = False
        if force == 'true':
            force_bool = True

        if renew == 'true':
            execStr = acem + " --renew --yes-I-know-dns-manual-mode-enough-go-ahead-please"
        else:
            execStr = acem + " --issue --force"

        # Determining the Primary Domain Order
        domainsTmp = []
        if siteName in domains:
            domainsTmp.append(siteName)
        for domainTmp in domains:
            if domainTmp == siteName:
                continue
            domainsTmp.append(domainTmp)
        domains = domainsTmp

        domainCount = 0
        for domain in domains:
            if slemp.checkIp(domain):
                continue
            if domain.find('*.') != -1:
                return slemp.returnJson(False, 'Pan-domain name cannot use the [document verification] method to apply for a certificate!')
            execStr += ' -w ' + path
            execStr += ' -d ' + domain
            domainCount += 1
        if domainCount == 0:
            return slemp.returnJson(False, 'Please select a domain name (excluding IP address and generic domain name)!')

        home_path = '/root/.acme.sh/' + domains[0]
        home_cert = home_path + '/fullchain.cer'
        home_key = home_path + '/' + domains[0] + '.key'

        if not os.path.exists(home_cert):
            home_path = '/.acme.sh/' + domains[0]
            home_cert = home_path + '/fullchain.cer'
            home_key = home_path + '/' + domains[0] + '.key'

        if slemp.isAppleSystem():
            user = slemp.execShell(
                "who | sed -n '2, 1p' |awk '{print $1}'")[0].strip()
            acem = '/Users/' + user + '/.acme.sh/'
            if not os.path.exists(home_cert):
                home_path = acem + domains[0]
                home_cert = home_path + '/fullchain.cer'
                home_key = home_path + '/' + domains[0] + '.key'

        # print home_cert
        cmd = 'export ACCOUNT_EMAIL=' + email + ' && ' + execStr
        print domains
        print cmd
        result = slemp.execShell(cmd)

        if not os.path.exists(home_cert.replace("\*", "*")):
            data = {}
            data['err'] = result
            data['out'] = result[0]
            data['msg'] = 'The issuance failed, we cannot verify your domain name: <p>1. Check whether the domain name is bound to the corresponding site.</p>\
                <p>2. Check whether the domain name is correctly resolved to this server, or the resolution has not fully taken effect.</p>\
                <p>3. If your site is set up with a reverse proxy or uses a CDN, please turn it off first.</p>\
                <p>4. If your site has set 301 redirection, please close it first.</p>\
                <p>5. If the above checks confirm that there is no problem, please try to change the DNS service provider.</p>'
            data['result'] = {}
            if result[1].find('new-authz error:') != -1:
                data['result'] = json.loads(
                    re.search("{.+}", result[1]).group())
                if data['result']['status'] == 429:
                    data['msg'] = 'The issuance failed, the number of failed attempts to apply for a certificate has reached the upper limit! <p>1. Check whether the domain name is bound to the corresponding site.</p>\
                        <p>2. Check whether the domain name is correctly resolved to this server, or the resolution has not fully taken effect.</p>\
                        <p>3. If your site is set up with a reverse proxy or uses a CDN, please turn it off first.</p>\
                        <p>4. If your site has set 301 redirection, please close it first.</p>\
                        <p>5. If the above checks confirm that there is no problem, please try to change the DNS service provider.</p>'
            data['status'] = False
            return slemp.getJson(data)

        if not os.path.exists(letpath):
            slemp.execShell("mkdir -p " + letpath)
        slemp.execShell("ln -sf \"" + home_cert + "\" \"" + csrpath + '"')
        slemp.execShell("ln -sf \"" + home_key + "\" \"" + keypath + '"')
        slemp.execShell('echo "let" > "' + letpath + '/README"')
        if(actionstr == '2'):
            return slemp.returnJson(True, 'Certificate updated!')

        # write configuration file
        result = self.setSslConf(siteName)
        if not result['status']:
            return slemp.getJson(result)
        result['csr'] = slemp.readFile(csrpath)
        result['key'] = slemp.readFile(keypath)
        slemp.restartWeb()

        return slemp.returnJson(True, 'OK', result)

    def httpToHttpsApi(self):
        siteName = request.form.get('siteName', '').encode('utf-8')
        file = self.getHostConf(siteName)
        conf = slemp.readFile(file)
        if conf:
            # if conf.find('ssl_certificate') == -1:
            #     return slemp.returnJson(False, 'SSL is not currently enabled')
            to = """#error_page 404/404.html;
    # HTTP_TO_HTTPS_START
    if ($server_port !~ 443){
        rewrite ^(/.*)$ https://$host$1 permanent;
    }
    # HTTP_TO_HTTPS_END"""
            conf = conf.replace('#error_page 404/404.html;', to)
            slemp.writeFile(file, conf)

        slemp.restartWeb()
        return slemp.returnJson(True, 'The setting is successful! The certificate should also be set!')

    def closeToHttpsApi(self):
        siteName = request.form.get('siteName', '').encode('utf-8')
        file = self.getHostConf(siteName)
        conf = slemp.readFile(file)
        if conf:
            rep = "\n\s*#HTTP_TO_HTTPS_START(.|\n){1,300}#HTTP_TO_HTTPS_END"
            conf = re.sub(rep, '', conf)
            rep = "\s+if.+server_port.+\n.+\n\s+\s*}"
            conf = re.sub(rep, '', conf)
            slemp.writeFile(file, conf)

        slemp.restartWeb()
        return slemp.returnJson(True, 'Close HTTPS jump successfully!')

    def getIndexApi(self):
        sid = request.form.get('id', '').encode('utf-8')
        data = {}
        index = self.getIndex(sid)
        data['index'] = index
        return slemp.getJson(data)

    def setIndexApi(self):
        sid = request.form.get('id', '').encode('utf-8')
        index = request.form.get('index', '').encode('utf-8')
        return self.setIndex(sid, index)

    def getLimitNetApi(self):
        sid = request.form.get('id', '').encode('utf-8')
        return self.getLimitNet(sid)

    def saveLimitNetApi(self):
        sid = request.form.get('id', '').encode('utf-8')
        perserver = request.form.get('perserver', '').encode('utf-8')
        perip = request.form.get('perip', '').encode('utf-8')
        limit_rate = request.form.get('limit_rate', '').encode('utf-8')
        return self.saveLimitNet(sid, perserver, perip, limit_rate)

    def closeLimitNetApi(self):
        sid = request.form.get('id', '').encode('utf-8')
        return self.closeLimitNet(sid)

    def getSecurityApi(self):
        sid = request.form.get('id', '').encode('utf-8')
        name = request.form.get('name', '').encode('utf-8')
        return self.getSecurity(sid, name)

    def setSecurityApi(self):
        fix = request.form.get('fix', '').encode('utf-8')
        domains = request.form.get('domains', '').encode('utf-8')
        status = request.form.get('status', '').encode('utf-8')
        name = request.form.get('name', '').encode('utf-8')
        sid = request.form.get('id', '').encode('utf-8')
        return self.setSecurity(sid, name, fix, domains, status)

    def getLogsApi(self):
        siteName = request.form.get('siteName', '').encode('utf-8')
        return self.getLogs(siteName)

    def getSitePhpVersionApi(self):
        siteName = request.form.get('siteName', '').encode('utf-8')
        return self.getSitePhpVersion(siteName)

    def getHostConfApi(self):
        siteName = request.form.get('siteName', '').encode('utf-8')
        host = self.getHostConf(siteName)
        return slemp.getJson({'host': host})

    def getRewriteConfApi(self):
        siteName = request.form.get('siteName', '').encode('utf-8')
        rewrite = self.getRewriteConf(siteName)
        return slemp.getJson({'rewrite': rewrite})

    def getRewriteTplApi(self):
        tplname = request.form.get('tplname', '').encode('utf-8')
        file = slemp.getRunDir() + '/rewrite/nginx/' + tplname + '.conf'
        if not os.path.exists(file):
            return slemp.returnJson(False, 'Template does not exist!')
        return slemp.returnJson(True, 'OK', file)

    def getRewriteListApi(self):
        rlist = self.getRewriteList()
        return slemp.getJson(rlist)

    def getRootDirApi(self):
        data = {}
        data['dir'] = slemp.getWwwDir()
        return slemp.getJson(data)

    def setEndDateApi(self):
        sid = request.form.get('id', '').encode('utf-8')
        edate = request.form.get('edate', '').encode('utf-8')
        return self.setEndDate(sid, edate)

    def addApi(self):
        webname = request.form.get('webinfo', '').encode('utf-8')
        ps = request.form.get('ps', '').encode('utf-8')
        path = request.form.get('path', '').encode('utf-8')
        version = request.form.get('version', '').encode('utf-8')
        port = request.form.get('port', '').encode('utf-8')
        return self.add(webname, port, ps, path, version)

    def addDomainApi(self):
        isError = slemp.checkWebConfig()
        if isError != True:
            return slemp.returnJson(False, 'ERROR: An error was detected in the configuration file, please exclude it before proceeding.<br><br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

        domain = request.form.get('domain', '').encode('utf-8')
        webname = request.form.get('webname', '').encode('utf-8')
        pid = request.form.get('id', '').encode('utf-8')
        if len(domain) < 3:
            return slemp.returnJson(False, 'Domain name cannot be empty!')
        domains = domain.split(',')
        for domain in domains:
            if domain == "":
                continue
            domain = domain.split(':')
            # print domain
            domain_name = self.toPunycode(domain[0])
            domain_port = '80'

            reg = "^([\w\-\*]{1,100}\.){1,4}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$"
            if not re.match(reg, domain_name):
                return slemp.returnJson(False, 'The domain name format is incorrect!')

            if len(domain) == 2:
                domain_port = domain[1]
            if domain_port == "":
                domain_port = "80"

            if not slemp.checkPort(domain_port):
                return slemp.returnJson(False, 'Port range is invalid!')

            opid = slemp.M('domain').where(
                "name=? AND (port=? OR pid=?)", (domain, domain_port, pid)).getField('pid')
            if opid:
                if slemp.M('sites').where('id=?', (opid,)).count():
                    return slemp.returnJson(False, 'The specified domain name has been bound!')
                slemp.M('domain').where('pid=?', (opid,)).delete()

            if slemp.M('binding').where('domain=?', (domain,)).count():
                return slemp.returnJson(False, 'The domain name you added already exists!')

            self.nginxAddDomain(webname, domain_name, domain_port)

            slemp.restartWeb()
            msg = slemp.getInfo('Website [{1}] added domain name [{2}] successfully!', (webname, domain_name))
            slemp.writeLog('Website management', msg)
            slemp.M('domain').add('pid,name,port,addtime',
                               (pid, domain_name, domain_port, slemp.getDate()))

        return slemp.returnJson(True, 'Domain name added successfully!')

    def addDirBindApi(self):
        pid = request.form.get('id', '').encode('utf-8')
        domain = request.form.get('domain', '').encode('utf-8')
        dirName = request.form.get('dirName', '').encode('utf-8')
        tmp = domain.split(':')
        domain = tmp[0]
        port = '80'
        if len(tmp) > 1:
            port = tmp[1]
        if dirName == '':
            slemp.returnJson(False, 'Directory cannot be empty!')

        reg = "^([\w\-\*]{1,100}\.){1,4}(\w{1,10}|\w{1,10}\.\w{1,10})$"
        if not re.match(reg, domain):
            return slemp.returnJson(False, 'The primary domain name format is incorrect!')

        siteInfo = slemp.M('sites').where(
            "id=?", (pid,)).field('id,path,name').find()
        webdir = siteInfo['path'] + '/' + dirName

        if slemp.M('binding').where("domain=?", (domain,)).count() > 0:
            return slemp.returnJson(False, 'The domain name you added already exists!')
        if slemp.M('domain').where("name=?", (domain,)).count() > 0:
            return slemp.returnJson(False, 'The domain name you added already exists!')

        filename = self.getHostConf(siteInfo['name'])
        conf = slemp.readFile(filename)
        if conf:
            rep = "enable-php-([0-9]{2,3})\.conf"
            tmp = re.search(rep, conf).groups()
            version = tmp[0]

            source_dirbind_tpl = slemp.getRunDir() + '/data/tpl/nginx_dirbind.conf'
            content = slemp.readFile(source_dirbind_tpl)
            content = content.replace('{$PORT}', port)
            content = content.replace('{$PHPVER}', version)
            content = content.replace('{$DIRBIND}', domain)
            content = content.replace('{$ROOT_DIR}', webdir)
            content = content.replace('{$SERVER_MAIN}', siteInfo['name'])
            content = content.replace('{$OR_REWRITE}', self.rewritePath)
            content = content.replace('{$LOGPATH}', slemp.getLogsDir())

            conf += "\r\n" + content
            shutil.copyfile(filename, '/tmp/backup.conf')
            slemp.writeFile(filename, conf)
        conf = slemp.readFile(filename)

        # Check for configuration errors
        isError = slemp.checkWebConfig()
        if isError != True:
            shutil.copyfile('/tmp/backup.conf', filename)
            return slemp.returnJson(False, 'ERROR: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

        slemp.M('binding').add('pid,domain,port,path,addtime',
                            (pid, domain, port, dirName, slemp.getDate()))

        slemp.restartWeb()
        msg = slemp.getInfo('Site [{1}] subdirectory [{2}] is bound to [{3}]',
                         (siteInfo['name'], dirName, domain))
        slemp.writeLog('Website management', msg)
        return slemp.returnJson(True, 'Added successfully!')

    def delDirBindApi(self):
        mid = request.form.get('id', '').encode('utf-8')
        binding = slemp.M('binding').where(
            "id=?", (mid,)).field('id,pid,domain,path').find()
        siteName = slemp.M('sites').where(
            "id=?", (binding['pid'],)).getField('name')

        filename = self.getHostConf(siteName)
        conf = slemp.readFile(filename)
        if conf:
            rep = "\s*.+BINDING-" + \
                binding['domain'] + \
                "-START(.|\n)+BINDING-" + binding['domain'] + "-END"
            conf = re.sub(rep, '', conf)
            slemp.writeFile(filename, conf)

        slemp.M('binding').where("id=?", (mid,)).delete()

        filename = self.getDirBindRewrite(siteName,  binding['path'])
        if os.path.exists(filename):
            os.remove(filename)
        slemp.restartWeb()
        msg = slemp.getInfo('Delete site [{1}] subdirectory [{2}] binding',
                         (siteName, binding['path']))
        slemp.writeLog('Website management', msg)
        return slemp.returnJson(True, 'Successfully deleted!')

    # Take subdirectory Rewrite
    def getDirBindRewriteApi(self):
        mid = request.form.get('id', '').encode('utf-8')
        add = request.form.get('add', '0').encode('utf-8')
        find = slemp.M('binding').where(
            "id=?", (mid,)).field('id,pid,domain,path').find()
        site = slemp.M('sites').where(
            "id=?", (find['pid'],)).field('id,name,path').find()

        filename = self.getDirBindRewrite(site['name'], find['path'])
        if add == '1':
            slemp.writeFile(filename, '')
            file = self.getHostConf(site['name'])
            conf = slemp.readFile(file)
            domain = find['domain']
            rep = "\n#BINDING-" + domain + \
                "-START(.|\n)+BINDING-" + domain + "-END"
            tmp = re.search(rep, conf).group()
            dirConf = tmp.replace('rewrite/' + site['name'] + '.conf;', 'rewrite/' + site[
                                  'name'] + '_' + find['path'] + '.conf;')
            conf = conf.replace(tmp, dirConf)
            slemp.writeFile(file, conf)
        data = {}
        data['rewrite_dir'] = self.rewritePath
        data['status'] = False
        if os.path.exists(filename):
            data['status'] = True
            data['data'] = slemp.readFile(filename)
            data['rlist'] = []
            for ds in os.listdir(self.rewritePath):
                if ds == 'list.txt':
                    continue
                data['rlist'].append(ds[0:len(ds) - 5])
            data['filename'] = filename
        return slemp.getJson(data)

    # Modify physical path
    def setPathApi(self):
        mid = request.form.get('id', '').encode('utf-8')
        path = request.form.get('path', '').encode('utf-8')

        path = self.getPath(path)
        if path == "" or mid == '0':
            return slemp.returnJson(False,  "Directory cannot be empty!")

        import files_api
        if not files_api.files_api().checkDir(path):
            return slemp.returnJson(False,  "Cannot use system critical directory as site directory")

        siteFind = slemp.M("sites").where(
            "id=?", (mid,)).field('path,name').find()
        if siteFind["path"] == path:
            return slemp.returnJson(False,  "Consistent with the original path, no need to modify!")
        file = self.getHostConf(siteFind['name'])
        conf = slemp.readFile(file)
        if conf:
            conf = conf.replace(siteFind['path'], path)
            slemp.writeFile(file, conf)

        # create basedir
        # userIni = path + '/.user.ini'
        # if os.path.exists(userIni):
            # slemp.execShell("chattr -i " + userIni)
        # slemp.writeFile(userIni, 'open_basedir=' + path + '/:/tmp/:/proc/')
        # slemp.execShell('chmod 644 ' + userIni)
        # slemp.execShell('chown root:root ' + userIni)
        # slemp.execShell('chattr +i ' + userIni)

        slemp.restartWeb()
        slemp.M("sites").where("id=?", (mid,)).setField('path', path)
        msg = slemp.getInfo('Modifying the physical path of the website [{1}] succeeded!', (siteFind['name'],))
        slemp.writeLog('Website management', msg)
        return slemp.returnJson(True,  "Set up successfully!")

    # Set the current site running directory
    def setSiteRunPathApi(self):
        mid = request.form.get('id', '').encode('utf-8')
        runPath = request.form.get('runPath', '').encode('utf-8')
        siteName = slemp.M('sites').where('id=?', (mid,)).getField('name')
        sitePath = slemp.M('sites').where('id=?', (mid,)).getField('path')

        newPath = sitePath + runPath
        # Handling Nginx
        filename = self.getHostConf(siteName)
        if os.path.exists(filename):
            conf = slemp.readFile(filename)
            rep = '\s*root\s*(.+);'
            path = re.search(rep, conf).groups()[0]
            conf = conf.replace(path, newPath)
            slemp.writeFile(filename, conf)

        self.delUserInI(sitePath)
        self.setDirUserINI(newPath)

        slemp.restartWeb()
        return slemp.returnJson(True, 'Set up successfully!')

    # Set up directory encryption
    def setHasPwdApi(self):
        username = request.form.get('username', '').encode('utf-8')
        password = request.form.get('password', '').encode('utf-8')
        siteName = request.form.get('siteName', '').encode('utf-8')
        mid = request.form.get('id', '')

        if len(username.strip()) == 0 or len(password.strip()) == 0:
            return slemp.returnJson(False, 'Username or password cannot be empty!')

        if siteName == '':
            siteName = slemp.M('sites').where('id=?', (mid,)).getField('name')

        # self.closeHasPwd(get)
        filename = self.passPath + '/' + siteName + '.pass'
        print filename
        passconf = username + ':' + slemp.hasPwd(password)

        if siteName == 'phpmyadmin':
            configFile = self.getHostConf('phpmyadmin')
        else:
            configFile = self.getHostConf(siteName)

        # Handling Nginx configuration
        conf = slemp.readFile(configFile)
        if conf:
            rep = '#error_page   404   /404.html;'
            if conf.find(rep) == -1:
                rep = '#error_page 404/404.html;'
            data = '''
    # AUTH_START
    auth_basic "Authorization";
    auth_basic_user_file %s;
    # AUTH_END''' % (filename,)
            conf = conf.replace(rep, rep + data)
            slemp.writeFile(configFile, conf)
        # write password configuration
        passDir = self.passPath
        if not os.path.exists(passDir):
            slemp.execShell('mkdir -p ' + passDir)
        slemp.writeFile(filename, passconf)

        slemp.restartWeb()
        msg = slemp.getInfo('Set site [{1}] to require password authentication!', (siteName,))
        slemp.writeLog("Website management", msg)
        return slemp.returnJson(True, 'Set up successfully!')

    # Cancel directory encryption
    def closeHasPwdApi(self):
        siteName = request.form.get('siteName', '').encode('utf-8')
        mid = request.form.get('id', '')
        if siteName == '':
            siteName = slemp.M('sites').where('id=?', (mid,)).getField('name')

        if siteName == 'phpmyadmin':
            configFile = self.getHostConf('phpmyadmin')
        else:
            configFile = self.getHostConf(siteName)

        if os.path.exists(configFile):
            conf = slemp.readFile(configFile)
            rep = "\n\s*#AUTH_START(.|\n){1,200}#AUTH_END"
            conf = re.sub(rep, '', conf)
            slemp.writeFile(configFile, conf)

        slemp.restartWeb()
        msg = slemp.getInfo('Clear password authentication for site [{1}]!', (siteName,))
        slemp.writeLog("Website management", msg)
        return slemp.returnJson(True, 'Set up successfully!')

    def delDomainApi(self):
        domain = request.form.get('domain', '').encode('utf-8')
        webname = request.form.get('webname', '').encode('utf-8')
        port = request.form.get('port', '').encode('utf-8')
        pid = request.form.get('id', '')

        find = slemp.M('domain').where("pid=? AND name=?",
                                    (pid, domain)).field('id,name').find()

        domain_count = slemp.M('domain').where("pid=?", (pid,)).count()
        if domain_count == 1:
            return slemp.returnJson(False, 'The last domain name cannot be deleted!')

        file = self.getHostConf(webname)
        conf = slemp.readFile(file)
        if conf:
            # delete domain
            rep = "server_name\s+(.+);"
            tmp = re.search(rep, conf).group()
            newServerName = tmp.replace(' ' + domain + ';', ';')
            newServerName = newServerName.replace(' ' + domain + ' ', ' ')
            conf = conf.replace(tmp, newServerName)

            # delete port
            rep = "listen\s+([0-9]+);"
            tmp = re.findall(rep, conf)
            port_count = slemp.M('domain').where(
                'pid=? AND port=?', (pid, port)).count()
            if slemp.inArray(tmp, port) == True and port_count < 2:
                rep = "\n*\s+listen\s+" + port + ";"
                conf = re.sub(rep, '', conf)
            # Preservation arrangement
            slemp.writeFile(file, conf)

        slemp.M('domain').where("id=?", (find['id'],)).delete()
        msg = slemp.getInfo('Website [{1}] deleted domain name [{2}] successfully!', (webname, domain))
        slemp.writeLog('Website management', msg)
        slemp.restartWeb()
        return slemp.returnJson(True, 'Site deleted successfully!')

    def deleteApi(self):
        sid = request.form.get('id', '').encode('utf-8')
        webname = request.form.get('webname', '').encode('utf-8')
        path = request.form.get('path', '0').encode('utf-8')
        return self.delete(sid, webname, path)

    def getProxyListApi(self):
        siteName = request.form.get('siteName', '').encode('utf-8')
        conf_path = self.getHostConf(siteName)
        old_conf = slemp.readFile(conf_path)
        rep = "(#PROXY-START(\n|.)+#PROXY-END)"
        url_rep = "proxy_pass (.*);|ProxyPass\s/\s(.*)|Host\s(.*);"
        host_rep = "Host\s(.*);"

        if re.search(rep, old_conf):
            # Construct proxy configuration
            if w == "nginx":
                get.todomain = str(re.search(host_rep, old_conf).group(1))
                get.proxysite = str(re.search(url_rep, old_conf).group(1))
            else:
                get.todomain = ""
                get.proxysite = str(re.search(url_rep, old_conf).group(2))
            get.proxyname = "old proxy"
            get.type = 1
            get.proxydir = "/"
            get.advanced = 0
            get.cachetime = 1
            get.cache = 0
            get.subfilter = "[{\"sub1\":\"\",\"sub2\":\"\"},{\"sub1\":\"\",\"sub2\":\"\"},{\"sub1\":\"\",\"sub2\":\"\"}]"

            # proxyname_md5 = self.__calc_md5(get.proxyname)
            # Backup and replace old virtual host configuration files
            os.system("cp %s %s_bak" % (conf_path, conf_path))
            conf = re.sub(rep, "", old_conf)
            slemp.writeFile(conf_path, conf)

            # self.createProxy(get)
            slemp.restartWeb()

        proxyUrl = self.__read_config(self.__proxyfile)
        sitename = sitename
        proxylist = []
        for i in proxyUrl:
            if i["sitename"] == sitename:
                proxylist.append(i)
        return slemp.getJson(proxylist)

    def getSiteTypesApi(self):
        # Take the website category
        data = slemp.M("site_types").field("id,name").order("id asc").select()
        data.insert(0, {"id": 0, "name": "Default"})
        return slemp.getJson(data)

    def getSiteDocApi(self):
        stype = request.form.get('type', '0').strip().encode('utf-8')
        vlist = []
        vlist.append('')
        vlist.append(slemp.getServerDir() +
                     '/openresty/nginx/html/index.html')
        vlist.append(slemp.getServerDir() + '/openresty/nginx/html/404.html')
        vlist.append(slemp.getServerDir() +
                     '/openresty/nginx/html/index.html')
        vlist.append(slemp.getServerDir() + '/web_conf/stop/index.html')
        data = {}
        data['path'] = vlist[int(stype)]
        return slemp.returnJson(True, 'ok', data)

    def addSiteTypeApi(self):
        name = request.form.get('name', '').strip().encode('utf-8')
        if not name:
            return slemp.returnJson(False, "Category name cannot be empty")
        if len(name) > 18:
            return slemp.returnJson(False, "The length of the category name cannot exceed 18 letters")
        if slemp.M('site_types').count() >= 10:
            return slemp.returnJson(False, 'Add up to 10 categories!')
        if slemp.M('site_types').where('name=?', (name,)).count() > 0:
            return slemp.returnJson(False, "The specified category name already exists!")
        slemp.M('site_types').add("name", (name,))
        return slemp.returnJson(True, 'Added successfully!')

    def removeSiteTypeApi(self):
        mid = request.form.get('id', '').encode('utf-8')
        if slemp.M('site_types').where('id=?', (mid,)).count() == 0:
            return slemp.returnJson(False, "The specified category does not exist!")
        slemp.M('site_types').where('id=?', (mid,)).delete()
        slemp.M("sites").where("type_id=?", (mid,)).save("type_id", (0,))
        return slemp.returnJson(True, "Category deleted!")

    def modifySiteTypeNameApi(self):
        # Modify website category name
        name = request.form.get('name', '').strip().encode('utf-8')
        mid = request.form.get('id', '').encode('utf-8')
        if not name:
            return slemp.returnJson(False, "Category name cannot be empty")
        if len(name) > 18:
            return slemp.returnJson(False, "The length of the category name cannot exceed 18 letters")
        if slemp.M('site_types').where('id=?', (mid,)).count() == 0:
            return slemp.returnJson(False, "The specified category does not exist!")
        slemp.M('site_types').where('id=?', (mid,)).setField('name', name)
        return slemp.returnJson(True, "Successfully modified!")

    def setSiteTypeApi(self):
        # Set the category of the specified site
        site_ids = request.form.get('site_ids', '').encode('utf-8')
        mid = request.form.get('id', '').encode('utf-8')
        site_ids = json.loads(site_ids)
        for sid in site_ids:
            print slemp.M('sites').where('id=?', (sid,)).setField('type_id', mid)
        return slemp.returnJson(True, "Set successfully!")

    ##### ----- end   ----- ###

    # Domain code conversion
    def toPunycode(self, domain):
        import re
        if sys.version_info[0] == 2:
            domain = domain.encode('utf8')
        tmp = domain.split('.')
        newdomain = ''
        for dkey in tmp:
                # match non-ascii characters
            match = re.search(u"[\x80-\xff]+", dkey)
            if not match:
                newdomain += dkey + '.'
            else:
                newdomain += 'xn--' + \
                    dkey.decode('utf-8').encode('punycode') + '.'
        return newdomain[0:-1]

    # Chinese path processing
    def toPunycodePath(self, path):
        if sys.version_info[0] == 2:
            path = path.encode('utf-8')
        if os.path.exists(path):
            return path
        import re
        match = re.search(u"[\x80-\xff]+", path)
        if not match:
            return path
        npath = ''
        for ph in path.split('/'):
            npath += '/' + self.toPunycode(ph)
        return npath.replace('//', '/')

    # path processing
    def getPath(self, path):
        if path[-1] == '/':
            return path[0:-1]
        return path

    def getSitePath(self, siteName):
        file = self.getHostConf(siteName)
        if os.path.exists(file):
            conf = slemp.readFile(file)
            rep = '\s*root\s*(.+);'
            path = re.search(rep, conf).groups()[0]
            return path
        return ''

    # Get the current site's running directory
    def getSiteRunPath(self, mid):
        siteName = slemp.M('sites').where('id=?', (mid,)).getField('name')
        sitePath = slemp.M('sites').where('id=?', (mid,)).getField('path')
        path = sitePath

        filename = self.getHostConf(siteName)
        if os.path.exists(filename):
            conf = slemp.readFile(filename)
            rep = '\s*root\s*(.+);'
            path = re.search(rep, conf).groups()[0]

        data = {}
        if sitePath == path:
            data['runPath'] = '/'
        else:
            data['runPath'] = path.replace(sitePath, '')

        dirnames = []
        dirnames.append('/')
        for filename in os.listdir(sitePath):
            try:
                filePath = sitePath + '/' + filename
                if os.path.islink(filePath):
                    continue
                if os.path.isdir(filePath):
                    dirnames.append('/' + filename)
            except:
                pass

        data['dirs'] = dirnames
        return data

    def getHostConf(self, siteName):
        return self.vhostPath + '/' + siteName + '.conf'

    def getRewriteConf(self, siteName):
        return self.rewritePath + '/' + siteName + '.conf'

    def getDirBindRewrite(self, siteName, dirname):
        return self.rewritePath + '/' + siteName + '_' + dirname + '.conf'

    def getIndexConf(self):
        return slemp.getServerDir() + '/openresty/nginx/conf/nginx.conf'

    def getDomain(self, pid):
        _list = slemp.M('domain').where("pid=?", (pid,)).field(
            'id,pid,name,port,addtime').select()
        return slemp.getJson(_list)

    def getLogs(self, siteName):
        logPath = slemp.getLogsDir() + '/' + siteName + '.log'
        if not os.path.exists(logPath):
            return slemp.returnJson(False, 'Log is empty')
        return slemp.returnJson(True, slemp.getNumLines(logPath, 100))

    # Get log status
    def getLogsStatus(self, siteName):
        filename = self.getHostConf(siteName)
        conf = slemp.readFile(filename)
        if conf.find('#ErrorLog') != -1:
            return False
        if conf.find("access_log  /dev/null") != -1:
            return False
        return True

    # Get directory encryption status
    def getHasPwd(self, siteName):
        filename = self.getHostConf(siteName)
        conf = slemp.readFile(filename)
        if conf.find('#AUTH_START') != -1:
            return True
        return False

    def getSitePhpVersion(self, siteName):
        conf = slemp.readFile(self.getHostConf(siteName))
        rep = "enable-php-([0-9]{2,3})\.conf"
        tmp = re.search(rep, conf).groups()
        data = {}
        data['phpversion'] = tmp[0]
        return slemp.getJson(data)

    def getIndex(self, sid):
        siteName = slemp.M('sites').where("id=?", (sid,)).getField('name')
        file = self.getHostConf(siteName)
        conf = slemp.readFile(file)
        rep = "\s+index\s+(.+);"
        tmp = re.search(rep, conf).groups()
        return tmp[0].replace(' ', ',')

    def setIndex(self, sid, index):
        if index.find('.') == -1:
            return slemp.returnJson(False,  'The default document format is incorrect, for example: index.html')

        index = index.replace(' ', '')
        index = index.replace(',,', ',')

        if len(index) < 3:
            return slemp.returnJson(False,  'Default document cannot be empt!')

        siteName = slemp.M('sites').where("id=?", (sid,)).getField('name')
        index_l = index.replace(",", " ")
        file = self.getHostConf(siteName)
        conf = slemp.readFile(file)
        if conf:
            rep = "\s+index\s+.+;"
            conf = re.sub(rep, "\n\tindex " + index_l + ";", conf)
            slemp.writeFile(file, conf)

        slemp.writeLog('Site Manager', 'Defualt document of site [{1}] is [{2}]', (siteName, index_l))
        return slemp.returnJson(True,  'Set successfully!')

    def getLimitNet(self, sid):
        siteName = slemp.M('sites').where("id=?", (sid,)).getField('name')
        filename = self.getHostConf(siteName)
        # total site concurrency
        data = {}
        conf = slemp.readFile(filename)
        try:
            rep = "\s+limit_conn\s+perserver\s+([0-9]+);"
            tmp = re.search(rep, conf).groups()
            data['perserver'] = int(tmp[0])

            # IP concurrency limit
            rep = "\s+limit_conn\s+perip\s+([0-9]+);"
            tmp = re.search(rep, conf).groups()
            data['perip'] = int(tmp[0])

            # request concurrency limit
            rep = "\s+limit_rate\s+([0-9]+)\w+;"
            tmp = re.search(rep, conf).groups()
            data['limit_rate'] = int(tmp[0])
        except:
            data['perserver'] = 0
            data['perip'] = 0
            data['limit_rate'] = 0

        return slemp.getJson(data)

    def checkIndexConf(self):
        limit = self.getIndexConf()
        nginxConf = slemp.readFile(limit)
        limitConf = "limit_conn_zone $binary_remote_addr zone=perip:10m;\n\t\tlimit_conn_zone $server_name zone=perserver:10m;"
        nginxConf = nginxConf.replace(
            "#limit_conn_zone $binary_remote_addr zone=perip:10m;", limitConf)
        slemp.writeFile(limit, nginxConf)

    def saveLimitNet(self, sid, perserver, perip, limit_rate):

        str_perserver = 'limit_conn perserver ' + perserver + ';'
        str_perip = 'limit_conn perip ' + perip + ';'
        str_limit_rate = 'limit_rate ' + limit_rate + 'k;'

        siteName = slemp.M('sites').where("id=?", (sid,)).getField('name')
        filename = self.getHostConf(siteName)

        conf = slemp.readFile(filename)
        if(conf.find('limit_conn perserver') != -1):
            # replace total concurrency
            rep = "limit_conn\s+perserver\s+([0-9]+);"
            conf = re.sub(rep, str_perserver, conf)

            # Replace IP concurrency limit
            rep = "limit_conn\s+perip\s+([0-9]+);"
            conf = re.sub(rep, str_perip, conf)

            # Replace request traffic limit
            rep = "limit_rate\s+([0-9]+)\w+;"
            conf = re.sub(rep, str_limit_rate, conf)
        else:
            conf = conf.replace('#error_page 404/404.html;', "#error_page 404/404.html;\n    " +
                                str_perserver + "\n    " + str_perip + "\n    " + str_limit_rate)

        slemp.writeFile(filename, conf)
        slemp.restartWeb()
        slemp.writeLog('Site manager', 'Pembatasan lalu lintas situs web [{1}] aktif!', (siteName,))
        return slemp.returnJson(True, 'Set successfully!')

    def closeLimitNet(self, sid):
        siteName = slemp.M('sites').where("id=?", (sid,)).getField('name')
        filename = self.getHostConf(siteName)
        conf = slemp.readFile(filename)
        # clean up total concurrency
        rep = "\s+limit_conn\s+perserver\s+([0-9]+);"
        conf = re.sub(rep, '', conf)

        # Clean up IP concurrency limit
        rep = "\s+limit_conn\s+perip\s+([0-9]+);"
        conf = re.sub(rep, '', conf)

        # Clear request traffic limit
        rep = "\s+limit_rate\s+([0-9]+)\w+;"
        conf = re.sub(rep, '', conf)
        slemp.writeFile(filename, conf)
        slemp.restartWeb()
        slemp.writeLog(
            'Site Management', 'Site [{1}] traffic control turned off!', (siteName,))
        return slemp.returnJson(True, 'Traffic throttling is turned off!')

    def getSecurity(self, sid, name):
        filename = self.getHostConf(name)
        conf = slemp.readFile(filename)
        data = {}
        if conf.find('SECURITY-START') != -1:
            rep = "#SECURITY-START(\n|.){1,500}#SECURITY-END"
            tmp = re.search(rep, conf).group()
            data['fix'] = re.search(
                "\(.+\)\$", tmp).group().replace('(', '').replace(')$', '').replace('|', ',')
            data['domains'] = ','.join(re.search(
                "valid_referers\s+none\s+blocked\s+(.+);\n", tmp).groups()[0].split())
            data['status'] = True
        else:
            data['fix'] = 'jpg,jpeg,gif,png,js,css'
            domains = slemp.M('domain').where(
                'pid=?', (sid,)).field('name').select()
            tmp = []
            for domain in domains:
                tmp.append(domain['name'])
            data['domains'] = ','.join(tmp)
            data['status'] = False
        return slemp.getJson(data)

    def setSecurity(self, sid, name, fix, domains, status):
        if len(fix) < 2:
            return slemp.returnJson(False, 'URL suffix cannot be empty!')
        file = self.getHostConf(name)
        if os.path.exists(file):
            conf = slemp.readFile(file)
            if conf.find('SECURITY-START') != -1:
                rep = "\s{0,4}#SECURITY-START(\n|.){1,500}#SECURITY-END\n?"
                conf = re.sub(rep, '', conf)
                slemp.writeLog('Website management', 'Site [' + name + '] anti-leech settings have been turned off!')
            else:
                rconf = '''#SECURITY-START Anti-leech configuration
location ~ .*\.(%s)$
{
    expires      30d;
    access_log /dev/null;
    valid_referers none blocked %s;
    if ($invalid_referer){
       return 404;
    }
}
# SECURITY-END
include enable-php-''' % (fix.strip().replace(',', '|'), domains.strip().replace(',', ' '))
                conf = re.sub("include\s+enable-php-", rconf, conf)
                slemp.writeLog('Website management', 'Site [' + name + '] has anti-leech!')
            slemp.writeFile(file, conf)
        slemp.restartWeb()
        return slemp.returnJson(True, 'Set up successfully!')

    def getPhpVersion(self):
        phpVersions = ('00', '52', '53', '54', '55',
                       '56', '70', '71', '72', '73', '74', '80', '81')
        data = []
        for val in phpVersions:
            tmp = {}
            if val == '00':
                tmp['version'] = '00'
                tmp['name'] = 'pure-static'
                data.append(tmp)

            checkPath = slemp.getServerDir() + '/php/' + val + '/bin/php'
            if os.path.exists(checkPath):
                tmp['version'] = val
                tmp['name'] = 'PHP-' + val
                data.append(tmp)

        return slemp.getJson(data)

    # Whether to jump to https
    def isToHttps(self, siteName):
        file = self.getHostConf(siteName)
        conf = slemp.readFile(file)
        if conf:
            if conf.find('HTTP_TO_HTTPS_START') != -1:
                return True
            if conf.find('$server_port !~ 443') != -1:
                return True
        return False

    def getRewriteList(self):
        rewriteList = {}
        rewriteList['rewrite'] = []
        rewriteList['rewrite'].append('current')
        for ds in os.listdir('rewrite/nginx'):
            rewriteList['rewrite'].append(ds[0:len(ds) - 5])
        rewriteList['rewrite'] = sorted(rewriteList['rewrite'])
        return rewriteList

    def createRootDir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
            if not slemp.isAppleSystem():
                slemp.execShell('chown -R www:www ' + path)
            slemp.execShell('chmod -R 755 ' + path)

    def nginxAddDomain(self, webname, domain, port):
        file = self.getHostConf(webname)
        conf = slemp.readFile(file)
        if not conf:
            return

        # Add domain name
        rep = "server_name\s*(.*);"
        tmp = re.search(rep, conf).group()
        domains = tmp.split(' ')
        if not slemp.inArray(domains, domain):
            newServerName = tmp.replace(';', ' ' + domain + ';')
            conf = conf.replace(tmp, newServerName)

        # add port
        rep = "listen\s+([0-9]+)\s*[default_server]*\s*;"
        tmp = re.findall(rep, conf)
        if not slemp.inArray(tmp, port):
            listen = re.search(rep, conf).group()
            conf = conf.replace(
                listen, listen + "\n\tlisten " + port + ';')
        # save configuration file
        slemp.writeFile(file, conf)
        return True

    def nginxAddConf(self):
        source_tpl = slemp.getRunDir() + '/data/tpl/nginx.conf'
        vhost_file = self.vhostPath + '/' + self.siteName + '.conf'
        content = slemp.readFile(source_tpl)

        content = content.replace('{$PORT}', self.sitePort)
        content = content.replace('{$SERVER_NAME}', self.siteName)
        content = content.replace('{$ROOT_DIR}', self.sitePath)
        content = content.replace('{$PHPVER}', self.phpVersion)
        content = content.replace('{$OR_REWRITE}', self.rewritePath)

        logsPath = slemp.getLogsDir()
        content = content.replace('{$LOGPATH}', logsPath)
        slemp.writeFile(vhost_file, content)

        rewrite_content = '''
location /{
    if (!-e $request_filename) {
       rewrite  ^(.*)$  /index.php/$1  last;
       break;
    }
}
        '''
        rewrite_file = self.rewritePath + '/' + self.siteName + '.conf'
        slemp.writeFile(rewrite_file, rewrite_content)

    def add(self, webname, port, ps, path, version):

        siteMenu = json.loads(webname)
        self.siteName = self.toPunycode(
            siteMenu['domain'].strip().split(':')[0]).strip()
        self.sitePath = self.toPunycodePath(
            self.getPath(path.replace(' ', '')))
        self.sitePort = port.strip().replace(' ', '')
        self.phpVersion = version

        if slemp.M('sites').where("name=?", (self.siteName,)).count():
            return slemp.returnJson(False, 'The site you added already exists!')

        # write to database
        pid = slemp.M('sites').add('name,path,status,ps,edate,addtime,type_id',
                                (self.siteName, self.sitePath, '1', ps, '0000-00-00', slemp.getDate(), 0,))
        opid = slemp.M('domain').where(
            "name=?", (self.siteName,)).getField('pid')
        if opid:
            if slemp.M('sites').where('id=?', (opid,)).count():
                return slemp.returnJson(False, 'The domain name you added already exists!')
            slemp.M('domain').where('pid=?', (opid,)).delete()

        # Add more domains
        for domain in siteMenu['domainlist']:
            sdomain = domain
            swebname = self.siteName
            spid = str(pid)
            # self.addDomain(domain, webname, pid)

        slemp.M('domain').add('pid,name,port,addtime',
                           (pid, self.siteName, self.sitePort, slemp.getDate()))

        self.createRootDir(self.sitePath)
        self.nginxAddConf()

        data = {}
        data['siteStatus'] = False
        slemp.restartWeb()
        return slemp.returnJson(True, 'Added successfully')

    def deleteWSLogs(self, webname):
        assLogPath = slemp.getLogsDir() + '/' + webname + '.log'
        errLogPath = slemp.getLogsDir() + '/' + webname + '.error.log'
        confFile = self.setupPath + '/nginx/vhost/' + webname + '.conf'
        rewriteFile = self.setupPath + '/nginx/rewrite/' + webname + '.conf'
        rewriteFile = self.setupPath + '/nginx/pass/' + webname + '.conf'
        keyPath = self.sslDir + webname + '/privkey.pem'
        certPath = self.sslDir + webname + '/fullchain.pem'
        logs = [assLogPath,
                errLogPath,
                confFile,
                rewriteFile,
                keyPath,
                certPath]
        for i in logs:
            slemp.deleteFile(i)

    def delete(self, sid, webname, path):
        self.deleteWSLogs(webname)
        if path == '1':
            rootPath = slemp.getWwwDir() + '/' + webname
            slemp.execShell('rm -rf ' + rootPath)

        slemp.M('sites').where("id=?", (sid,)).delete()
        slemp.restartWeb()
        return slemp.returnJson(True, 'Site deleted successfully!')

    def setEndDate(self, sid, edate):
        result = slemp.M('sites').where(
            'id=?', (sid,)).setField('edate', edate)
        siteName = slemp.M('sites').where('id=?', (sid,)).getField('name')
        slemp.writeLog('TYPE_SITE', 'After the setting is successful, the site will automatically stop after it expires!', (siteName, edate))
        return slemp.returnJson(True, 'After the setting is successful, the site will automatically stop after it expires!')

    # ssl related methods start
    def setSslConf(self, siteName):
        file = self.getHostConf(siteName)
        conf = slemp.readFile(file)

        keyPath = self.sslDir + siteName + '/privkey.pem'
        certPath = self.sslDir + siteName + '/fullchain.pem'
        if conf:
            if conf.find('ssl_certificate') == -1:
                sslStr = """#error_page 404/404.html;
    ssl_certificate    %s;
    ssl_certificate_key  %s;
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:HIGH:!aNULL:!MD5:!RC4:!DHE;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    error_page 497  https://$host$request_uri;
""" % (certPath, keyPath)
            if(conf.find('ssl_certificate') != -1):
                return slemp.returnData(True, 'SSL enabled successfully!')

            conf = conf.replace('#error_page 404/404.html;', sslStr)

            rep = "listen\s+([0-9]+)\s*[default_server]*;"
            tmp = re.findall(rep, conf)
            if not slemp.inArray(tmp, '443'):
                listen = re.search(rep, conf).group()
                conf = conf.replace(
                    listen, listen + "\n\tlisten 443 ssl http2;")
            shutil.copyfile(file, '/tmp/backup.conf')

            slemp.writeFile(file, conf)
            isError = slemp.checkWebConfig()
            if(isError != True):
                shutil.copyfile('/tmp/backup.conf', file)
                return slemp.returnData(False, 'Certificate error: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

        slemp.restartWeb()
        self.saveCert(keyPath, certPath)

        msg = slemp.getInfo('Website [{1}] successfully enabled SSL!', siteName)
        slemp.writeLog('Website management', msg)
        return slemp.returnData(True, 'SSL enabled successfully!')

    def saveCert(self, keyPath, certPath):
        try:
            certInfo = self.getCertName(certPath)
            if not certInfo:
                return slemp.returnData(False, 'Certificate parsing failed!')
            vpath = self.sslDir + certInfo['subject']
            if not os.path.exists(vpath):
                os.system('mkdir -p ' + vpath)
            slemp.writeFile(vpath + '/privkey.pem',
                         slemp.readFile(keyPath))
            slemp.writeFile(vpath + '/fullchain.pem',
                         slemp.readFile(certPath))
            slemp.writeFile(vpath + '/info.json', json.dumps(certInfo))
            return slemp.returnData(True, 'Certificate saved successfully!')
        except Exception as e:
            return slemp.returnData(False, 'Certificate save failed!')

    # get certificate name
    def getCertName(self, certPath):
        try:
            openssl = '/usr/local/openssl/bin/openssl'
            if not os.path.exists(openssl):
                openssl = 'openssl'
            result = slemp.execShell(
                openssl + " x509 -in " + certPath + " -noout -subject -enddate -startdate -issuer")
            tmp = result[0].split("\n")
            data = {}
            data['subject'] = tmp[0].split('=')[-1]
            data['notAfter'] = self.strfToTime(tmp[1].split('=')[1])
            data['notBefore'] = self.strfToTime(tmp[2].split('=')[1])
            data['issuer'] = tmp[3].split('O=')[-1].split(',')[0]
            if data['issuer'].find('/') != -1:
                data['issuer'] = data['issuer'].split('/')[0]
            result = slemp.execShell(
                openssl + " x509 -in " + certPath + " -noout -text|grep DNS")
            data['dns'] = result[0].replace(
                'DNS:', '').replace(' ', '').strip().split(',')
            return data
        except:
            return None

    # clear excess .user.ini
    def delUserInI(self, path, up=0):
        for p1 in os.listdir(path):
            try:
                npath = path + '/' + p1
                if os.path.isdir(npath):
                    if up < 100:
                        self.delUserInI(npath, up + 1)
                else:
                    continue
                useriniPath = npath + '/.user.ini'
                if not os.path.exists(useriniPath):
                    continue
                slemp.execShell('which chattr && chattr -i ' + useriniPath)
                slemp.execShell('rm -f ' + useriniPath)
            except:
                continue
        return True

    # Set up directory defense
    def setDirUserINI(self, newPath):
        filename = newPath + '/.user.ini'
        if os.path.exists(filename):
            slemp.execShell("chattr -i " + filename)
            os.remove(filename)
            return slemp.returnJson(True, 'Anti-cross-site settings cleared!')

        self.delUserInI(newPath)
        slemp.writeFile(filename, 'open_basedir=' +
                     newPath + '/:/tmp/:/proc/')
        slemp.execShell("chattr +i " + filename)

        return slemp.returnJson(True, 'Anti-cross-site settings turned on!')

    # Conversion time
    def strfToTime(self, sdate):
        import time
        return time.strftime('%Y-%m-%d', time.strptime(sdate, '%b %d %H:%M:%S %Y %Z'))
    # ssl related methods end
