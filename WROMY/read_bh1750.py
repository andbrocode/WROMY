#!/usr/bin/python
#---------------------------------------------------------------------
#
# bh1750.py
#
# Read data from a BH1750 digital light sensor and store it.
#
#
# Modified by: Andreas Brotzer (Jul 2021)
# Modified by: Andreas Brtozer (Jan 2023)
# Modified by: Andreas Brtozer (Mar 2023)
#
# Based on original by: Matt Hawkins (26/06/2018)
#
# For more information please visit :
# https://www.raspberrypi-spy.co.uk/?s=bh1750
#
#
#
#-------------- IMPORTS ----------------------------------------------

import collections
import subprocess
import smbus
import time
import yaml
import csv

from pathlib import Path
from datetime import datetime
from numpy import zeros, array

#-------------- SETTINGS ---------------------------------------------

path_to_config = '/home/pi/WROMY/'
config_file = 'bh1750.yaml'


## get raspi id
# pi_name = subprocess.run(['hostname'], capture_output=True, shell=True, check=True).stdout.decode()
# pi_num = int(pi_name[:-1].split("-")[2])

# Define some constants from the datasheet
DEVICE     = 0x23 # Default device I2C address
POWER_DOWN = 0x00 # No active state
POWER_ON   = 0x01 # Power on
RESET      = 0x07 # Reset data register value

# Start measurement at 4lx resolution. Time typically 16ms.
CONTINUOUS_LOW_RES_MODE = 0x13

# Start measurement at 1lx resolution. Time typically 120ms
CONTINUOUS_HIGH_RES_MODE_1 = 0x10

# Start measurement at 0.5lx resolution. Time typically 120ms
CONTINUOUS_HIGH_RES_MODE_2 = 0x11

# Start measurement at 1lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_HIGH_RES_MODE_1 = 0x20

# Start measurement at 0.5lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_HIGH_RES_MODE_2 = 0x21

# Start measurement at 1lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_LOW_RES_MODE = 0x23

#bus = smbus.SMBus(0) # Rev 1 Pi uses 0
bus = smbus.SMBus(1)  # Rev 2 Pi uses 1


#-------------- METHODS ----------------------------------------------

def __convertToNumber(data):

	# Simple function to convert 2 bytes of data
	# into a decimal number. Optional parameter 'decimals'
	# will round to specified number of decimal places.

	result=(data[1] + (256 * data[0])) / 1.2
	return (result)


def __readLight(addr=DEVICE):

	# Read data from I2C interface
	data = bus.read_i2c_block_data(addr, ONE_TIME_HIGH_RES_MODE_1)
	return __convertToNumber(data)


def __writeOutput(outpath, outfile, msg):

	# Write data to output file
	if not Path(outpath).is_dir():
		Path(outpath).mkdir()
	if not Path(outpath+outfile).exists():
		Path(outpath+outfile).touch()

	with open(outpath+outfile,"a") as out:
		writer = csv.writer(out, delimiter=",")
		writer.writerow(msg)
	out.close()


def __checkThresholds(dataBuffer, threshold, statusOld):

	# adopt status if thresholds are passed
        def statusCheck(statusNew):
            if statusOld != statusNew:
                return True
            else:
                return False

	## check if it is dark
        dark = all(i < threshold for i in sorted(array(dataBuffer))[10:])

	## if not dark, it has to be light... 
        if not dark and all(i >= threshold):
            statusNew = 1 # light is on and/or lid open
            return statusNew, statusCheck(statusNew)

        else:
            statusNew = 0 # refers to dark (= closed lid + no light)
            return statusNew, statusCheck(statusNew)


def __readConfig(path, filename):

	import yaml

	with open(path+filename,'r') as stream:
		data = yaml.load(stream, Loader=yaml.FullLoader)
		stream.close()

	return data['CONFIG']



##-------------- MAIN -------------------------------------------------

def main():

	## get raspi id
	pi_name = subprocess.run(['hostname'], capture_output=True, shell=True, check=True).stdout.decode()
	pi_num = int(pi_name.split("-")[2][:-1])

   	## read configuration
	config = __readConfig(path_to_config, config_file)

	## adjust output file
	#config['outFile'] = f"WS{str(pi_num)}.txt"

	## create data buffer
	dataBuffer = collections.deque(zeros(config.get('dataBufferPoints')), maxlen=config.get('dataBufferPoints'))

	## log notes
	logNotes = {0: 'dark', 1: 'light'}

	status  = 0
	counter = 0
	changedStatus = False

	while True:
		
		## counter is required to avoid testing to early
		if counter < 20:
			counter +=1

		## read sensor value
		lightLevel = __readLight()
		lightValue = round(lightLevel, 1)


		## update names
		config['outPathData'] = config.get('outPath')+f"LX{pi_num}.D/{datetime.utcnow().year}/"
		config['outFileLog'] = f"WROMY_LX{pi_num}_{datetime.utcnow().year}.log"

		## check if output path exists
		if not Path(config.get('outPathData')).exists():
			Path(config.get('outPathData')).mkdir()

		## check if logfile exists
		if not Path(config.get('outPathLog')+config.get('outFileLog')).exists():
			Path(config.get('outPathLog')+config.get('outFileLog')).touch()

		## get current time stamp
		dt = datetime.utcnow()
		fdate, ftime = dt.strftime('%Y%m%d'), dt.strftime('%H%M%S')

		## update file name
		filename = f'WS{pi_num}_{fdate}.txt'

		## write output to file
		__writeOutput(config.get('outPathData'), filename, [fdate, ftime, lightValue])

		## add new value to buffer
		dataBuffer.append(lightValue)

		## checks if thresholds have been passed
		if counter > 10:
			lastStatus = status
			status, changedStatus = __checkThresholds(dataBuffer, config.get(f'WS{pi_num}').get('thresholds'), status)


		## output is written, if a threshold has been trespassed
		if changedStatus:
			dt = datetime.utcnow()
			fdate, ftime = dt.strftime('%Y%m%d'), dt.strftime('%H%M%S')

			try:
				msg = [int(fdate), int(ftime), f'WS{pi_num}', 'status', lastStatus, logNotes[lastStatus],'end']
				__writeOutput(config.get('outPathLog'), config.get('outFileLog'), msg)

				msg = [int(fdate), int(ftime), f'WS{pi_num}', 'status', status, logNotes[status],'start']
				__writeOutput(config.get('outPathLog'), config.get('outFileLog'), msg)
			except:
				print(f" -> Failed to write to log file: {outPathLog}{outFileLog}!")

			## reset counter and status boolean to launch relaxation time
			counter, changedStatus = 0, False


		## sleep until next sampling
		time.sleep(config.get('samplePeriod'))



#----------------------------------------------------------------------

if __name__=="__main__":
   main()

## End of File
