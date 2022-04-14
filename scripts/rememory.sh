#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
#+------------------------------------
#+ free memory script
#+------------------------------------

endDate=`date +"%Y-%m-%d %H:%M:%S"`
sysName=`uname`
curPath=`pwd`
rootPath=$(dirname "$curPath")

log="free memory!"
echo "★[$endDate] $log"
echo '----------------------------------------------------------------------------'

if [ $sysName == 'Darwin' ]; then
	echo 'Apple memory free!'
else
	echo 'do start!'
fi

if [ -f $rootPath"/php/init.d/php52" ];then
	$rootPath"/php/init.d/php52" reload
fi

if [ -f $rootPath"/php/init.d/php53" ];then
	$rootPath"/php/init.d/php53" reload
fi

if [ -f $rootPath"/php/init.d/php54" ];then
	$rootPath"/php/init.d/php54" reload
fi

if [ -f $rootPath"/php/init.d/php55" ];then
	$rootPath"/php/init.d/php55" reload
fi

if [ -f $rootPath"/php/init.d/php56" ];then
	$rootPath"/php/init.d/php56" reload
fi

if [ -f $rootPath"/php/init.d/php70" ];then
	$rootPath"/php/init.d/php70" reload
fi

if [ -f $rootPath"/php/init.d/php71" ];then
	$rootPath"/php/init.d/php71" reload
fi

if [ -f $rootPath"/php/init.d/php72" ];then
	$rootPath"/php/init.d/php72" reload
fi

if [ -f $rootPath"/php/init.d/php73" ];then
	$rootPath"/php/init.d/php73" reload
fi

if [ -f $rootPath"/php/init.d/php74" ];then
	$rootPath"/php/init.d/php74" reload
fi

if [ -f $rootPath"/php/init.d/php80" ];then
	$rootPath"/php/init.d/php80" reload
fi

if [ -f $rootPath"/php/init.d/php81" ];then
	$rootPath"/php/init.d/php81" reload
fi

if [ -f $rootPath"/openresty/nginx/sbin/nginx" ];then
	$rootPath"/openresty/nginx/sbin/nginx" -s reload
fi

sync
sleep 2
sync

if [ $sysName == 'Darwin' ]; then
	echo 'done!'
else
	echo 3 > /proc/sys/vm/drop_caches
fi

echo '----------------------------------------------------------------------------'
