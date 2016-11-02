import serial
#from datetime  import datetime
#from tmparser import *
#from comwrapper import *
from time import sleep
import serial.tools.list_ports
import argparse
from myqueuemanager import MyQueue
import logging

logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s')
logging.info('Started')
logging.warning('%s before you %s', 'Look', 'leap!')
logging.error('I am an error')

class ComWrapper():
    #a serial port wrapper that returns one TM packet at a time.
    #Packet length is always in the first byte.
    def __init__(   self, 
                    port="loop://",
                    port_baud=9600,
                    port_stopbits=serial.STOPBITS_ONE,
                    port_parity=serial.PARITY_NONE,
                    port_timeout=0): #use 0 to get non blocking
        self.serial_port = None
        self.serial_port = serial.serial_for_url( url=port,
                                          baudrate=port_baud,
                                          stopbits=port_stopbits,
                                          parity=port_parity,
                                          timeout=port_timeout)
        #queue to put received packets to
        self.dirq = MyQueue(subject=MyQueue.SUBJECT_NETWORKPACKETS_IN)

    def exportPacket(self,buf):
        name = self.dirq.add(buf)

    def getPacket(self):
        #Read first byte in buffer. Its value should denote the packet length.
        #Try to read so many bytes, with a timeout big enough so that the entire packet
        #has time to arrive at the current baudrate, with a little margin.
        #If no bytes are available to read, return None.
        if(self.serial_port.inWaiting()):
            data = self.serial_port.read(1)
            #todo verify that len(data) == 1
            length = data[0]
            #todo log warning if length is feasible
            self.serial_port.timeout=0.01 + length/(self.serial_port.baudrate/10)
            #timeout so the entire packet has time to arrive at the current baudrate, with 10ms margin
            data = bytes([length]) + self.serial_port.read(length-1)
            return data
        else:
            return None

    def putPacket(self,buf):
        self.serial_port.write(buf)

    def __del__(self):
         if self.serial_port:
             self.serial_port.close()

if __name__ == '__main__':
    # When this module is executed from the command-line:
    print("Serial ports available:")
    ports=serial.tools.list_ports.comports()
    for port in ports: print(port)

    parser = argparse.ArgumentParser()
    parser.add_argument("port", help="The serial port to connect to.")
    parser.add_argument("baudrate", type=int, help="Baud rate to use.")
    args = parser.parse_args()

    p=ComWrapper(port=args.port, port_baud=args.baudrate)

    while True:
        buf=p.getPacket()
        if(buf != None):
            logging.debug("New incoming packet received: %s",buf)
            p.exportPacket(buf)
        else:
            sleep(0.01)
            #TODO: look for any outgoing packets to send (serial-packets-to-send dirq)

