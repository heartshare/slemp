#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
LANG=en_US.UTF-8


if [ -f /etc/motd ];then
    echo "Welcome to panel panel" > /etc/motd
fi

sed -i 's#SELINUX=enforcing#SELINUX=disabled#g' /etc/selinux/config

wget -O /tmp/master.zip https://codeload.github.com/basoro/slemp/zip/master
cd /tmp && unzip /tmp/master.zip
/usr/bin/cp -rf  /tmp/slemp-master/* /home/slemp/server/panel
rm -rf /tmp/master.zip
rm -rf /tmp/slemp-master


#yum install -y curl-devel libmcrypt libmcrypt-devel

#cd /home/slemp/server/panel/scripts && sh lib.sh
#pip install -r /home/slemp/server/panel/requirements.txt


sh /etc/init.d/slemp stop && rm -rf  /home/slemp/server/panel/scripts/init.d/slemp && rm -rf  /etc/init.d/slemp

echo -e "stop slemp"
isStart=`ps -ef|grep 'gunicorn -c setting.py app:app' |grep -v grep|awk '{print $2}'`
port=$(cat /home/slemp/server/panel/data/port.pl)
n=0
while [[ "$isStart" != "" ]];
do
    echo -e ".\c"
    sleep 0.5
    isStart=$(lsof -n -P -i:$port|grep LISTEN|grep -v grep|awk '{print $2}'|xargs)
    let n+=1
    if [ $n -gt 15 ];then
        break;
    fi
done


echo -e "start slemp"
cd /home/slemp/server/panel && sh cli.sh start
isStart=`ps -ef|grep 'gunicorn -c setting.py app:app' |grep -v grep|awk '{print $2}'`
n=0
while [[ ! -f /etc/init.d/slemp ]];
do
    echo -e ".\c"
    sleep 0.5
    let n+=1
    if [ $n -gt 15 ];then
        break;
    fi
done
echo -e "start slemp success"

/etc/init.d/slemp default
