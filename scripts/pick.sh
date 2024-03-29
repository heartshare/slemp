#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin

curPath=`pwd`
rootPath=$(dirname "$curPath")


#----------------------------- code packaging -------------------------#

echo $rootPath
cd $rootPath
rm -rf ./*.pyc
rm -rf ./*/*.pyc

startTime=`date +%s`

zip -r -q -o panel.zip  ./ -x@$curPath/pick_filter.txt



mv panel.zip $rootPath/scripts

endTime=`date +%s`
((outTime=($endTime-$startTime)))
echo -e "Time consumed:\033[32m $outTime \033[0mSec!"
