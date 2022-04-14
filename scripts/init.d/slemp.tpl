#!/bin/bash
# chkconfig: 2345 55 25
# description: SLEMP Cloud Service

### BEGIN INIT INFO
# Provides:          bt
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts slemp
# Description:       starts the slemp
### END INIT INFO


PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin

slemp_path={$SERVER_PATH}

slemp_start(){
	isStart=`ps -ef|grep 'gunicorn -c setting.py app:app' |grep -v grep|awk '{print $2}'`
	if [ "$isStart" == '' ];then
            echo -e "Starting slemp... \c"
            cd $slemp_path && gunicorn -c setting.py app:app
            port=$(cat ${slemp_path}/data/port.pl)
            isStart=""
            while [[ "$isStart" == "" ]];
            do
                echo -e ".\c"
                sleep 0.5
                isStart=$(lsof -n -P -i:$port|grep LISTEN|grep -v grep|awk '{print $2}'|xargs)
                let n+=1
                if [ $n -gt 15 ];then
                    break;
                fi
            done
            if [ "$isStart" == '' ];then
                    echo -e "\033[31mfailed\033[0m"
                    echo '------------------------------------------------------'
                    tail -n 20 ${slemp_path}/logs/error.log
                    echo '------------------------------------------------------'
                    echo -e "\033[31mError: slemp service startup failed.\033[0m"
                    return;
            fi
            echo -e "\033[32mdone\033[0m"
    else
            echo "Starting slemp... slemp(pid $(echo $isStart)) already running"
    fi


    isStart=$(ps aux |grep 'task.py'|grep -v grep|awk '{print $2}')
    if [ "$isStart" == '' ];then
            echo -e "Starting slemp-tasks... \c"
            cd $slemp_path && nohup python task.py >> $slemp_path/logs/task.log 2>&1 &
            sleep 0.3
            isStart=$(ps aux |grep 'task.py'|grep -v grep|awk '{print $2}')
            if [ "$isStart" == '' ];then
                    echo -e "\033[31mfailed\033[0m"
                    echo '------------------------------------------------------'
                    tail -n 20 $slemp_path/logs/task.log
                    echo '------------------------------------------------------'
                    echo -e "\033[31mError: slemp-tasks service startup failed.\033[0m"
                    return;
            fi
            echo -e "\033[32mdone\033[0m"
    else
            echo "Starting slemp-tasks... slemp-tasks (pid $isStart) already running"
    fi
}


slemp_stop()
{
	echo -e "Stopping slemp-tasks... \c";
    pids=$(ps aux | grep 'task.py'|grep -v grep|awk '{print $2}')
    arr=($pids)

    for p in ${arr[@]}
    do
            kill -9 $p
    done
    echo -e "\033[32mdone\033[0m"

    echo -e "Stopping slemp... \c";
    arr=`ps aux|grep 'gunicorn -c setting.py app:app'|grep -v grep|awk '{print $2}'`
	for p in ${arr[@]}
    do
            kill -9 $p &>/dev/null
    done

    if [ -f $pidfile ];then
    	rm -f $pidfile
    fi
    echo -e "\033[32mdone\033[0m"
}

slemp_status()
{
        isStart=$(ps aux|grep 'gunicorn -c setting.py app:app'|grep -v grep|awk '{print $2}')
        if [ "$isStart" != '' ];then
                echo -e "\033[32mslemp (pid $(echo $isStart)) already running\033[0m"
        else
                echo -e "\033[31mslemp not running\033[0m"
        fi

        isStart=$(ps aux |grep 'task.py'|grep -v grep|awk '{print $2}')
        if [ "$isStart" != '' ];then
                echo -e "\033[32mslemp-task (pid $isStart) already running\033[0m"
        else
                echo -e "\033[31mslemp-task not running\033[0m"
        fi
}


slemp_reload()
{
	isStart=$(ps aux|grep 'gunicorn -c setting.py app:app'|grep -v grep|awk '{print $2}')

    if [ "$isStart" != '' ];then
    	echo -e "Reload slemp... \c";
	    arr=`ps aux|grep 'gunicorn -c setting.py app:app'|grep -v grep|awk '{print $2}'`
		for p in ${arr[@]}
        do
                kill -9 $p
        done
        cd $slemp_path && gunicorn -c setting.py app:app
        isStart=`ps aux|grep 'gunicorn -c setting.py app:app'|grep -v grep|awk '{print $2}'`
        if [ "$isStart" == '' ];then
                echo -e "\033[31mfailed\033[0m"
                echo '------------------------------------------------------'
                tail -n 20 $slemp_path/logs/error.log
                echo '------------------------------------------------------'
                echo -e "\033[31mError: slemp service startup failed.\033[0m"
                return;
        fi
        echo -e "\033[32mdone\033[0m"
    else
        echo -e "\033[31mslemp not running\033[0m"
        slemp_start
    fi
}


error_logs()
{
	tail -n 100 $slemp_path/logs/error.log
}

case "$1" in
    'start') slemp_start;;
    'stop') slemp_stop;;
    'reload') slemp_reload;;
    'restart')
        slemp_stop
        slemp_start;;
    'status') slemp_status;;
    'logs') error_logs;;
    'default')
        cd $slemp_path
        port=$(cat $slemp_path/data/port.pl)
        password=$(cat $slemp_path/data/default.pl)
        if [ -f $slemp_path/data/domain.conf ];then
            address=$(cat $slemp_path/data/domain.conf)
        fi
        if [ -f $slemp_path/data/admin_path.pl ];then
            auth_path=$(cat $slemp_path/data/admin_path.pl)
        fi
        if [ "$address" = "" ];then
            address=$(curl -sS --connect-timeout 10 -m 60 https://www.bt.cn/Api/getIpAddress)
        fi
        echo -e "=================================================================="
        echo -e "\033[32mSLEMP-Panel default info!\033[0m"
        echo -e "=================================================================="
        echo  "SLEMP-Panel-URL: http://$address:$port$auth_path"
        echo -e `python $slemp_path/tools.py username`
        echo -e "password: $password"
        echo -e "\033[33mWarning:\033[0m"
        echo -e "\033[33mIf you cannot access the panel, \033[0m"
        echo -e "\033[33mrelease the following port (7200|888|80|443|22) in the security group\033[0m"
        echo -e "=================================================================="
        ;;
esac
