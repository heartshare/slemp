# coding: utf-8

import psutil
import time
import os
import sys
import slemp
import re
import json
import pwd


from flask import request


class task_api:

    def __init__(self):
        pass

    def countApi(self):
        c = slemp.M('tasks').where("status!=?", ('1',)).count()
        return str(c)

    def listApi(self):

        p = request.form.get('p', '1').encode('utf-8')
        limit = request.form.get('limit', '10').strip()
        search = request.form.get('search', '').strip()

        start = (int(p) - 1) * int(limit)
        limit_str = str(start) + ',' + str(limit)

        _list = slemp.M('tasks').where('', ()).field(
            'id,name,type,status,addtime,start,end').limit(limit_str).order('id desc').select()
        _ret = {}
        _ret['data'] = _list

        count = slemp.M('tasks').where('', ()).count()
        _page = {}
        _page['count'] = count
        _page['tojs'] = 'remind'
        _page['p'] = p

        _ret['page'] = slemp.getPage(_page)
        return slemp.getJson(_ret)

    def getExecLogApi(self):
        file = os.getcwd() + "/tmp/panelExec.log"
        v = slemp.getLastLine(file, 100)
        return v

    def getTaskSpeedApi(self):
        tempFile = os.getcwd() + '/tmp/panelExec.log'
        freshFile = os.getcwd() + '/tmp/panelFresh'

        find = slemp.M('tasks').where('status=? OR status=?',
                                   ('-1', '0')).field('id,type,name,execstr').find()
        if not len(find):
            return slemp.returnJson(False, 'No task queue is currently executing -2!')

        isTask = os.getcwd() + '/tmp/panelTask.pl'
        slemp.writeFile(isTask, 'True')

        echoMsg = {}
        echoMsg['name'] = find['name']
        echoMsg['execstr'] = find['execstr']
        if find['type'] == 'download':
            import json
            try:
                tmp = slemp.readFile(tempFile)
                if len(tmp) < 10:
                    return slemp.returnJson(False, 'No task queue is currently executing -3!')
                echoMsg['msg'] = json.loads(tmp)
                echoMsg['isDownload'] = True
            except:
                slemp.M('tasks').where(
                    "id=?", (find['id'],)).save('status', ('0',))
                return slemp.returnJson(False, 'No task queue is currently executing -4!')
        else:
            echoMsg['msg'] = slemp.getLastLine(tempFile, 10)
            echoMsg['isDownload'] = False

        echoMsg['task'] = slemp.M('tasks').where("status!=?", ('1',)).field(
            'id,status,name,type').order("id asc").select()
        return slemp.getJson(echoMsg)
