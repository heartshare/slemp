# coding: utf-8

import sys
import os
import json
import time
# print sys.path

sys.path.append("/usr/local/lib/python2.7/site-packages")
import psutil

sys.path.append(os.getcwd() + "/class/core")
reload(sys)
sys.setdefaultencoding('utf-8')
import db
import slemp


def set_mysql_root(password):
    # Set MySQL password
    import db
    import os
    sql = db.Sql()

    root_mysql = '''#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
pwd=$1
${server}/init.d/mysql stop
${server}/bin/mysqld_safe --skip-grant-tables&
echo 'Mengubah kata sandi...';
sleep 6
m_version=$(cat ${server}/version.pl|grep -E "(5.1.|5.5.|5.6.|mariadb)")
if [ "$m_version" != "" ];then
    ${server}/bin/mysql -uroot -e "insert into mysql.user(Select_priv,Insert_priv,Update_priv,Delete_priv,Create_priv,Drop_priv,Reload_priv,Shutdown_priv,Process_priv,File_priv,Grant_priv,References_priv,Index_priv,Alter_priv,Show_db_priv,Super_priv,Create_tmp_table_priv,Lock_tables_priv,Execute_priv,Repl_slave_priv,Repl_client_priv,Create_view_priv,Show_view_priv,Create_routine_priv,Alter_routine_priv,Create_user_priv,Event_priv,Trigger_priv,Create_tablespace_priv,User,Password,host)values('Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','root',password('${pwd}'),'127.0.0.1')"
    ${server}/bin/mysql -uroot -e "insert into mysql.user(Select_priv,Insert_priv,Update_priv,Delete_priv,Create_priv,Drop_priv,Reload_priv,Shutdown_priv,Process_priv,File_priv,Grant_priv,References_priv,Index_priv,Alter_priv,Show_db_priv,Super_priv,Create_tmp_table_priv,Lock_tables_priv,Execute_priv,Repl_slave_priv,Repl_client_priv,Create_view_priv,Show_view_priv,Create_routine_priv,Alter_routine_priv,Create_user_priv,Event_priv,Trigger_priv,Create_tablespace_priv,User,Password,host)values('Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','root',password('${pwd}'),'localhost')"
    ${server}/bin/mysql -uroot -e "UPDATE mysql.user SET password=PASSWORD('${pwd}') WHERE user='root'";
else
    ${server}/bin/mysql -uroot -e "UPDATE mysql.user SET authentication_string='' WHERE user='root'";
    ${server}/bin/mysql -uroot -e "FLUSH PRIVILEGES";
    ${server}/bin/mysql -uroot -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '${pwd}';";
fi
${server} -uroot -e "FLUSH PRIVILEGES";
pkill -9 mysqld_safe
pkill -9 mysqld
sleep 2
${server}/init.d/mysql start

echo '==========================================='
echo "Kata sandi root berhasil diubah menjadi: ${pwd}"
echo "The root password set ${pwd}  successuful"'''

    server = slemp.getServerDir() + '/mysql'
    root_mysql = root_mysql.replace('${server}', server)
    slemp.writeFile('mysql_root.sh', root_mysql)
    os.system("/bin/bash mysql_root.sh " + password)
    os.system("rm -f mysql_root.sh")

    pos = slemp.getServerDir() + '/mysql'
    result = sql.table('config').dbPos(pos, 'mysql').where(
        'id=?', (1,)).setField('mysql_root', password)


def set_panel_pwd(password, ncli=False):
    # Set panel password
    import db
    sql = db.Sql()
    result = sql.table('users').where('id=?', (1,)).setField(
        'password', slemp.md5(password))
    username = sql.table('users').where('id=?', (1,)).getField('username')
    if ncli:
        print("|-Username: " + username)
        print("|-Password: " + password)
    else:
        print(username)


def set_panel_username(username=None):
    # random panel username
    import db
    sql = db.Sql()
    if username:
        if len(username) < 5:
            print("|-Error, username cannot be less than 5 characters long")
            return
        if username in ['admin', 'root']:
            print("|-Error, too simple username cannot be used")
            return

        sql.table('users').where('id=?', (1,)).setField('username', username)
        print("|-New username: %s" % username)
        return

    username = sql.table('users').where('id=?', (1,)).getField('username')
    if username == 'admin':
        username = slemp.getRandomString(8).lower()
        sql.table('users').where('id=?', (1,)).setField('username', username)
    print('username: ' + username)


if __name__ == "__main__":
    type = sys.argv[1]
    if type == 'root':
        set_mysql_root(sys.argv[2])
    elif type == 'panel':
        set_panel_pwd(sys.argv[2])
    elif type == 'username':
        set_panel_username()
    else:
        print('ERROR: Parameter error')
