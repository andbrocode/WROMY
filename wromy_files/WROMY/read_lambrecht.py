"""
read_lambrecht.py


ROMY wetter aqcuistition script

The output of the Lambrecht THP senors is received as three susequent strings,
which are formatted and written to day files: ./data/BW.WROMY.WS*.D.<year>.<doy>

A logfile is written in ./data/<year>.log

"""
__author__ = 'AndreasBrotzer'
__year__   = '2021'

##_____________________________________________________________
 

'''---- import libraries ----'''

import sys, serial, csv, subprocess, glob

from os import path
from pathlib import Path
from datetime import datetime

##_____________________________________________________________
''' ---- set variables ---- '''

## automatically find connected UBS port
port=subprocess.run(['ls /dev/ttyUSB*'], capture_output=True, shell=True, check=True).stdout.decode()[:-1]

serialport, baudrate = port, 4800
#serialport, baudrate = "/dev/wetter", 4800


## get raspi id
pi_name = subprocess.run(['hostname'], capture_output=True, shell=True, check=True).stdout.decode()
pi_num = int(pi_name[:-1].split("-")[2])

outpath = f'/home/pi/WROMY/data/WS{pi_num}.D/'

##_____________________________________________________________
'''---- define methods ----'''

class Log():

    def __init__(self, path, filename):
        self.path = path
        self.filename = filename

    def logging(self, msg):
        with open(self.path+self.filename, "a") as l:
             writer = csv.writer(l, delimiter=",")
             writer.writerow([msg])
        l.close()


def __checkLogFile(outpath, logname):
    if not path.isdir(outpath):
        Path(outpath).mkdir()
        log.logging(f'{datetime.utcnow().strftime("%Y%m%d, %H%M%S")}, created {outpath}')
    if not path.isfile(outpath+logname):
        Path(outpath+logname).touch()
        log.logging(f'{datetime.utcnow().strftime("%Y%m%d, %H%M%S")}, created {outpath}{logname}')


def __checkOutputFile(outpath, outfile):
    if not path.isdir(outpath):
        Path(outpath).mkdir()
        log.logging(f"created {outpath}")

    if not path.isfile(outpath+outfile):

        ## count lines of last file
        last_file = max(glob.glob(outpath+"/*"), key=path.getctime)
        out = subprocess.run(['wc -l {}'.format(last_file)], capture_output=True, shell=True, check=True)
        lines = int(str(out.stdout.decode()).split(" ")[0])

        ## make new file
        Path(outpath+outfile).touch()

        ## write header to file
        header = ["Seconds", "Date", "Time (UTC)", "Temperature (°C)", "Pressure (hPa)", "rel. Humidity (%)"]
        __writeOutput(outpath, outfile, header)

        ## add entry to logfile
        #log.logging(f'{datetime.utcnow().strftime("%Y%m%d, %H%M%S")},{last_file.split("/")[-1]} contains {lines} lines')
        #log.logging(f'{datetime.utcnow().strftime("%Y%m%d, %H%M%S")},{outfile} has been created')


def __writeOutput(outpath, outfile, msg):
    with open(outpath+outfile,"a") as out:
        writer = csv.writer(out, delimiter=",")
        writer.writerow(msg)
   

def main():

    ## initalize serial connection
    ser = serial.Serial(port=serialport, baudrate=baudrate)
    ser.flushInput()

    ## initialize log object
    logname = f"WROMY_WS{pi_num}_{datetime.utcnow().strftime('%Y')}.log"
    global log
    log = Log(outpath, logname)

    ## check if log file exits
    __checkLogFile(outpath, logname)
	


    while True:

        try:

            ## join subsequent output strings
            i = 0
            dataarray = []
            while i < 3:
                i+=1

                ser_bytes = ser.readline()
                datastring = ser_bytes[0:len(ser_bytes)-2].decode()
                dataarray.append(datastring)

                ## avoid to start collecting data inbetween datastring transmission
                if i == 1 and "$WIMTA" not in datastring:
                    i=0
            #print(dataarray)

            ## get systime as UTC
            fdate = datetime.utcnow().strftime("%Y%m%d")
            fyear = datetime.utcnow().strftime("%Y")
            ftime = datetime.utcnow().strftime("%H%M%S")
            fdoy  = datetime.utcnow().strftime("%j")
            fsecs = int(ftime[:2])*3600+int(ftime[2:4])*60+int(ftime[-2:])


            ## pick relevant measurments from output strings
            no_data = -9999
            
            if "$WIMTA" in dataarray[0]:
                tt = float(dataarray[0].split(",")[1])
            else:
                tt = no_data
            if "$WIMHU" in dataarray[1]:
                hh = float(dataarray[1].split(",")[1])
            else:
                hh = no_data
            if "$WIMMB" in dataarray[2]:
                pp = float(dataarray[2].split(",")[3])
            else:
                pp = no_data

            ## define output file name
            # outfile = "WROMY.WSX.D."+str(fdate)
            outfile = f"BW.WROMY.WS{pi_num}.D.{fyear}.{fdoy}"

            ## check if output file for the current day exists
            __checkOutputFile(outpath, outfile)

            ## write formatted string to output file
            msg = f'{fsecs},{fdate},{ftime},{tt},{pp},{hh}'
            msg = [fsecs, fdate, ftime, tt, pp, hh]
            __writeOutput(outpath, outfile, msg)
            #print(msg)
            
        except Exception as e:
            print(e)
            log.logging(f'{datetime.utcnow().strftime("%Y%m%d, %H%M%S")},Some error occurred in {sys.argv[0]}-> terminating')
            print(f"\n -> Error occurred --> terminating {sys.argv[0]}")
            sys.exit(0)


##_____________________________________________________________

if __name__ == "__main__":
    main()

##_____________________________________________________________
# End of File
