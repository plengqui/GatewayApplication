
from datetime  import datetime, timedelta
from tmparser import *
from siparser import *
from time import sleep
from myqueuemanager import MyQueue
from collections import deque
from construct.core import ConstructError
from construct.core import FieldError
from construct.core import RangeError
import logging

from datetime import *
from struct import *
import socket


class TinymeshController(object):
    """Check for new Tinymesh packets on the incoming queue SUBJECT_NETWORKPACKETS_IN, and parse them.
    Keep connectivity and health status of each radio using the metadata in each packet.
    The action is driven by external call to process_new_data() at regular intervals (typically seconds).
    Sends any received Sportident punches to competition administration system using SIRAP.
    SIRAP hostname/ip is given as argument to the constructor.
    """

    __singleton_instance = None
    def __new__(cls,hostip):
        if TinymeshController.__singleton_instance is None:
            TinymeshController.__singleton_instance = object.__new__(cls)
            TinymeshController.__singleton_instance.sirap_hostname = hostip
        return TinymeshController.__singleton_instance

    def __init__(self,hostip):
        self.sirap_hostname = hostip
        self.dirq = MyQueue(subject=MyQueue.SUBJECT_NETWORKPACKETS_IN)
        self.radioStatus = {}  # A dictionary of status data for each radio.
        self.serialData = deque([])  # When a packet with serial data payload is received, this is the queue it is put on.
        self.last_purge = datetime.now() # Used to clean up the queue at regular intervals.

    def sirap_buildmsg(self,cn,sinr, punchtime):

        #punchTime = datetime(2016, 8, 20, hour=8, minute=0, second=0)
        logging.debug("Sending SIRAP for %s",punchtime)
        zero12h = datetime(punchtime.year, punchtime.month, punchtime.day, 12 if (punchtime.hour > 11) else 0, 0, 0)
        # the nearest noon or midnight before the punchTime
        logging.debug("Nearset noon/midnight before is %s", zero12h)


        # t = number of tenths of seconds between zero12h and punchTime
        # where zero12h is the nearest noon or midnight before the punchTime

        t = (punchtime - zero12h).seconds * 10

        # bytes of a SIRAP packet:
        # 0=0
        # 1=control
        # 2=0
        # 3 right,4,5,6 left = chipNo
        # 7,8,9,10=0
        # right 11,12,13,14 left = t
        msg = pack('<BHLLL', 0, cn, sinr, 0, t)
        return msg

    # write msg to the tcp connection
    # TODO: put actual SIRAP sending in a separate process, fed by a dirq queue (so we dont miss any punches if tcp fails)
    def sirap_send(self,msg):
        host = self.sirap_hostname
        port = 10001
        mySocket = socket.socket()
        mySocket.connect((host, port))
        sent = mySocket.send(msg)
        logging.info("Sent %i bytes",sent)
        # response = mySocket.recv(1024).decode()
        # print('Received from server: ' + response)
        mySocket.close()

    def process_serial_data(self,data):
        """Attempt to parse the data as a sportident punch. If successful, send with SIRAP and print to gui.
        Otherwise log as error.
        Append a human readable log message with the punch data to serialData.
        Gets called when we have received a TM packet of type serial.
        Arguments:
            data -- list of integers representing bytes of the packet
        """
        if(len(data)!=20):
            logging.warning("Unexpected length of serial packet %s: %s", len(data), data)
        # TODO: check if there are more than one punches in the serial data. Parse all of them.

        buf=bytes(data)
        try:
            punch = SiPacket.parse(buf)
        except (ConstructError, FieldError, RangeError) as e:
            logging.warning("Could not parse serial packet as Sportident punch: %s", data)
        except:
            logging.warning("Unknown exception parsing serial packet as Sportident punch: %s", data)
        else:
            logging.debug("Serial data packet received: %s",punch)
            self.serialData.append("Control=" + str(punch.Cn) + " Card=" + str(punch.SiNr) + " Time=" + punch.ThTl.strftime("%H:%M:%S") + " Memorypos=" + str(punch.Mem))
            #send with SIRAP to OLA:
            self.sirap_send(self.sirap_buildmsg(punch.Cn, punch.SiNr, punch.ThTl))


    def get_serial_data(self):
        """Check if any new Sportident punch has been received. If so, returns it as a human readable message.
        This gets called by the gui.
        """
        if self.serialData:
            return self.serialData.popleft()
        else:
            return None

    #TODO: pick up serial data to send to the radio with given id (for example an acknowledge)
    #TBD: how to send to a given SRR sportident station??



    def process_new_data(self):
        """Check incoming queue for any new packets. Parse them with TM format.
        Update the radioStatus with signal strength and other health data.
        If the packet is a serial payload packet, call process_serial_data() with the serial payload.
        This method gets called regularly by the event loop of the GUI.
        """
        for name in self.dirq:
            if not self.dirq.lock(name):
                continue
            buf = self.dirq.get(name)
            try:
                d=ReceivedPacket.parse(buf)
            except:
            #except (construct.core.ConstructError, construct.core.FieldError, construct.core.RangeError) as e:
                logging.warning("Could not parse TM packet: %s",buf)
            else:
                logging.debug("Received TM packet: %s",d)
                if d.OriginId in self.radioStatus:
                    logging.debug("Previous radio status: %s", self.radioStatus[d.OriginId])
                    if self.radioStatus[d.OriginId]['MessageCounter'] < d.MessageCounter-1:
                        logging.error("Gap in message sequence for radio id %s. Last message was %d, current message is %d",d.OriginId, self.radioStatus[d.OriginId]['MessageCounter'], d.MessageCounter)
                    self.radioStatus[d.OriginId].update({
                        "OriginRssi": d.OriginRssi,
                        "OriginNetworkLevel": d.OriginNetworkLevel,
                        "HopCounter": d.HopCounter,
                        "MessageCounter": d.MessageCounter,
                        "LatencyCounter": d.LatencyCounter,
                        "ReceivedTime": d.ReceivedTime
                        })
                else:
                    self.radioStatus[d.OriginId]={
                        "OriginRssi": d.OriginRssi,
                        "OriginNetworkLevel": d.OriginNetworkLevel,
                        "HopCounter": d.HopCounter,
                        "MessageCounter": d.MessageCounter,
                        "LatencyCounter": d.LatencyCounter,
                        "ReceivedTime": d.ReceivedTime
                        }
                if(d.PacketType=="ReceiveEvent" and d.PacketContents.MessageDetail in ["DigitalInputChangeDetected","Analogue0InputTrig","Analogue1InputTrig","RfJammingDetected","DeviceReset",
                                      "StatusIma", "ChannelBusySimilarId", "ChannelIsFree", "ChannelIsJammed", "OtherTmActiveOnChannel","StatusNid", "StatusNextReceiver"]):
                    #If the packet is of a type that has a footer, save the status data from that.
                    self.radioStatus[d.OriginId].update({
                            "ModuleTemperature": d.PacketContents.Footer.ModuleTemperature,
                            "ModuleVoltage": d.PacketContents.Footer.ModuleVoltage,
                            "DigitalInputs": d.PacketContents.Footer.DigitalInputs,
                            "Analogue0": d.PacketContents.Footer.Analogue0,
                            "Analogue1": d.PacketContents.Footer.Analogue1,
                            "HwVersion": d.PacketContents.Footer.HwVersion,
                            "FwVersion": d.PacketContents.Footer.FwVersion
                            })
                if(d.PacketType=="ReceiveSerial"):
                    self.process_serial_data(d.PacketContents.SerialData)
            self.dirq.remove(name)
            if(datetime.now() - self.last_purge > timedelta(minutes=1)):
                self.dirq.purge() #clean old debris from the queue every 2 minutes
                self.last_purge=datetime.now()
        return self.radioStatus
