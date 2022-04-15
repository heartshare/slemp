#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

curPath=`pwd`
rootPath=$(dirname "$curPath")
rootPath=$(dirname "$rootPath")
serverPath=$(dirname "$rootPath")

install_tmp=${rootPath}/tmp/slemp_install.pl


action=$1
type=$2

if [ "${2}" == "" ];then
	echo 'Missing installation script...' > $install_tmp
	exit 0
fi

if [ ! -d $curPath/versions/$2 ];then
	echo 'Missing install script 2...' > $install_tmp
	exit 0
fi

sh -x $curPath/versions/$2/install.sh $1
