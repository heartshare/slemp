#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin

curPath=`pwd`
rootPath=$(dirname "$curPath")
serverPath=$(dirname "$rootPath")
sourcePath=$serverPath/source/lib
libPath=$serverPath/lib

mkdir -p $sourcePath
mkdir -p $libPath
rm -rf ${libPath}/lib.pl

Install_Libzip()
{
#----------------------------- libzip start -------------------------#
if [ ! -d ${libPath}/libzip ];then
    cd ${sourcePath}
    if [ ! -f ${sourcePath}/libzip-1.2.0.tar.gz ];then
    	wget -O libzip-1.2.0.tar.gz https://nih.at/libzip/libzip-1.2.0.tar.gz -T 20
    fi
    tar -zxf libzip-1.2.0.tar.gz
    cd libzip-1.2.0
    ./configure --prefix=${libPath}/libzip && make && make install
fi
echo -e "Install_Libzip" >> ${libPath}/lib.pl
#----------------------------- libzip end  -------------------------#
}

Install_Libiconv()
{
#----------------------------- libiconv start -------------------------#
	cd ${sourcePath}
	if [ ! -d ${libPath}/libiconv ];then
		# wget -O libiconv-1.15.tar.gz  https://ftp.gnu.org/pub/gnu/libiconv/libiconv-1.15.tar.gz  -T 5
		wget -O libiconv-1.15.tar.gz https://raw.githubusercontent.com/basoro/slemp/gh-pages/assets/libiconv-1.15.tar.gz -T 5
		tar zxvf libiconv-1.15.tar.gz
		cd libiconv-1.15
	    ./configure --prefix=${libPath}/libiconv --enable-static
	    make && make install
	    cd ${sourcePath}
	    rm -rf libiconv-1.15
		rm -f libiconv-1.15.tar.gz
	fi
	echo -e "Install_Libiconv" >> ${libPath}/lib.pl
#----------------------------- libiconv end -------------------------#
}


Install_Libiconv
# Install_Libzip

sysName=`uname`
if [ "$sysName" == "Darwin" ];then
    brew install libmemcached
    brew install curl
    brew install zlib
    brew install freetype
    brew install openssl
    brew install libzip
else
    yum -y install libmemcached libmemcached-devel
    yum -y install curl curl-devel
    yum -y install zlib zlib-devel
    yum -y install freetype freetype-devel
    yum -y install openssl openssl-devel
    yum -y install libzip libzip-devel
    yum -y install graphviz

    yum -y install sqlite-devel
    yum -y install oniguruma oniguruma-devel
    yum -y install ImageMagick ImageMagick-devel
fi
