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

actionType=$1
version=$2

LIBNAME=fileinfo
LIBV=0

NON_ZTS_FILENAME=`ls $serverPath/php/${version}/lib/php/extensions | grep no-debug-non-zts`
extFile=$serverPath/php/${version}/lib/php/extensions/${NON_ZTS_FILENAME}/${LIBNAME}.so

sysName=`uname`
if [ "$sysName" == "Darwin" ];then
	BAK='_bak'
else
	BAK=''
fi

Install_lib()
{

	isInstall=`cat $serverPath/php/$version/etc/php.ini|grep "${LIBNAME}.so"`
	if [ "${isInstall}" != "" ];then
		echo "php-$version not install ${LIBNAME}, Plese select other version!"
		return
	fi

	if [ ! -f "$extFile" ];then

		if [ ! -d $sourcePath/php${version}/ext ];then
			cd $serverPath/panel/plugins/php && /bin/bash install.sh install ${version}
		fi

		cd $sourcePath/php${version}/ext/${LIBNAME}


		#o my god. fuck,what error? fix it
		FIND_undef=`cat Makefile|grep '#undef strndup'`
		if [ "$FIND_undef" == "" ];then
			sed -i $BAK "s/char \*strndup/\#undef strndup\nchar \*strndup/g" libmagic/softmagic.c
		fi

		$serverPath/php/$version/bin/phpize
		./configure --with-php-config=$serverPath/php/$version/bin/php-config

		FIND_C99=`cat Makefile|grep c99`
		if [ "$FIND_C99" == "" ];then
			sed -i $BAK 's/CFLAGS \=/CFLAGS \= -std=c99/g' Makefile
		fi

		make && make install && make clean

	fi

	if [ ! -f "$extFile" ];then
		echo "ERROR!"
		return
	fi


    echo "" >> $serverPath/php/$version/etc/php.ini
	echo "[${LIBNAME}]" >> $serverPath/php/$version/etc/php.ini
	echo "extension=${LIBNAME}.so" >> $serverPath/php/$version/etc/php.ini

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

	echo $serverPath/php/$version/etc/php.ini
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
