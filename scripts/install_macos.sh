#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
LANG=en_US.UTF-8

USER=$(who | sed -n "2,1p" |awk '{print $1}')
DEV="/Users/${USER}/Desktop/slempdev"


mkdir -p $DEV
mkdir -p $DEV/wwwroot
mkdir -p $DEV/server
mkdir -p $DEV/wwwlogs
mkdir -p $DEV/backup/database
mkdir -p $DEV/backup/site

# install brew
if [ ! -f /usr/local/bin/brew ];then
	/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
	brew install python@2
	brew install mysql
fi

brew install libzip bzip2 gcc openssl re2c cmake


if [ ! -d $DEV/server/panel ]; then
	wget -O /tmp/main.zip https://codeload.github.com/basoro/slemp/zip/main
	cd /tmp && unzip /tmp/main.zip
	mv /tmp/slemp-main $DEV/server/panel
	rm -f /tmp/main.zip
	rm -rf /tmp/slemp-main
fi

if [ ! -d $DEV/server/lib ]; then
	cd $DEV/server/panel/scripts && ./lib.sh
fi

pip install -I -r $DEV/server/panel/requirements.txt

cd $DEV/server/panel && ./cli.sh start
cd $DEV/server/panel && ./cli.sh stop

sleep 5
cd $DEV/server/panel && ./scripts/init.d/slemp default
cd $DEV/server/panel && ./cli.sh debug
