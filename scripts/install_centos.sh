#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
LANG=en_US.UTF-8

mkdir -p /home/slemp/server
mkdir -p /home/slemp/wwwroot
mkdir -p /home/slemp/wwwlogs
mkdir -p /home/slemp/backup/database
mkdir -p /home/slemp/backup/site


if [ ! -f /usr/bin/applydeltarpm ];then
	yum -y provides '*/applydeltarpm'
	yum -y install deltarpm
fi


setenforce 0
sed -i 's#SELINUX=enforcing#SELINUX=disabled#g' /etc/selinux/config

yum install -y wget curl vixie-cron lsof
#https need

if [ ! -f /root/.acme.sh ];then
	curl  https://get.acme.sh | sh
fi

if [ -f "/etc/init.d/iptables" ];then

	iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j ACCEPT
	iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 80 -j ACCEPT
	iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 443 -j ACCEPT
	iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 888 -j ACCEPT
	iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 7200 -j ACCEPT
	iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 3306 -j ACCEPT
	iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 30000:40000 -j ACCEPT
	service iptables save

	iptables_status=`service iptables status | grep 'not running'`
	if [ "${iptables_status}" == '' ];then
		service iptables restart
	fi
fi

#Does not turn on during installation
service iptables stop

if [ "${isVersion}" == '' ];then
	if [ ! -f "/etc/init.d/iptables" ];then
		yum install firewalld -y
		systemctl enable firewalld
		systemctl start firewalld

		firewall-cmd --permanent --zone=public --add-port=22/tcp
		firewall-cmd --permanent --zone=public --add-port=80/tcp
		firewall-cmd --permanent --zone=public --add-port=443/tcp
		firewall-cmd --permanent --zone=public --add-port=888/tcp
		firewall-cmd --permanent --zone=public --add-port=7200/tcp
		firewall-cmd --permanent --zone=public --add-port=3306/tcp
		firewall-cmd --permanent --zone=public --add-port=30000-40000/tcp
		firewall-cmd --reload
	fi
fi

#Does not turn on during installation
systemctl stop firewalld


yum install -y libevent libevent-devel mysql-devel libjpeg* libpng* gd* zip unzip libmcrypt libmcrypt-devel

if [ ! -d /home/slemp/server/panel ];then
	wget -O /tmp/master.zip https://codeload.github.com/basoro/slemp/zip/master
	cd /tmp && unzip /tmp/master.zip
	mv /tmp/slemp-master /home/slemp/server/panel
	rm -rf /tmp/master.zip
	rm -rf /tmp/slemp-master
fi

yum groupinstall -y "Development Tools"
paces="wget python-devel python-imaging libicu-devel zip unzip bzip2-devel gcc libxml2 libxml2-dev libxslt* libjpeg-devel libpng-devel libwebp libwebp-devel lsof pcre pcre-devel vixie-cron crontabs"
yum -y install $paces
yum -y lsof net-tools.x86_64
yum -y install ncurses-devel mysql-dev locate cmake
yum -y install python-devel.x86_64
yum -y install MySQL-python
yum -y install epel-release

if [ ! -f '/usr/bin/pip' ];then
	wget https://bootstrap.pypa.io/pip/2.7/get-pip.py
	python get-pip.py
	pip install --upgrade pip
fi


cd /home/slemp/server/panel/scripts && ./lib.sh

pip install -I -r /home/slemp/server/panel/requirements.txt


cd /home/slemp/server/panel && ./cli.sh start
sleep 5

cd /home/slemp/server/panel && ./cli.sh stop
cd /home/slemp/server/panel && ./scripts/init.d/slemp default
cd /home/slemp/server/panel && ./cli.sh start
