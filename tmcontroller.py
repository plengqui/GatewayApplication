from datetime  import datetime, timedelta
from tmparser import *
from siparser import *
from time import sleep
from myqueuemanager import MyQueue
from collections import deque
from construct.core import ConstructError


class TinymeshController(object):

    __singleton_instance = None
    def __new__(cls):
        if TinymeshController.__singleton_instance is None:
            TinymeshController.__singleton_instance = object.__new__(cls)
        #TinymeshController.__singleton_instance.val = val
        return TinymeshController.__singleton_instance

    def process_serial_data(self,data): #data = list of integers
        #This gets called when we have received a TM packet of type serial.
        #Attempt to parse it as a sportident punch. If successful, send with SIRAP and print to gui.
        #Otherwise log as error.
        buf=bytes(data)
        print("Serial data packet:")
        try:
            punch = siparser.SiPacket.parse(buf)
        except:
            # except (construct.core.ConstructError, construct.core.FieldError, construct.core.RangeError) as e:
            print("Could not parse packet: ", data)
        else:
            print(punch)
            #TODO send with SIRAP to OLA
            self.serialData.append("Control=" + punch.Cn + " Card=" + punch.SiNr + " Time=" + ThTl.strftime("%H:%M:%S"))

    def get_serial_data(self):
        #this gets called by the gui to see if any new serial data has been received
        if self.serialData:
            return self.serialData.popleft()
        else:
            return None

    #TODO: pick up serial data to send to the radio with given id (for example an acknowledge)
    #TBD: how to send to a given SRR sportident station??

    def __init__(self):
        self.dirq = MyQueue(subject=MyQueue.SUBJECT_NETWORKPACKETS_IN)
        self.radioStatus = {}  # keep a dictionary of dictionaries
        self.serialData = deque([])
        self.last_purge = datetime.now()


    def process_new_data(self):
        #Check incoming queue for any new packets. Parse them with TM format.
        # Update the radio status with RSSI etc. If serial packet, process the serial data.
        for name in self.dirq:
            if not self.dirq.lock(name):
                continue
            #print("# reading element %s" % name, end="")
            buf = self.dirq.get(name)
            try:
                d=ReceivedPacket.parse(buf)
            except:
            #except (construct.core.ConstructError, construct.core.FieldError, construct.core.RangeError) as e:
                print("Could not parse packet: ",buf)
            else:
                print(d)
                if d.OriginId in self.radioStatus:
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
                #todo: it seems like i am creating a new dictionary, instead of just updating the values that are new
                #tried fixing it by using update() instead. See how that works.
                #print(d.OriginId,d.MessageCounter, d.PacketType, d.ReceivedTime, d.OriginRssi, sep="\t",end="")
                if(d.PacketType=="ReceiveEvent" and d.PacketContents.MessageDetail in ["DigitalInputChangeDetected","Analogue0InputTrig","Analogue1InputTrig","RfJammingDetected","DeviceReset",
                                      "StatusIma", "ChannelBusySimilarId", "ChannelIsFree", "ChannelIsJammed", "OtherTmActiveOnChannel","StatusNid", "StatusNextReceiver"]):
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
