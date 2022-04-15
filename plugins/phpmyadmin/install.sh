#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

curPath=`pwd`
rootPath=$(dirname "$curPath")
rootPath=$(dirname "$rootPath")
serverPath=$(dirname "$rootPath")

install_tmp=${rootPath}/tmp/slemp_install.pl

Install_phpmyadmin()
{
	mkdir -p ${serverPath}/phpmyadmin
	mkdir -p ${serverPath}/source/phpmyadmin

	VER=$1
	FILE=phpMyAdmin-${VER}-all-languages.tar.gz
	FDIR=phpMyAdmin-${VER}-all-languages
	DOWNLOAD=https://files.phpmyadmin.net/phpMyAdmin/${VER}/$FILE


	if [ ! -f $serverPath/source/phpmyadmin/$FILE ];then
		wget -O $serverPath/source/phpmyadmin/$FILE $DOWNLOAD --no-check-certificate
	fi

	if [ ! -d $serverPath/source/phpmyadmin/$FDIR ];then
		cd $serverPath/source/phpmyadmin  && tar zxvf $FILE
	fi

	cp -r $serverPath/source/phpmyadmin/$FDIR $serverPath/phpmyadmin/
	cd $serverPath/phpmyadmin/ && mv $FDIR phpmyadmin

	echo "${1}" > ${serverPath}/phpmyadmin/version.pl
	echo 'The installation is complete' > $install_tmp

}

Uninstall_phpmyadmin()
{
	rm -rf ${serverPath}/phpmyadmin
	echo 'Uninstall complete' > $install_tmp
}

action=$1
if [ "${1}" == 'install' ];then
	Install_phpmyadmin $2
else
	Uninstall_phpmyadmin $2
fi
