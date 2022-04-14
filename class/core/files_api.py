# coding: utf-8

import psutil
import time
import os
import sys
import slemp
import re
import json
import pwd
import shutil

from flask import request
from flask import send_file, send_from_directory
from flask import make_response
from flask import session


class files_api:

    rPath = None

    def __init__(self):
        self.rPath = slemp.getRootDir() + '/recycle_bin/'

    ##### ----- start ----- ###
    def getBodyApi(self):
        path = request.form.get('path', '').encode('utf-8')
        return self.getBody(path)

    def getLastBodyApi(self):
        path = request.form.get('path', '').encode('utf-8')
        line = request.form.get('line', '100')

        if not os.path.exists(path):
            return slemp.returnJson(False, 'File does not exist', (path,))

        try:
            data = slemp.getNumLines(path, int(line))
            return slemp.returnJson(True, 'OK', data)
        except Exception as ex:
            return slemp.returnJson(False, u'Could not read the file correctly!' + str(ex))

    def saveBodyApi(self):
        path = request.form.get('path', '').encode('utf-8')
        data = request.form.get('data', '').encode('utf-8')
        encoding = request.form.get('encoding', '').encode('utf-8')
        return self.saveBody(path, data, encoding)

    def downloadApi(self):
        filename = request.args.get('filename', '').encode('utf-8')
        if not os.path.exists(filename):
            return ''
        response = make_response(send_from_directory(
            os.path.dirname(filename).encode('utf-8'), os.path.basename(filename).encode('utf-8'), as_attachment=True))
        return response

    def zipApi(self):
        sfile = request.form.get('sfile', '').encode('utf-8')
        dfile = request.form.get('dfile', '').encode('utf-8')
        stype = request.form.get('type', '').encode('utf-8')
        path = request.form.get('path', '').encode('utf-8')
        return self.zip(sfile, dfile, stype, path)

    def unzipApi(self):
        sfile = request.form.get('sfile', '').encode('utf-8')
        dfile = request.form.get('dfile', '').encode('utf-8')
        stype = request.form.get('type', '').encode('utf-8')
        coding = request.form.get('coding', '').encode('utf-8')
        password = request.form.get('password', '').encode('utf-8')
        return self.unzip(sfile, dfile, stype, coding, password)

    # Move a file or directory
    def mvFileApi(self):
        sfile = request.form.get('sfile', '').encode('utf-8')
        dfile = request.form.get('dfile', '').encode('utf-8')
        if not self.checkFileName(dfile):
            return slemp.returnJson(False, 'Filenames cannot contain special characters!')
        if not os.path.exists(sfile):
            return slemp.returnJson(False, 'The specified file does not exist!')

        if not self.checkDir(sfile):
            return slemp.returnJson(False, 'Sensitive directory, please don\'t play tricks!')

        import shutil
        try:
            shutil.move(sfile, dfile)
            msg = slemp.getInfo('Move file or directory [{1}] to [{2}] successful!', (sfile, dfile,))
            slemp.writeLog('File management', msg)
            return slemp.returnJson(True, 'Move file or directory succeeded!')
        except:
            return slemp.returnJson(False, 'Failed to move file or directory!')

    def deleteApi(self):
        path = request.form.get('path', '').encode('utf-8')
        return self.delete(path)

    def fileAccessApi(self):
        filename = request.form.get('filename', '').encode('utf-8')
        data = self.getAccess(filename)
        return slemp.getJson(data)

    def setFileAccessApi(self):

        if slemp.isAppleSystem():
            return slemp.returnJson(True, 'The development machine is not set!')

        filename = request.form.get('filename', '').encode('utf-8')
        user = request.form.get('user', '').encode('utf-8')
        access = request.form.get('access', '755')
        sall = '-R'
        try:
            if not self.checkDir(filename):
                return slemp.returnJson(False, 'Please don\'t play tricks')

            if not os.path.exists(filename):
                return slemp.returnJson(False, 'The specified file does not exist!')

            os.system('chmod ' + sall + ' ' + access + " '" + filename + "'")
            os.system('chown ' + sall + ' ' + user +
                      ':' + user + " '" + filename + "'")
            msg = slemp.getInfo(
                'Set [{1}] permission to [{2}] owner to [{3}]', (filename, access, user,))
            slemp.writeLog('File management', msg)
            return slemp.returnJson(True, 'Set successfully!')
        except:
            return slemp.returnJson(False, 'Setup failed!')

    def getDirSizeApi(self):
        path = request.form.get('path', '').encode('utf-8')
        tmp = self.getDirSize(path)
        return slemp.returnJson(True, tmp[0].split()[0])

    def getDirApi(self):
        path = request.form.get('path', '').encode('utf-8')
        if not os.path.exists(path):
            path = slemp.getRootDir() + "/wwwroot"
        search = request.args.get('search', '').strip().lower()
        page = request.args.get('p', '1').strip().lower()
        row = request.args.get('showRow', '10')
        disk = request.form.get('disk', '')
        if disk == 'True':
            row = 1000

        return self.getDir(path, int(page), int(row), search)

    def createFileApi(self):
        file = request.form.get('path', '').encode('utf-8')
        try:
            if not self.checkFileName(file):
                return slemp.returnJson(False, 'Filenames cannot contain special characters!')
            if os.path.exists(file):
                return slemp.returnJson(False, 'The specified file already exists!')
            _path = os.path.dirname(file)
            if not os.path.exists(_path):
                os.makedirs(_path)
            open(file, 'w+').close()
            self.setFileAccept(file)
            msg = slemp.getInfo('Creating file [{1}] succeeded!', (file,))
            slemp.writeLog('File management', msg)
            return slemp.returnJson(True, 'File created successfully!')
        except Exception as e:
            # print str(e)
            return slemp.returnJson(True, 'File creation failed!')

    def createDirApi(self):
        path = request.form.get('path', '').encode('utf-8')
        try:
            if not self.checkFileName(path):
                return slemp.returnJson(False, 'Directory names cannot contain special characters!')
            if os.path.exists(path):
                return slemp.returnJson(False, '指定目录已存在!')
            os.makedirs(path)
            self.setFileAccept(path)
            msg = slemp.getInfo('Create directory [{1}] successful!', (path,))
            slemp.writeLog('File management', msg)
            return slemp.returnJson(True, 'Directory created successfully!')
        except Exception as e:
            return slemp.returnJson(False, 'Directory creation failed!')

    def downloadFileApi(self):
        import db
        import time
        url = request.form.get('url', '').encode('utf-8')
        path = request.form.get('path', '').encode('utf-8')
        filename = request.form.get('filename', '').encode('utf-8')

        isTask = slemp.getRootDir() + '/tmp/panelTask.pl'
        execstr = url + '|slemp|' + path + '/' + filename
        slemp.M('tasks').add('name,type,status,addtime,execstr',
                          ('下载文件[' + filename + ']', 'download', '0', time.strftime('%Y-%m-%d %H:%M:%S'), execstr))
        slemp.writeFile(isTask, 'True')
        # self.setFileAccept(path + '/' + filename)
        return slemp.returnJson(True, 'Download task added to queue!')

    def removeTaskApi(self):
        mid = request.form.get('id', '').encode('utf-8')
        try:
            name = slemp.M('tasks').where('id=?', (mid,)).getField('name')
            status = slemp.M('tasks').where('id=?', (mid,)).getField('status')
            slemp.M('tasks').delete(mid)
            if status == '-1':
                os.system(
                    "kill `ps -ef |grep 'python panelSafe.pyc'|grep -v grep|grep -v panelExec|awk '{print $2}'`")
                os.system(
                    "kill `ps aux | grep 'python task.pyc$'|awk '{print $2}'`")
                os.system('''
pids=`ps aux | grep 'sh'|grep -v grep|grep install|awk '{print $2}'`
arr=($pids)

for p in ${arr[@]}
do
    kill -9 $p
done
            ''')

                os.system(
                    'rm -f ' + name.replace('scan directory [', '').replace(']', '') + '/scan.pl')
                isTask = slemp.getRootDir() + '/tmp/panelTask.pl'
                slemp.writeFile(isTask, 'True')
                os.system('/etc/init.d/slemp start')
        except:
            os.system('/etc/init.d/slemp start')
        return slemp.returnJson(True, 'Task deleted!')

    # upload files
    def uploadFileApi(self):
        from werkzeug.utils import secure_filename
        from flask import request

        path = request.args.get('path', '').encode('utf-8')

        if not os.path.exists(path):
            os.makedirs(path)
        f = request.files['zunfile']
        filename = os.path.join(path, f.filename)
        if sys.version_info[0] == 2:
            filename = filename.encode('utf-8')
        s_path = path
        if os.path.exists(filename):
            s_path = filename
        p_stat = os.stat(s_path)
        f.save(filename)
        os.chown(filename, p_stat.st_uid, p_stat.st_gid)
        os.chmod(filename, p_stat.st_mode)

        msg = slemp.getInfo('Uploading file [{1}] to [{2}] succeeded!', (filename, path))
        slemp.writeLog('File management', msg)
        return slemp.returnMsg(True, 'Uploaded successfully!')

    def getRecycleBinApi(self):
        rPath = self.rPath
        if not os.path.exists(rPath):
            os.system('mkdir -p ' + rPath)
        data = {}
        data['dirs'] = []
        data['files'] = []
        data['status'] = os.path.exists('data/recycle_bin.pl')
        data['status_db'] = os.path.exists('data/recycle_bin_db.pl')
        for file in os.listdir(rPath):
            try:
                tmp = {}
                fname = rPath + file
                tmp1 = file.split('_slemp_')
                tmp2 = tmp1[len(tmp1) - 1].split('_t_')
                tmp['rname'] = file
                tmp['dname'] = file.replace('_slemp_', '/').split('_t_')[0]
                tmp['name'] = tmp2[0]
                tmp['time'] = int(float(tmp2[1]))
                if os.path.islink(fname):
                    filePath = os.readlink(fname)
                    link = ' -> ' + filePath
                    if os.path.exists(filePath):
                        tmp['size'] = os.path.getsize(filePath)
                    else:
                        tmp['size'] = 0
                else:
                    tmp['size'] = os.path.getsize(fname)
                if os.path.isdir(fname):
                    data['dirs'].append(tmp)
                else:
                    data['files'].append(tmp)
            except:
                continue
        return slemp.returnJson(True, 'OK', data)

    # Recycle Bin Switch
    def recycleBinApi(self):
        c = 'data/recycle_bin.pl'
        db = request.form.get('db', '').encode('utf-8')
        if db != '':
            c = 'data/recycle_bin_db.pl'
        if os.path.exists(c):
            os.remove(c)
            slemp.writeLog('File management', 'Recycle bin is turned off!')
            return slemp.returnJson(True, 'Recycle Bin is turned off!')
        else:
            slemp.writeFile(c, 'True')
            slemp.writeLog('File management', 'Recycle bin is turned on!')
            return slemp.returnJson(True, 'Recycle bin is turned on!')

    def reRecycleBinApi(self):
        rPath = self.rPath
        path = request.form.get('path', '').encode('utf-8')
        dFile = path.replace('_slemp_', '/').split('_t_')[0]
        try:
            import shutil
            shutil.move(rPath + path, dFile)
            msg = slemp.getInfo('Move file [{1}] to recycle bin successful!', (dFile,))
            slemp.writeLog('File management', msg)
            return slemp.returnJson(True, 'Recovery was successful!')
        except Exception as e:
            msg = slemp.getInfo('Failed to restore [{1}] from Recycle Bin!', (dFile,))
            slemp.writeLog('File management', msg)
            return slemp.returnJson(False, 'Recovery failed!')

    def delRecycleBinApi(self):
        rPath = self.rPath
        path = request.form.get('path', '').encode('utf-8')
        empty = request.form.get('empty', '').encode('utf-8')
        dFile = path.split('_t_')[0]

        if not self.checkDir(path):
            return slemp.returnJson(False, 'Sensitive directory, Please don\'t play tricks!')

        os.system('which chattr && chattr -R -i ' + rPath + path)
        if os.path.isdir(rPath + path):
            import shutil
            shutil.rmtree(rPath + path)
        else:
            os.remove(rPath + path)

        tfile = path.replace('_slemp_', '/').split('_t_')[0]
        msg = slemp.getInfo('{1} has been completely removed from the trash!', (tfile,))
        slemp.writeLog('File management', msg)
        return slemp.returnJson(True, msg)

    # get progress
    def getSpeedApi(self):
        data = slemp.getSpeed()
        return slemp.returnJson(True, 'Recycle bin emptied!', data)

    def closeRecycleBinApi(self):
        rPath = self.rPath
        os.system('which chattr && chattr -R -i ' + rPath)
        rlist = os.listdir(rPath)
        i = 0
        l = len(rlist)
        for name in rlist:
            i += 1
            path = rPath + name
            slemp.writeSpeed(name, i, l)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        slemp.writeSpeed(None, 0, 0)
        slemp.writeLog('File management', 'Recycle bin emptied!')
        return slemp.returnJson(True, 'Recycle bin emptied!')

    def deleteDirApi(self):
        path = request.form.get('path', '').encode('utf-8')
        if not os.path.exists(path):
            return slemp.returnJson(False, 'The specified file does not exist!')

        # Check if .user.ini
        if path.find('.user.ini'):
            os.system("chattr -i '" + path + "'")
        try:
            if os.path.exists('data/recycle_bin.pl'):
                if self.mvRecycleBin(path):
                    return slemp.returnJson(True, 'Moved file to recycle bin!')
            slemp.execShell('rm -rf ' + path)
            slemp.writeLog('File management', 'Delete file successfully!', (path,))
            return slemp.returnJson(True, 'Delete file successfully!')
        except:
            return slemp.returnJson(False, 'Delete file failed!')

    def closeLogsApi(self):
        logPath = slemp.getLogsDir()
        os.system('rm -f ' + logPath + '/*')
        os.system('kill -USR1 `cat ' + slemp.getServerDir() +
                  'openresty/nginx/logs/nginx.pid`')
        slemp.writeLog('File management', 'The website log has been cleared!')
        tmp = self.getDirSize(logPath)
        return slemp.returnJson(True, tmp[0].split()[0])

    def setBatchDataApi(self):
        path = request.form.get('path', '').encode('utf-8')
        stype = request.form.get('type', '').encode('utf-8')
        access = request.form.get('access', '').encode('utf-8')
        user = request.form.get('user', '').encode('utf-8')
        data = request.form.get('data')
        if stype == '1' or stype == '2':
            session['selected'] = {
                'path': path,
                'type': stype,
                'access': access,
                'user': user,
                'data': data
            }
            return slemp.returnJson(True, 'The marking is successful, please click the Paste All button in the target directory!')
        elif stype == '3':
            for key in json.loads(data):
                try:
                    key = key.encode('utf-8')
                    filename = path + '/' + key
                    if not self.checkDir(filename):
                        return slemp.returnJson(False, 'FILE_DANGER')
                    os.system('chmod -R ' + access + " '" + filename + "'")
                    os.system('chown -R ' + user + ':' +
                              user + " '" + filename + "'")
                except:
                    continue
            slemp.writeLog('File management', 'Batch setting permissions succeeded!')
            return slemp.returnJson(True, 'Batch setting permissions succeeded!')
        else:
            import shutil
            isRecyle = os.path.exists('data/recycle_bin.pl')
            data = json.loads(data)
            l = len(data)
            i = 0
            for key in data:
                try:
                    filename = path + '/' + key.encode('utf-8')
                    topath = filename
                    if not os.path.exists(filename):
                        continue

                    i += 1
                    slemp.writeSpeed(key, i, l)
                    if os.path.isdir(filename):
                        if not self.checkDir(filename):
                            return slemp.returnJson(False, 'Please don\'t play tricks!')
                        if isRecyle:
                            self.mvRecycleBin(topath)
                        else:
                            shutil.rmtree(filename)
                    else:
                        if key == '.user.ini':
                            os.system('which chattr && chattr -i ' + filename)
                        if isRecyle:
                            self.mvRecycleBin(topath)
                        else:
                            os.remove(filename)
                except:
                    continue
                slemp.writeSpeed(None, 0, 0)
            slemp.writeLog('File management', 'Batch delete successfully!')
            return slemp.returnJson(True, 'Batch delete successfully!')

    def checkExistsFilesApi(self):
        dfile = request.form.get('dfile', '').encode('utf-8')
        filename = request.form.get('filename', '').encode('utf-8')
        data = []
        filesx = []
        if filename == '':
            filesx = json.loads(session['selected']['data'])
        else:
            filesx.append(filename)

        print filesx

        for fn in filesx:
            if fn == '.':
                continue
            filename = dfile + '/' + fn
            if os.path.exists(filename):
                tmp = {}
                stat = os.stat(filename)
                tmp['filename'] = fn
                tmp['size'] = os.path.getsize(filename)
                tmp['mtime'] = str(int(stat.st_mtime))
                data.append(tmp)
        return slemp.returnJson(True, 'ok', data)

    def batchPasteApi(self):
        path = request.form.get('path', '').encode('utf-8')
        stype = request.form.get('type', '').encode('utf-8')
        # filename = request.form.get('filename', '').encode('utf-8')
        import shutil
        if not self.checkDir(path):
            return slemp.returnJson(False, 'Please don\'t play tricks!')
        i = 0
        myfiles = json.loads(session['selected']['data'])
        l = len(myfiles)
        if stype == '1':
            for key in myfiles:
                i += 1
                slemp.writeSpeed(key, i, l)
                try:

                    sfile = session['selected'][
                        'path'] + '/' + key.encode('utf-8')
                    dfile = path + '/' + key.encode('utf-8')

                    if os.path.isdir(sfile):
                        shutil.copytree(sfile, dfile)
                    else:
                        shutil.copyfile(sfile, dfile)
                    stat = os.stat(sfile)
                    os.chown(dfile, stat.st_uid, stat.st_gid)
                except:
                    continue
            msg = slemp.getInfo('Batch copy from [{1}] to [{2}] succeeded',
                             (session['selected']['path'], path,))
            slemp.writeLog('File management', msg)
        else:
            for key in myfiles:
                try:
                    i += 1
                    slemp.writeSpeed(key, i, l)

                    sfile = session['selected'][
                        'path'] + '/' + key.encode('utf-8')
                    dfile = path + '/' + key.encode('utf-8')

                    shutil.move(sfile, dfile)
                except:
                    continue
            msg = slemp.getInfo('Batch move from [{1}] to [{2}] succeeded',
                             (session['selected']['path'], path,))
            slemp.writeLog('File management', msg)
        slemp.writeSpeed(None, 0, 0)
        errorCount = len(myfiles) - i
        del(session['selected'])
        msg = slemp.getInfo('Batch operation succeeded [{1}], failed [{2}]', (str(i), str(errorCount)))
        return slemp.returnJson(True, msg)

    def copyFileApi(self):
        sfile = request.form.get('sfile', '').encode('utf-8')
        dfile = request.form.get('dfile', '').encode('utf-8')

        if not os.path.exists(sfile):
            return slemp.returnJson(False, 'The specified file does not exist!')

        if os.path.isdir(sfile):
            return self.copyDir(sfile, dfile)

        import shutil
        try:
            shutil.copyfile(sfile, dfile)
            msg = slemp.getInfo('Copying file [{1}] to [{2}] succeeded!', (sfile, dfile,))
            slemp.writeLog('File management', msg)
            stat = os.stat(sfile)
            os.chown(dfile, stat.st_uid, stat.st_gid)
            return slemp.returnJson(True, 'File copy successfully!')
        except:
            return slemp.returnJson(False, 'File copy failed!')

    ##### ----- end ----- ###

    def copyDir(self, sfile, dfile):

        if not os.path.exists(sfile):
            return slemp.returnJson(False, 'The specified directory does not exist!')

        if os.path.exists(dfile):
            return slemp.returnJson(False, 'The specified directory already exists!')
        import shutil
        try:
            shutil.copytree(sfile, dfile)
            stat = os.stat(sfile)
            os.chown(dfile, stat.st_uid, stat.st_gid)
            msg = slemp.getInfo('Copy directory [{1}] to [{2}] successful!', (sfile, dfile))
            slemp.writeLog('File management', msg)
            return slemp.returnJson(True, 'Directory copy successfully!')
        except:
            return slemp.returnJson(False, 'Directory copy failed!')

    # Check for sensitive directories
    def checkDir(self, path):
        path = path.replace('//', '/')
        if path[-1:] == '/':
            path = path[:-1]

        nDirs = ('',
                 '/',
                 '/*',
                 '/www',
                 '/root',
                 '/boot',
                 '/bin',
                 '/etc',
                 '/home',
                 '/dev',
                 '/sbin',
                 '/var',
                 '/usr',
                 '/tmp',
                 '/sys',
                 '/proc',
                 '/media',
                 '/mnt',
                 '/opt',
                 '/lib',
                 '/srv',
                 '/selinux',
                 '/home/slemp/server',
                 '/home/slemp/server/data',
                 slemp.getRootDir())

        return not path in nDirs

    def getDirSize(self, path):
        if slemp.getOs() == 'darwin':
            tmp = slemp.execShell('du -sh ' + path)
        else:
            tmp = slemp.execShell('du -sbh ' + path)
        return tmp

    def checkFileName(self, filename):
        # Check filename
        nots = ['\\', '&', '*', '|', ';']
        if filename.find('/') != -1:
            filename = filename.split('/')[-1]
        for n in nots:
            if n in filename:
                return False
        return True

    def setFileAccept(self, filename):
        auth = 'www:www'
        if slemp.getOs() == 'darwin':
            user = slemp.execShell(
                "who | sed -n '2, 1p' |awk '{print $1}'")[0].strip()
            auth = user + ':staff'
        os.system('chown -R ' + auth + ' ' + filename)
        os.system('chmod -R 755 ' + filename)

    # move to recycle bin
    def mvRecycleBin(self, path):
        rPath = self.rPath
        if not os.path.exists(rPath):
            os.system('mkdir -p ' + rPath)

        rFile = rPath + path.replace('/', '_slemp_') + '_t_' + str(time.time())
        try:
            import shutil
            shutil.move(path, rFile)
            slemp.writeLog('File management', slemp.getInfo(
                'Move file [{1}] to recycle bin successful!', (path)))
            return True
        except:
            slemp.writeLog('File management', slemp.getInfo(
                'Failed to move file [{1}] to recycle bin!', (path)))
            return False

    def getBody(self, path):
        if not os.path.exists(path):
            return slemp.returnJson(False, 'File does not exist', (path,))

        if os.path.getsize(path) > 2097152:
            return slemp.returnJson(False, u'Files larger than 2MB cannot be edited online!')

        fp = open(path, 'rb')
        data = {}
        data['status'] = True
        try:
            if fp:
                from chardet.universaldetector import UniversalDetector
                detector = UniversalDetector()
                srcBody = b""
                for line in fp.readlines():
                    detector.feed(line)
                    srcBody += line
                detector.close()
                char = detector.result
                data['encoding'] = char['encoding']
                if char['encoding'] == 'GB2312' or not char['encoding'] or char[
                        'encoding'] == 'TIS-620' or char['encoding'] == 'ISO-8859-9':
                    data['encoding'] = 'GBK'
                if char['encoding'] == 'ascii' or char[
                        'encoding'] == 'ISO-8859-1':
                    data['encoding'] = 'utf-8'
                if char['encoding'] == 'Big5':
                    data['encoding'] = 'BIG5'
                if not char['encoding'] in ['GBK', 'utf-8',
                                            'BIG5']:
                    data['encoding'] = 'utf-8'
                try:
                    if sys.version_info[0] == 2:
                        data['data'] = srcBody.decode(
                            data['encoding']).encode('utf-8', errors='ignore')
                    else:
                        data['data'] = srcBody.decode(data['encoding'])
                except:
                    data['encoding'] = char['encoding']
                    if sys.version_info[0] == 2:
                        data['data'] = srcBody.decode(
                            data['encoding']).encode('utf-8', errors='ignore')
                    else:
                        data['data'] = srcBody.decode(data['encoding'])
            else:
                if sys.version_info[0] == 2:
                    data['data'] = srcBody.decode('utf-8').encode('utf-8')
                else:
                    data['data'] = srcBody.decode('utf-8')
                data['encoding'] = u'utf-8'

            return slemp.returnJson(True, 'OK', data)
        except Exception as ex:
            return slemp.returnJson(False, u'The file encoding is not compatible, the file cannot be read correctly!' + str(ex))

    def saveBody(self, path, data, encoding='utf-8'):
        if not os.path.exists(path):
            return slemp.returnJson(False, 'File does not exist')
        try:
            if encoding == 'ascii':
                encoding = 'utf-8'
            if sys.version_info[0] == 2:
                data = data.encode(encoding, errors='ignore')
                fp = open(path, 'w+')
            else:
                data = data.encode(
                    encoding, errors='ignore').decode(encoding)
                fp = open(path, 'w+', encoding=encoding)
            fp.write(data)
            fp.close()

            slemp.writeLog('File management', 'File saved successfully', (path,))
            return slemp.returnJson(True, 'File saved successfully')
        except Exception as ex:
            return slemp.returnJson(False, 'Save ERROR:' + str(ex))

    def zip(self, sfile, dfile, stype, path):
        if sfile.find(',') == -1:
            if not os.path.exists(path + '/' + sfile):
                return slemp.returnMsg(False, 'The specified file does not exist!')

        try:
            tmps = slemp.getRunDir() + '/tmp/panelExec.log'
            if stype == 'zip':
                os.system("cd '" + path + "' && zip '" + dfile +
                          "' -r '" + sfile + "' > " + tmps + " 2>&1")
            else:
                sfiles = ''
                for sfile in sfile.split(','):
                    if not sfile:
                        continue
                    sfiles += " '" + sfile + "'"
                os.system("cd '" + path + "' && tar -zcvf '" +
                          dfile + "' " + sfiles + " > " + tmps + " 2>&1")
            self.setFileAccept(dfile)
            slemp.writeLog("File management", 'File compression succeeded!', (sfile, dfile))
            return slemp.returnJson(True, 'File compression succeeded!')
        except:
            return slemp.returnJson(False, 'File compression failed!')

    def unzip(self, sfile, dfile, stype, coding, password):
        if sfile.find(',') == -1:
            if not os.path.exists(sfile):
                return slemp.returnMsg(False, 'The specified file or directory does not exist!')

        tmps = slemp.getRunDir() + '/tmp/panelExec.log'
        if stype == 'zip':
            os.system("unzip -o '" + sfile +
                      "' -d '" + dfile + "' > " + tmps + " 2>&1")
        else:
            os.system("tar zxf '" +
                      sfile + "' -C '" + dfile + " > " + tmps + " 2>&1")
        self.setFileAccept(dfile)
        slemp.writeLog('File management', 'File decompression succeeded!', (sfile, dfile))
        return slemp.returnMsg(True, 'File decompression succeeded!')

    def delete(self, path):

        if not os.path.exists(path):
            return slemp.returnJson(False, 'The specified file does not exist!')

        # Check if .user.ini
        if path.find('.user.ini') >= 0:
            os.system("chattr -i '" + path + "'")

        try:
            if os.path.exists('data/recycle_bin.pl'):
                if self.mvRecycleBin(path):
                    return slemp.returnJson(True, 'Moved file to recycle bin!')
            os.remove(path)
            slemp.writeLog('File management', slemp.getInfo(
                'Delete file [{1}] succeeded!', (path)))
            return slemp.returnJson(True, 'Delete file successfully!')
        except:
            return slemp.returnJson(False, 'Delete file failed!')

    def getAccess(self, filename):
        data = {}
        try:
            stat = os.stat(filename)
            data['chmod'] = str(oct(stat.st_mode)[-3:])
            data['chown'] = pwd.getpwuid(stat.st_uid).pw_name
        except:
            data['chmod'] = 755
            data['chown'] = 'www'
        return data

        # Calculate the number of files
    def getCount(self, path, search):
        i = 0
        for name in os.listdir(path):
            if search:
                if name.lower().find(search) == -1:
                    continue
            # if name[0:1] == '.':
            #     continue
            i += 1
        return i

    def getDir(self, path, page=1, page_size=10, search=None):
        data = {}
        dirnames = []
        filenames = []

        info = {}
        info['count'] = self.getCount(path, search)
        info['row'] = page_size
        info['p'] = page
        info['tojs'] = 'getFiles'
        pageObj = slemp.getPageObject(info, '1,2,3,4,5,6,7,8')
        data['PAGE'] = pageObj[0]

        i = 0
        n = 0
        for filename in os.listdir(path):
            if search:
                if filename.lower().find(search) == -1:
                    continue
            i += 1
            if n >= pageObj[1].ROW:
                break
            if i < pageObj[1].SHIFT:
                continue

            try:
                filePath = (path + '/' + filename).encode('utf8')
                link = ''
                if os.path.islink(filePath):
                    filePath = os.readlink(filePath)
                    link = ' -> ' + filePath
                    if not os.path.exists(filePath):
                        filePath = path + '/' + filePath
                    if not os.path.exists(filePath):
                        continue

                stat = os.stat(filePath)
                accept = str(oct(stat.st_mode)[-3:])
                mtime = str(int(stat.st_mtime))
                user = ''
                try:
                    user = pwd.getpwuid(stat.st_uid).pw_name
                except:
                    user = str(stat.st_uid)
                size = str(stat.st_size)
                if os.path.isdir(filePath):
                    dirnames.append(filename + ';' + size + ';' +
                                    mtime + ';' + accept + ';' + user + ';' + link)
                else:
                    filenames.append(filename + ';' + size + ';' +
                                     mtime + ';' + accept + ';' + user + ';' + link)
                n += 1
            except:
                continue

        data['DIR'] = sorted(dirnames)
        data['FILES'] = sorted(filenames)
        data['PATH'] = path.replace('//', '/')
        return slemp.getJson(data)
