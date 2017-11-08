import time
import serial
from struct import *
import math

# This script is just a quick hack I used to learn the binary format Sportident stations auto-send when a punch is made.
# It uses the "struct" standard python library. Later I chose the more powerful construct library.

# configure the serial connections (the parameters differs on the device you are connecting to):
ser = serial.Serial(
        port='COM14',
        baudrate=9600,
        timeout=3
)
print("B",calcsize("B"))
print("H",calcsize("H"))
print("I",calcsize("I"))
print("BBBHIBHBBHHB",calcsize("<BBBHIBHBBHHB"))

ser.isOpen()


while 1 :
#	ser.write('gobblygoook')
        print("go!")
        # let's wait one second before reading output (let's give device time to answer)
        time.sleep(1)
        while ser.inWaiting() > 0:
                stx,typ,ln,cn,sn,td,t,tss,m2,m10,crc,etc=unpack('>BBBHIBHBBHHB',ser.read(19))
                print("cn",cn,"sn",sn," tid ",math.floor(t/3600),math.floor((t%3600)/60),t%60)
#(2, 211, 13, 32, 778103, 3, 40142, 221, 0, 320, 6732, 3)
#STX, 0xD3, LEN, CN1, CN0, SN3, SN2, SN1, SN0, TD, TH, TL, TSS, MEM2, MEM1, MEM0, CRC1, CRC0, ETX
#LEN 1 byte length byte,0Dh = 13 byte
#CN1, CN0 2 bytes stations code number 1...999
#SN3...SN0 4 bytes SI-Card number
#TD 1 byte day-of-week/half day bit5...bit4 4 week counter relative bit3...bit1 day of week 000b Sunday 001b Monday 010b Tuesday 011b Wednesday 100b Thursday 101b Friday 110b Saturday bit0 24h counter (0-am, 1-pm)
#TH...TL 2 bytes 12h timer, binary
#TSS 1 byte sub second values 1/256 sec
#MEM2...MEM0 3 bytes backup memory start address of the data record
#CRC1, CRC0 2 bytes 16 bit CRC value, computed including command byte and LEN 
