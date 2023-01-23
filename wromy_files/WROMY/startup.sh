#!/bin/bash
#
# start up acquistion scripts at reboot
#
#
# by Andreas Brotzer @2021
## ____________________________________

function check_process {
	if (pgrep -f "python3 ${1}" &>/dev/null); then
		echo " -> launched ${1##*/}"
		stat="ok"
	else 
		echo " -> Error"
		stat="error"
	fi
    eval "$2=$stat"
}

function launch_script {

	screen -S ${2} -X quit
	screen -dmS ${2} python3 ${1}${2}

	check_process ${1}${2} $3

}

## ____________________________________
## set variables

mailadress="brotzer@geophysik.uni-muenchen.de"

workdir="/home/pi/WROMY/"
datapath="${workdir}data/"

sdate=$(date '+%Y%m%d')
stime=$(date '+%H%M%S')

hostname=$(hostname)
pi_name=${hostname:12}

subject="WROMY-WS${pi_name}-LOG"

## ____________________________________
## launch acuisition scripts 

script1="read_lambrecht.py"
launch_script $workdir $script1 status1

sleep 3

script2="read_bh1750.py"
launch_script $workdir $script2 status2


if [ $pi_name == 1 ]; then
	sudo screen -dmS read_wave python3 /home/pi/WROMY/read_wave.py
	check_process "/home/pi/WROMY/read_wave.py" status3

fi



## ____________________________________
## write log and send status report

message="${sdate}, ${stime}, WS${pi_name} started acquisition, ${script1}=${status1}, ${script2}=${status2}"
echo $message > "${datapath}WROMY${pi_name}_${sdate:0:4}.log"
echo $message | mail -s $subject $mailadress

exit
# END OF FILE
