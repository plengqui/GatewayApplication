
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

class TinymeshController(object):
    """Check for new Tinymesh packets on the incoming queue SUBJECT_NETWORKPACKETS_IN, and parse them.
    Keep connectivity and health status of each radio using the metadata in each packet.
    The action is driven by external call to process_new_data() at regular intervals (typically seconds).
    TODO: send any received Sportident punches to competition administration system using SIRAP.
    """

    __singleton_instance = None
    def __new__(cls):
        if TinymeshController.__singleton_instance is None:
            TinymeshController.__singleton_instance = object.__new__(cls)
        #TinymeshController.__singleton_instance.val = val
        return TinymeshController.__singleton_instance

    def __init__(self):
        self.dirq = MyQueue(subject=MyQueue.SUBJECT_NETWORKPACKETS_IN)
        self.radioStatus = {}  # A dictionary of status data for each radio.
        self.serialData = deque([])  # When a packet with serial data payload is received, this is the queue it is put on.
        self.last_purge = datetime.now() # Used to clean up the queue at regular intervals.

    def process_serial_data(self,data):
        """Attempt to parse the data as a sportident punch. If successful, send with SIRAP and print to gui.
        Otherwise log as error.
        Append a human readable log message with the punch data to serialData.
        Gets called when we have received a TM packet of type serial.
        Arguments:
            data -- list of integers representing bytes of the packet
        """
        if(len(data)!=20):
            logging.warning("Unexpected length of serial packet %s", len(data))
        # TODO: check if there are more than one punches in the serial data. Parse all of them.

        buf=bytes(data)
        try:
            punch = SiPacket.parse(buf)
        except (ConstructError, FieldError, RangeError) as e:
            logging.exception("Could not parse serial packet as Sportident punch: %s", data)
        except:
            logging.exception("Exception parsing serial packet as Sportident punch: %s", data)
        else:
            logging.debug("Serial data packet received: %s",punch)
            self.serialData.append("Control=" + str(punch.Cn) + " Card=" + str(punch.SiNr) + " Time=" + punch.ThTl.strftime("%H:%M:%S") + " Memorypos=" + str(punch.Mem))
            # TODO send with SIRAP to OLA
        # private static void sendSirapPunch(int chipNo, DateTime punchTime, DateTime zeroTime, int control, TcpClient client)
        # {
        #     DateTime ZeroTime = new DateTime(DateTime.Now.Year, DateTime.Now.Month, DateTime.Now.Day, 0, 0, 0);
        #     ZeroTime.AddHours(zeroTime.Hour);
        #     ZeroTime.AddMinutes(zeroTime.Minute);
        #     NetworkStream ns = client.GetStream();
        #     byte[] msg = new byte[15];
        #     msg[0] = (byte)0x00;
        #     msg[1] = (byte)control;  // == CSI
        #     msg[2] = 0; // csi hi
        #     msg[3] = (byte)(chipNo & 0xff);
        #     msg[4] = (byte)((chipNo >> 8) & 0xff);
        #     msg[5] = (byte)((chipNo >> 16) & 0xff);
        #     msg[6] = (byte)((chipNo >> 24) & 0xff);
        #     msg[7] = 0;
        #     msg[8] = 0;
        #     msg[9] = 0;
        #     msg[10] = 0;
        #     int time = (int)(punchTime.TimeOfDay.TotalMilliseconds / 100 - ZeroTime.TimeOfDay.TotalMilliseconds / 100);
        #     if (time < 0)
        #         time += 10 * 60 * 60 * 24;
        #     msg[11] = (byte)(time & 0xff);
        #     msg[12] = (byte)((time >> 8) & 0xff);
        #     msg[13] = (byte)((time >> 16) & 0xff);
        #     msg[14] = (byte)((time >> 24) & 0xff);
        #     ns.Write(msg, 0, 15);
        # }

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
                logging.error("Could not parse TM packet: %s",buf)
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
