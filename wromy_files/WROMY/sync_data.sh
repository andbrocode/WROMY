#!/bin/bash

YEAR=$(date +%Y)
PINAME=${HOSTNAME:12}

PATH_TO_WROMY_DATA="/home/pi/WROMY/data"
HOST_TARGET="sysop@taupo.geophysik.uni-muenchen.de"


echo -e "\n synchronizing: WS${PINAME} ..."

/usr/bin/rsync -urlt ${PATH_TO_WROMY_DATA}/WS?.D/${YEAR}/BW* ${HOST_TARGET}:/freenas-ffb-01/romy_archive/${YEAR}/BW/WROMY/WS${PINAME}.D/ >/dev/null 2>&1
/usr/bin/rsync -urlt ${PATH_TO_WROMY_DATA}/WS?.D/${YEAR}/WROMY*.log ${HOST_TARGET}:/freenas-ffb-01/romy_archive/${YEAR}/BW/WROMY/logs/ >/dev/null 2>&1
/usr/bin/rsync -urlt ${PATH_TO_WROMY_DATA}/LX?.D/${YEAR}/*.txt ${HOST_TARGET}:/freenas-ffb-01/romy_archive/${YEAR}/BW/WROMY/LX${PINAME}.D/ >/dev/null 2>&1
/usr/bin/rsync -urlt ${PATH_TO_WROMY_DATA}/WROMY*.log ${HOST_TARGET}:/freenas-ffb-01/romy_archive/${YEAR}/BW/WROMY/logs/ >/dev/null 2>&1

if [ $PINAME == 1 ]; then
    /usr/bin/rsync -urlt ${PATH_TO_WROMY_DATA}/RDN.D/${YEAR}/BW* ${HOST_TARGET}:/freenas-ffb-01/romy_archive/${YEAR}/BW/WROMY/RDN.D/ >/dev/null 2>&1
fi

## END OF FILE
