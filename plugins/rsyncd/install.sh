#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH


curPath=`pwd`
rootPath=$(dirname "$curPath")
rootPath=$(dirname "$rootPath")
serverPath=$(dirname "$rootPath")
sysName=`uname`

install_tmp=${rootPath}/tmp/slemp_install.pl
Install_rsyncd()
{
	echo 'Installing script file...' > $install_tmp
	mkdir -p $serverPath/rsyncd
	echo '1.0' > $serverPath/rsyncd/version.pl
	echo 'The installation is complete' > $install_tmp

}

Uninstall_rsyncd()
{
	rm -rf $serverPath/rsyncd
	echo "Uninstall complete" > $install_tmp
}

action=$1
if [ "${1}" == 'install' ];then
	Install_rsyncd
else
	Uninstall_rsyncd
fi
