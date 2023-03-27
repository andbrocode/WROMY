#!/usr/bin/python3 
#
# script to exert acoustic signal when radon level is critical!
#
# AndBro @2021
#
## _________________________________

import RPi.GPIO as GPIO
import time 

from datetime import datetime


## variables ___________________________

this_year = datetime.utcnow().strftime("%Y")

path_to_data = f'/home/pi/WROMY/data/RDN.D/{this_year}/'

buzzer = 4

## initialisiere GPIO __________________________

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(buzzer,GPIO.OUT)

try:
    while True:
    
        ## chill a bit
        time.sleep(20)

        ## dynamic variables
        fdoy     = datetime.utcnow().strftime("%j")
        fyear    = datetime.utcnow().strftime("%Y")
        filename = f'BW.WROMY.RDN.D.{fyear}.{fdoy}'

        ## get last radon readings
        with open(path_to_data+filename, 'r') as rdn:
            lines = rdn.readlines()
            if lines:
                last_line = lines[-1]
            radon_value = last_line.split(",")[3]
            print("Radon value:" + radon_value + "Bq/m3")

        ## check if thresholds are exceeded 
        if int(radon_value) > 300 and int(radon_value) < 1000: 
            for i in range(10):
                GPIO.output(buzzer,GPIO.HIGH)
                time.sleep(1)
                GPIO.output(buzzer,GPIO.LOW)
                time.sleep(2)

        elif int(radon_value) > 1000:
            for i in range(10):
                GPIO.output(buzzer,GPIO.HIGH)
                time.sleep(1)
                GPIO.output(buzzer,GPIO.LOW)
                time.sleep(0.5)

except KeyboardInterrupt:
    print("Some error occurred!")
    GPIO.cleanup()  
    pass


## End Of File
