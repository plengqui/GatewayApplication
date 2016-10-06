import serial

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

