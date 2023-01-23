#!/bin/bash
#
# crontab job to check if the script, which is passed as an arguemnt
# is running an active process. If not, it is restarted up to 5 times
# and terminated after. Log files are written and status updates sent
# via mail.
#
# author: Andreas Brotzer
# year:   2021
#
mailadress="brotzer@geophysik.uni-muenchen.de"
#
## _____________________________________________
## set variables

process=${1}

path="${HOME}/WROMY/"

logpath="${path}data/"

#mailadress="brotzer@geophysik.uni-muenchen.de"

host=$(hostname)
pi_name=${host:12}

subject="WROMY-WS${pi_name}-LOG"

## _____________________________________________
## define functions 

## check if value 999.9 is several times in array of last measurements
function check () {
	counter=0
	array=$1

	for i in ${array[@]};do

		if [ "$i" == "999.9" ]; then 
			counter=$(($counter + 1))
		fi
	done

	if [ $counter -gt 5 ]; then
		echo 1
	else
		echo 0
	fi
}


## check if sensor error occurred and send mail if detected
function check_values () {

	pi_name=$1
 	mailadress=$2

	sdate=$(date +"%Y%m%d")
	stime=$(date +"%H%M%S")
	doy=$(date +"%j")


	t=$(tail -n 25 /home/pi/WROMY/data/WS${pi_name}.D/BW.WROMY.WS${pi_name}.D.${sdate:0:4}.${doy} | awk -F"," '{print $4}')
	p=$(tail -n 25 /home/pi/WROMY/data/WS${pi_name}.D/BW.WROMY.WS${pi_name}.D.${sdate:0:4}.${doy} | awk -F"," '{print $5}')
	h=$(tail -n 25 /home/pi/WROMY/data/WS${pi_name}.D/BW.WROMY.WS${pi_name}.D.${sdate:0:4}.${doy} | awk -F"," '{print $6}')

	check_t=$(check "${t[@]}")
	check_p=$(check "${p[@]}")
	check_h=$(check "${h[@]}")

	## when errofile exists, no new mail is being send. Avoids mailbox spam
	## file in /tmp -> will be removed at reboot
	if [ -f $errorfile ]; then
		exit
	fi

	if [[ ( "$check_t" == "1" ) || ( "$check_p" == "1" ) || ( "$check_h" == "1" ) ]]; then 
		echo " -> ERROR 999.9 detected!"
		echo "${sdate}, ${stime}, ERROR 999.9 occured for WS${pi_name}!" | mail -s "WROMY-WS${pi_name}-ERROR" $mailadress
	fi

}


## _____________________________________________

{

if [ -z "$process" ];then
	echo "no process passed!"
	exit
fi

if [ -f "/tmp/terminated.tmp" ];then
	echo "status: is termiated"
	exit
fi

## _____________________________________________
## check if acquisition script is still a running process
# if (! (pgrep -f "python3 ${path}${process}" &>/dev/null)); then

## check screen sessions rather than processes

if [ ${process} == "read_wave.py" ]; then
	screen_status=$(sudo screen -S ${process} -Q select . ; echo $?)
else
	screen_status=$(screen -S ${process} -Q select . ; echo $?)
fi


if [ ! "${screen_status}" == 0 ]; then

	counter=1
	while [ $counter -lt 5 ]; do

		echo -e "\n____________________"
		echo "${counter}: not running "

		## get current date and time
		date=$(date +"%Y%m%d")
		time=$(date +"%H%M%S")

		## restart acquisition script
		if [ ${process} == "read_wave.py" ]; then
#			sudo screen -S ${process%%.*} -X quit
			sudo screen -S ${process} -X quit
#			sudo screen -dmS ${process%%.*} /usr/bin/python3 ${path}${process} & 
			sudo screen -dmS ${process} /usr/bin/python3 ${path}${process} & 
		else
			## quit and start the script again as a screen session
#			screen -S ${process%%.*} -X quit
			screen -S ${process} -X quit
#			screen -dmS ${process%%.*} /usr/bin/python3 ${path}${process} &
			screen -dmS ${process} /usr/bin/python3 ${path}${process} &

		fi

		## pause a moment
		sleep 5

		## increase counter
		counter=$((${counter}+1))

		## check if process has started
		if (pgrep -f "${process}" &>/dev/null); then
			echo "${date}, ${time}, LT,$process restarted successfully" >> "${logpath}WROMY${pi_name}_${date:0:4}.log"
			echo "${date}, ${time}, LT, $process restarted successfully" | mail -s ${subject} ${mailadress}
			echo -e  "\n -> process running again"
			counter=5
			break
		else
			echo "${date}, ${time}, LT, $process restart ${counter} failed" >> "${logpath}WROMY${pi_name}_${date:0:4}.log"

		fi

	## if restart failed 5 times, this script is terminated
	if [ $counter == 5 ]; then
		echo "${date}, ${time}, LT, $process restart failed" >> "${logpath}WROMY${pi_name}_${date:0:4}.log"
	    	echo "${date}, ${time}, LT, checkromywetter.sh has been terminated" >> "${logpath}WROMY${pi_name}_${date:0:4}.log"

		line1="${date}, ${time}, LT, $process restart failed "
		line2="${date}, ${time}, LT, checkromywetter.sh has been terminated"
		echo -e "$line1 \n $line2" | mail -s ${subject} ${mailadress}

		touch "/tmp/terminated.tmp"
		exit
	fi
	done

elif (pgrep -f "python3 ${path}${process}" &>/dev/null); then
	echo "already running"

fi
}

## _____________________________________________
## check if sensor error occurred (=999.9) and send status mail in case
if [ $process == "read_lambrecht.py" ]; then
	check_values $pi_name $mailadress
	echo " -> checked for sensor errors"
fi

exit
## END OF FILE
