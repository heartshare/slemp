# -*- coding: utf-8 -*-
#!/bin/bash

PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

#https://dev.mysql.com/downloads/mysql/5.7.html
#https://dev.mysql.com/downloads/file/?id=489855

curPath=`pwd`
rootPath=$(dirname "$curPath")
rootPath=$(dirname "$rootPath")
serverPath=$(dirname "$rootPath")
sysName=`uname`


install_tmp=${rootPath}/tmp/slemp_install.pl
mysqlDir=${serverPath}/source/mysql

Install_mysql()
{
	mkdir -p ${mysqlDir}
	echo 'Installing script file...' > $install_tmp

	if [ "$sysName" != "Darwin" ];then
		mkdir -p /var/log/mariadb
		touch /var/log/mariadb/mariadb.log
		groupadd mysql
		useradd -g mysql mysql
		chown -R mysql:mysql /var/log/mariadb/*
	fi

	if [ ! -f ${mysqlDir}/mysql-boost-5.7.26.tar.gz ];then
		wget -O ${mysqlDir}/mysql-boost-5.7.26.tar.gz https://cdn.mysql.com/archives/mysql-5.7/mysql-boost-5.7.26.tar.gz
	fi

	if [ ! -d ${mysqlDir}/mysql-5.7.26 ];then
		 cd ${mysqlDir} && tar -zxvf  ${mysqlDir}/mysql-boost-5.7.26.tar.gz
	fi

	if [ ! -d $serverPath/mysql ];then
		cd ${mysqlDir}/mysql-5.7.26 && cmake \
		-DCMAKE_INSTALL_PREFIX=$serverPath/mysql \
		-DMYSQL_USER=mysql \
		-DMYSQL_TCP_PORT=3306 \
		-DMYSQL_UNIX_ADDR=/var/tmp/mysql.sock \
		-DWITH_MYISAM_STORAGE_ENGINE=1 \
		-DWITH_INNOBASE_STORAGE_ENGINE=1 \
		-DWITH_MEMORY_STORAGE_ENGINE=1 \
		-DENABLED_LOCAL_INFILE=1 \
		-DWITH_PARTITION_STORAGE_ENGINE=1 \
		-DEXTRA_CHARSETS=all \
		-DDEFAULT_CHARSET=utf8 \
		-DDEFAULT_COLLATION=utf8_general_ci \
		-DDOWNLOAD_BOOST=1 \
		-DWITH_BOOST=${mysqlDir}/mysql-5.7.26/boost/
		make && make install && make clean
		echo '5.7' > $serverPath/mysql/version.pl
		echo 'The installation is complete' > $install_tmp
	fi
}

Uninstall_mysql()
{
	rm -rf $serverPath/mysql
	echo 'Uninstall complete' > $install_tmp
}

action=$1
if [ "${1}" == 'install' ];then
	Install_mysql
else
	Uninstall_mysql
fi
