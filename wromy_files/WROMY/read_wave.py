# MIT License
#
# This script reads the sensor values of the Wave Radon device by Airthings, manipulates 
# them and writes the data to an outout file to: ./data/BW.WROMY.RDN.D.<year>.<doy>
# 
#
# modified by Andreas Brotzer in 2021. Adjusted for python3 and Wave Radon Device
#
#
# Originally CC license by Copyright (c) 2018 Airthings AS
#
# https://airthings.com

# ===============================
# Module import dependencies
# ===============================

__author__ = 'AndreasBrotzer'
__year__   = '2021'

from bluepy.btle import UUID, Peripheral, Scanner, DefaultDelegate
from pathlib import Path
import csv
import sys
import time
import struct
import datetime


# ===============================
# Set variables
# ===============================

#SerialNumber = int(sys.argv[1])
#SamplePeriod = int(sys.argv[2])

SerialNumber = 2950040221
SamplePeriod = 60
OutPath      = "/home/pi/WROMY/data/RDN.D/"

# ====================================
# Utility functions for WavePlus class
# ====================================

def parseSerialNumber(ManuDataHexStr):
    if (ManuDataHexStr == None or ManuDataHexStr == "None"):
        SN = "Unknown"
    else:
        ManuData = bytearray.fromhex(ManuDataHexStr)

        if (((ManuData[1] << 8) | ManuData[0]) == 0x0334):
            SN  =  ManuData[2]
            SN |= (ManuData[3] << 8)
            SN |= (ManuData[4] << 16)
            SN |= (ManuData[5] << 24)
        else:
            SN = "Unknown"
    return SN

# ===============================
# Class WavePlus
# ===============================

class WavePlus():

	def __init__(self, SerialNumber):
		self.periph        = None
		self.curr_val_char = None
		self.MacAddr       = None
		self.SN            = SerialNumber
		#self.uuid          = UUID("b42e2a68-ade7-11e4-89d3-123b93f75cba")
		# new uuid found in forum: https://github.com/Airthings/wave-reader/issues/6
		self.uuid          = UUID("b42e4dcc-ade7-11e4-89d3-123b93f75cba")

	def connect(self):
		# Auto-discover device on first connection
		if (self.MacAddr is None):
		    scanner     = Scanner().withDelegate(DefaultDelegate())
		    searchCount = 0
		    while self.MacAddr is None and searchCount < 50:
		        devices      = scanner.scan(0.1) # 0.1 seconds scan period
		        searchCount += 1
		        for dev in devices:
		            ManuData = dev.getValueText(255)
		            SN = parseSerialNumber(ManuData)
		            if (SN == self.SN):
		                self.MacAddr = dev.addr # exits the while loop on next conditional check
		                break # exit for loop
		    
		    if (self.MacAddr is None):
		        print("ERROR: Could not find device.")
		        print("GUIDE: (1) Please verify the serial number.")
		        print("       (2) Ensure that the device is advertising.")
		        print("       (3) Retry connection.")
		        sys.exit(1)
		
		# Connect to device
		print("connecting to device")
		if (self.periph is None):
		    self.periph = Peripheral(self.MacAddr)
		if (self.curr_val_char is None):
		    self.curr_val_char = self.periph.getCharacteristics(uuid=self.uuid)[0]

	def read(self):
		if (self.curr_val_char is None):
			print("ERROR: Devices are not connected.")
			sys.exit(1)            
		datetimestring = datetime.datetime.utcnow()
		rawdata = self.curr_val_char.read()
		rawdata = struct.unpack('<BBBBHHHHHHHH', rawdata)
		sensors = Sensors()
		sensors.set(rawdata, datetimestring)
		return sensors

	def disconnect(self):
		if self.periph is not None:
		    self.periph.disconnect()
		    self.periph = None
		    self.curr_val_char = None

# ===================================
# Class Sensor and sensor definitions
# ===================================

NUMBER_OF_SENSORS               = 7
SENSOR_IDX_HUMIDITY             = 0
SENSOR_IDX_RADON_SHORT_TERM_AVG = 1
SENSOR_IDX_RADON_LONG_TERM_AVG  = 2
SENSOR_IDX_TEMPERATURE          = 3
SENSOR_IDX_SDATE		        = 4
SENSOR_IDX_STIME		        = 5

class Sensors():
    def __init__(self):
        self.sensor_version = None
        self.sensor_data    = [None]*NUMBER_OF_SENSORS
        self.sensor_units   = ["%rH", "Bq/m3", "Bq/m3", "degC", "hPa", "ppm", "ppb"]
    
    def set(self, rawData, datetimestring):
        self.sensor_version = rawData[0]
        if (self.sensor_version == 1):
            self.sensor_data[SENSOR_IDX_HUMIDITY]             = rawData[1]/2.0
            self.sensor_data[SENSOR_IDX_RADON_SHORT_TERM_AVG] = self.conv2radon(rawData[4])
            self.sensor_data[SENSOR_IDX_RADON_LONG_TERM_AVG]  = self.conv2radon(rawData[5])
            self.sensor_data[SENSOR_IDX_TEMPERATURE]          = rawData[6]/100.0
            self.sensor_data[SENSOR_IDX_SDATE]	              = datetimestring.strftime("%Y%m%d")
            self.sensor_data[SENSOR_IDX_STIME]                = datetimestring.strftime("%H%M%S")
        else:
            print("ERROR: Unknown sensor version.\n")
            print("GUIDE: Contact Airthings for support.\n")
            sys.exit(1)
   
    def conv2radon(self, radon_raw):
        radon = "N/A" # Either invalid measurement, or not available
        if 0 <= radon_raw <= 16383:
            radon  = radon_raw
        return radon

    def getValue(self, sensor_index):
        return self.sensor_data[sensor_index]

    def getUnit(self, sensor_index):
        return self.sensor_units[sensor_index]




# ====================================
# Write Output to File
# ====================================

def __writeOutput(outpath, outfile, msg):
	
	if not Path(outpath).is_dir():
		Path(outpath).mkdir()
	if not Path(outpath+outfile).exists():
		Path(outpath+outfile).touch()

	with open(outpath+outfile,"a") as out:
		writer = csv.writer(out, delimiter=",")
		writer.writerow(msg)
	out.close()


# ====================================
# MAIN
# ====================================

try:
	#---- Initialize ----#
	waveplus = WavePlus(SerialNumber)

	if not Path(OutPath).exists():
		Path(OutPath).mkdir()

	print("Device serial number: %s" %(SerialNumber))

		
	while True:
		
		connected = False
		attempts = 0
		while not connected and attempts < 10:

			try:
				waveplus.connect()
				connected = True
				print("connected successfully")
				break
			except Exception: 
				waveplus.disconnect()
				waveplus = WavePlus(SerialNumber)
				attempts += 1
				print("yet another try..")				
				raise
				
		# read values
		sensors = waveplus.read()

		# set systime and file
		SysTime = datetime.datetime.utcnow()
		OutFile = "BW.WROMY.RDN.D.%s.%s" %(SysTime.strftime("%Y"), SysTime.strftime("%j"))

		# check file
		if not Path(OutPath+OutFile).exists():
			
			Path(OutPath+OutFile).touch()

			# define header
			header = []
			header.append('Date')
			header.append('Time (UTC)')
			header.append('Humidity (%s)' %(str(sensors.getUnit(SENSOR_IDX_HUMIDITY))))
			header.append('Radon ST avg (%s)' %(str(sensors.getUnit(SENSOR_IDX_RADON_SHORT_TERM_AVG))))
			header.append('Radon LT avg (%s)' %(str(sensors.getUnit(SENSOR_IDX_RADON_LONG_TERM_AVG))))
			header.append('Temperature (%s)' %(str(sensors.getUnit(SENSOR_IDX_TEMPERATURE))))
			print(header)
			# write header
			__writeOutput(OutPath, OutFile, header)

		# extract
		humidity     = str(sensors.getValue(SENSOR_IDX_HUMIDITY))             
		radon_st_avg = str(sensors.getValue(SENSOR_IDX_RADON_SHORT_TERM_AVG)) 
		radon_lt_avg = str(sensors.getValue(SENSOR_IDX_RADON_LONG_TERM_AVG))  
		temperature  = str(sensors.getValue(SENSOR_IDX_TEMPERATURE))          

		sdate        = sensors.getValue(SENSOR_IDX_SDATE)
		stime		 = sensors.getValue(SENSOR_IDX_STIME)

		data = [sdate, stime, humidity, radon_st_avg, radon_lt_avg, temperature]
		
		# Print data		
		__writeOutput(OutPath, OutFile, data)



		print(data)


		waveplus.disconnect()

		time.sleep(SamplePeriod)
			
finally:
    waveplus.disconnect()

# END OF FILE
