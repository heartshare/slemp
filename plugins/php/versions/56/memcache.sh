#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

curPath=`pwd`

rootPath=$(dirname "$curPath")
rootPath=$(dirname "$rootPath")
rootPath=$(dirname "$rootPath")
rootPath=$(dirname "$rootPath")
serverPath=$(dirname "$rootPath")
sourcePath=${serverPath}/source/php

LIBNAME=memcache
LIBV=2.2.7
sysName=`uname`
actionType=$1
version=$2
extFile=$serverPath/php/${version}/lib/php/extensions/no-debug-non-zts-20131226/${LIBNAME}.so

if [ "$sysName" == "Darwin" ];then
	BAK='_bak'
else
	BAK=''
fi

Install_lib()
{
	isInstall=`cat $serverPath/php/$version/etc/php.ini|grep "${LIBNAME}.so"`
	if [ "${isInstall}" != "" ];then
		echo "php-$version ${LIBNAME} is installed, please choose another version!"
		return
	fi

	if [ ! -f "$extFile" ];then

		php_lib=$sourcePath/php_lib
		mkdir -p $php_lib
		if [ ! -d $php_lib/${LIBNAME}-${LIBV} ];then
			wget -O $php_lib/${LIBNAME}-${LIBV}.tgz http://pecl.php.net/get/${LIBNAME}-${LIBV}.tgz
			cd $php_lib && tar xvf ${LIBNAME}-${LIBV}.tgz
		fi
		cd $php_lib/${LIBNAME}-${LIBV}

		$serverPath/php/$version/bin/phpize
		./configure --with-php-config=$serverPath/php/$version/bin/php-config --enable-memcache --with-zlib-dir
		make && make install && make clean

	fi

	if [ ! -f "$extFile" ];then
		echo "ERROR!"
		return
	fi
	echo "extension=${LIBNAME}.so" >> $serverPath/php/$version/etc/php.ini
	echo "extension=${LIBNAME}" >> $serverPath/php/$version/etc/php.ini

	$serverPath/php/init.d/php$version reload
	echo '==========================================================='
	echo 'successful!'
}


Uninstall_lib()
{
	if [ ! -f "$serverPath/php/$version/bin/php-config" ];then
		echo "php-$version is not installed, please select another version!"
		return
	fi

	if [ ! -f "$extFile" ];then
		echo "php-$version not install ${LIBNAME}, Plese select other version!"
		return
	fi

	sed -i $BAK "/${LIBNAME}.so/d" $serverPath/php/$version/etc/php.ini
	sed -i $BAK "/${LIBNAME}/d" $serverPath/php/$version/etc/php.ini

	rm -f $extFile
	$serverPath/php/init.d/php$version reload
	echo '==============================================='
	echo 'successful!'
}


if [ "$actionType" == 'install' ];then
	Install_lib
elif [ "$actionType" == 'uninstall' ];then
	Uninstall_lib
fi
