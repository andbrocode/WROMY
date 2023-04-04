#!/bin/bash
#
# sync data with freenas archive
#

YEAR=$(date +%Y)
PINAME=${HOSTNAME:12}

PATH_TO_WROMY_DATA="/home/pi/WROMY/data"
HOST_TARGET="sysop@taupo.geophysik.uni-muenchen.de"
SERVER="/freenas-ffb-01/romy_archive/"

echo -e "\n -> synchronizing: WS${PINAME} ... \n"

/usr/bin/rsync -urlt ${PATH_TO_WROMY_DATA}/WS?.D/${YEAR}/BW* ${HOST_TARGET}:${SERVER}${YEAR}/BW/WROMY/WS${PINAME}.D/ >/dev/null 2>&1
/usr/bin/rsync -urlt ${PATH_TO_WROMY_DATA}/WS?.D/${YEAR}/WROMY*.log ${HOST_TARGET}:${SERVER}${YEAR}/BW/WROMY/logs/ >/dev/null 2>&1
/usr/bin/rsync -urlt ${PATH_TO_WROMY_DATA}/LX?.D/${YEAR}/*.txt ${HOST_TARGET}:${SERVER}${YEAR}/BW/WROMY/LX${PINAME}.D/ >/dev/null 2>&1
/usr/bin/rsync -urlt ${PATH_TO_WROMY_DATA}/Logfiles/*.log ${HOST_TARGET}:${SERVER}${YEAR}/BW/WROMY/logs/ >/dev/null 2>&1

if [ $PINAME == 1 ]; then
    /usr/bin/rsync -urlt ${PATH_TO_WROMY_DATA}/RDN.D/${YEAR}/BW* ${HOST_TARGET}:${SERVER}${YEAR}/BW/WROMY/RDN.D/ >/dev/null 2>&1
fi

## END OF FILE
