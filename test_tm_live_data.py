"""Generate authentic Tinymesh data packets on a serial port.
Intended to be used with a loopback serial port driver such as https://www.eltima.com/virtual-com-port/
"""


from tmparser import *
from time import sleep
import serial

serial_port = serial.serial_for_url( url="COM2",baudrate=19200,
                                          stopbits=1,parity=serial.PARITY_NONE,timeout=1)
with open('live_test_data.txt') as fp:
    for line in fp:
        h=line.strip().split(' ')
        #sleep(0.02)
        n=[int(x,16) for x in h]
        serial_port.write(bytes(n))
        #print(n)
        #d=ReceivedPacket.parse(bytes(n))
        #print(d)

serial_port.close()
