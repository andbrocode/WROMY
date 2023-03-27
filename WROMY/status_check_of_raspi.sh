#! /bin/bash
#
# checking status of raspberry pi
#
# Andreas Brotzer @2021
## _____________________

ofile='/tmp/status.tmp'
mailadress='brotzer@geophysik.uni-muenchen.de'

## _____________________

host=$(hostname)
pi_name=${host:12}

sdate=$(date +"%Y%m%d")
stime=$(date +"%H%M%S")

rm $ofile

## _____________________

echo "NAME  : $(uname -n)
DATE  : $(date)
MODEL : $(cat /sys/firmware/devicetree/base/model | tr '\0' ' ')
OS    : $(grep PRETTY_NAME /etc/os-release | cut -d \" -f 2)
KERNEL: $(uname -r)
IP    : $(ifconfig | grep broadcast |tr -s ' '| cut -d ' ' -f 3)
CPU T : $(vcgencmd measure_temp | egrep -o '[0-9]*\.[0-9]*') °C
Core V: $(vcgencmd measure_volts core | egrep -o '[0-9]*\.[0-9]*') Volts
UPTIME:$(uptime)
" > $ofile

## _____________________

STATUS=$(vcgencmd get_throttled | sed -n 's|^throttled=\(.*\)|\1|p')
if [[ ${STATUS} -ne 0 ]]; then
  echo "" >> $ofile
  if [ $((${STATUS} & 0x00001)) -ne 0 ]; then
    echo "${sdate}, ${stime}, Power is currently Under Voltage" >> $ofile
  elif [ $((${STATUS} & 0x10000)) -ne 0 ]; then
    echo "${sdate}, ${stime}, Power has previously been Under Voltage" >> $ofile
  fi
  if [ $((${STATUS} & 0x00002)) -ne 0 ]; then
    echo "${sdate}, ${stime}, ARM Frequency is currently Capped" >> $ofile
  elif [ $((${STATUS} & 0x20000)) -ne 0 ]; then
    echo "${sdate}, ${stime}, ARM Frequency has previously been Capped" >> $ofile
  fi
  if [ $((${STATUS} & 0x00004)) -ne 0 ]; then
    echo "${sdate}, ${stime}, CPU is currently Throttled" >> $ofile
  elif [ $((${STATUS} & 0x40000)) -ne 0 ]; then
    echo "${sdate}, ${stime}, CPU has previously been Throttled" >> $ofile
  fi
  if [ $((${STATUS} & 0x00008)) -ne 0 ]; then
    echo "${sdate}, ${stime}, Currently at Soft Temperature Limit" >> $ofile
  elif [ $((${STATUS} & 0x80000)) -ne 0 ]; then
    echo "${sdate}, ${stime}, Previously at Soft Temperature Limit" >> $ofile
  fi

  cat $ofile | mail -s "Warning raspi-romy-0${pi_name}" $mailadress  

  else
    echo "No abnormalities were detected!"
  echo ""
fi


exit
## _____________________
## END OF FILE
