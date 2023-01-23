#!/bin/bash
#
# update /WROMY on all raspi-romy-0[1-9] 
#
# Andbro @2021
# ___________

for i in 1 4 5 6 7 8 9;do 

echo "____________________________"
echo "updating raspi-romy-0$i ..."

rsync -arutv -e ssh --exclude="data/*"  ./WROMY pi@raspi-romy-0${i}:~

done 

## END OF FILE
