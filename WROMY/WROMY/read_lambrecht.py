"""
read_lambrecht.py


ROMY wetter aqcuistition script

The output of the Lambrecht THP senors is received as three susequent strings,
which are formatted and written to day files: ./data/BW.WROMY.WS*.D.<year>.<doy>

A logfile is written in ./data/<year>.log

"""
__author__ = 'AndreasBrotzer'
__year__   = '2021'

# updated by Andreas Brotzer | March 2023

##_____________________________________________________________
 

'''---- import libraries ----'''

import sys, serial, csv, subprocess, glob, time
import RPi.GPIO as GPIO

from os import path
from pathlib import Path
from datetime import datetime

##_____________________________________________________________
''' ---- set variables ---- '''

## automatically find connected UBS port
port=subprocess.run(['ls /dev/ttyUSB*'], capture_output=True, shell=True, check=True).stdout.decode()[:-1]

serialport, baudrate = port, 4800
#serialport, baudrate = "/dev/wetter", 4800

## mail to send notification
mail = "brotzer@geophysik.uni-muenchen.de"

## get raspi id
pi_name = subprocess.run(['hostname'], capture_output=True, shell=True, check=True).stdout.decode()
pi_num = int(pi_name[:-1].split("-")[2])

## set initial path for data -> is updated with present year later
outpath = f'/home/pi/WROMY/data/WS{pi_num}.D/{datetime.utcnow().year}/'
logpath = f'/home/pi/WROMY/data/Logfiles/'

## GPIO setup
GPIO.setmode(GPIO.BCM) ## set GPIO name convention
GPIO.setup(23, GPIO.OUT) ## set PIN23 as output

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


## --------------------------------------
def __checkLogFile(outpath, logname):
    
    ## check directory
    if not path.isdir(outpath):
        Path(outpath).mkdir()
        log.logging(f'{datetime.utcnow().strftime("%Y%m%d, %H%M%S")}, created {outpath}')

    ## check file
    if not path.isfile(outpath+logname):
        Path(outpath+logname).touch()
        log.logging(f'{datetime.utcnow().strftime("%Y%m%d, %H%M%S")}, created {outpath}{logname}')

    ## set log object as logfile
    #log = Log(outpath, logname)


## --------------------------------------
def __checkOutputFile(outpath, outfile):

    if not path.isdir(outpath):
        Path(outpath).mkdir()
        __check_LogFile(outpath, logname)

    if not path.isfile(outpath+outfile):

        ## count lines of last file
        #last_file = max(glob.glob(outpath+"/*"), key=path.getctime)
        #out = subprocess.run(['wc -l {}'.format(last_file)], capture_output=True, shell=True, check=True)
        #lines = int(str(out.stdout.decode()).split(" ")[0]) 
            
        ## make new file
        Path(outpath+outfile).touch()

        ## write header to file
        header = ["Seconds", "Date", "Time (UTC)", "Temperature (°C)", "Pressure (hPa)", "rel. Humidity (%)"]
        __writeOutput(outpath, outfile, header)

        ## add entry to logfile
        #log.logging(f'{datetime.utcnow().strftime("%Y%m%d, %H%M%S")},{last_file.split("/")[-1]} contains {lines} lines')
        #log.logging(f'{datetime.utcnow().strftime("%Y%m%d, %H%M%S")},{outfile} has been created')


## --------------------------------------
def __writeOutput(out_path, out_file, msg):

    with open(out_path+out_file, "a") as out:
        writer = csv.writer(out, delimiter=",")
        writer.writerow(msg)
    out.close()


## --------------------------------------
def __updateYear(year, outpath):

    outpath = f"{outpath[:-5]}{year}/"
    logname = f"WROMY_WS{pi_num}_{year}.log"

    __checkLogFile(logpath, logname)

    log = Log(logpath, logname)
    return outpath, logname, log


## --------------------------------------
def __activate_relais():

    GPIO.output(23, GPIO.HIGH)
    time.sleep(1)    
    GPIO.output(23, GPIO.LOW)
    time.sleep(0.1)


## --------------------------------------
def __send_mail(subject, body, mailadress):

    ## send mail via linux mail client
    return_stat = subprocess.run([f"mail", f"-s {subject}", f"{mailadress}"], input=body.encode())



##_____________________________________________________________

def main(outpath):

    ## initalize serial connection
    ser = serial.Serial(port=serialport, baudrate=baudrate)
    ser.flushInput()

    ## initialize log object
    logname = f"WROMY_WS{pi_num}_{datetime.utcnow().strftime('%Y')}.log"
    global log
    log = Log(logpath, logname)

    ## check if log file exits
    __checkLogFile(logpath, logname)

    msg = f'{datetime.utcnow().strftime("%Y%m%d, %H%M%S")}, START: started read_lambrecht.py'
    log.logging(msg)

    while True:


         ## get systime as UTC
        fdate = datetime.utcnow().strftime("%Y%m%d")
        fyear = datetime.utcnow().strftime("%Y")
        ftime = datetime.utcnow().strftime("%H%M%S")
        fdoy  = datetime.utcnow().strftime("%j")
        fsecs = int(ftime[:2])*3600+int(ftime[2:4])*60+int(ftime[-2:])

        ## define output file name
        outfile = f"BW.WROMY.WS{pi_num}.D.{fyear}.{fdoy}"

        ## check if output file for the current day exists
        __checkOutputFile(outpath, outfile)
	    
        ## check if year has changed
        if fyear != outpath[-5:-1]:
            outpath, logname, log = __updateYear(fyear, outpath)


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


        except Exception as e:
            #print(e)

            msg = f'{datetime.utcnow().strftime("%Y%m%d, %H%M%S")}, Exception occurred while reading datastream {sys.argv[0]}'

            ## write error to log
            log.logging(msg)
            
            ## send notification via mail
            __send_mail(f' ERROR: WROMY-{pi_name[-2:]}', msg, mail)


        finally:

            ##check if THP sensor error 999.9 occurs
            if 999.9 in [tt,pp,hh]:
                ## activate relais switch to restet THP sensor
                print(" -> activating relais!")
                __activate_relais()
               
                ## add entry to log file 
                msg = f'{datetime.utcnow().strftime("%Y%m%d, %H%M%S")}, 999.9 Error occurred -> relais activated'
                log.logging(msg)


            ## write formatted string to output file
            msg = f'{fsecs},{fdate},{ftime},{tt},{pp},{hh}'
            msg = [fsecs, fdate, ftime, tt, pp, hh]
            __writeOutput(outpath, outfile, msg)
            #print(outpath, outfile, msg)





##_____________________________________________________________

if __name__ == "__main__":
    main(outpath)


# End of File
