#!/bin/bash
# Autor: s0cket8088
# Date: 17/02/2018

# Apache IDS

# vars
file1=/tmp/apache.0
file2=/tmp/apache.1


function redirect {
	#echo "[+] Log redirect"
	trap 'exit 0' TERM
	exec > /dev/null 2>&1
	tail -n0 -f $log > $file1 2>&1
}

function rotate {
	#echo "[+] Log rotate"
	cp $file1 $file2
	cat /dev/null > $file1
}

function kill-redirect {
	#echo "[+] Kill process"
	PID=$(ps -ef | grep tail | grep -v grep | awk '$3~/'$$'/{print$2}')
	kill $PID
}

function log-search {
	#echo "[+] Log search"
	while read line
		do
		vulnerability=$(echo $line | awk -F ';' '{print$1}')
		payload=$(echo $line | awk -F ';' '{print$2}')
	
		if [ $(cat $file2 | grep -i $payload | wc -l) != 0 ]
		then
			echo "[+] $vulnerability attack detected!" | tee -a malicious.txt
			cat $file2 | grep -i $payload >> malicious.txt		
		fi
	done < signatures.list
}


# input parameter check and print usage
if [ $# != 1 ]
then
	echo 'Usage:
	bash Apache-IDS.sh <log-path>
	bash Apache-IDS.sh /var/log/apache2/access.log'
exit
fi

# save input parameter
log=$1

# print banner
clear
echo '
##############################################################################
##				APACHE IDS				    ##
##############################################################################

[+] If an attack is detected it will show it on the screen.
[+] Please wait.'

# loop
while [ 1 ]; do
	echo -e "\n[+] Searching..."
	redirect &
	sleep 5
	kill-redirect
	log-search
	rotate
done

