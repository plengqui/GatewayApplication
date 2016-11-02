import serial
#from datetime  import datetime
#from tmparser import *
#from comwrapper import *
from time import sleep
import serial.tools.list_ports
import argparse
from myqueuemanager import MyQueue

    
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
        #self.serial_port.open()
        self.packet_length=0 #0 if we are waiting for a new packet. >0 if we are waiting for a full packet to come into the buffer

        #queue to put received packets to
        self.dirq = MyQueue(subject=MyQueue.SUBJECT_NETWORKPACKETS_IN)


    def exportPacket(self,buf):
        name = self.dirq.add(buf)

    def getPacket(self):
        #read what is in buffer, check that it is feasible
        #chop up according to first byte which is length, or if t
        if(self.packet_length == 0):
            #New packet, if any.
            if(self.serial_port.inWaiting()):
                data = self.serial_port.read(1)
                self.packet_length = data[0]
            else:
                return None
        if(self.serial_port.inWaiting()>=self.packet_length-1):
            data = bytes([self.packet_length]) + self.serial_port.read(self.packet_length-1)
            self.packet_length=0
            return data

        #todo: add else clause with timeout check
        #start a timer when first part of packet is read
        #timeout should be very short, since TM packets should come in one piece from the gateway
        #i,e within length/baudrate seconds.

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
            p.exportPacket(buf)
            print(":",buf,flush=True)
        else:
            #print('.',end='',flush=True)
            sleep(0.01)
            #TODO: look for packets on the serial-packets-to-send dirq

