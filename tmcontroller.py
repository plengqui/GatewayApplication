from datetime  import datetime
from tmparser import *
from time import sleep

def processSerialData(data): #list of integers
        buf=bytes(data)
        print("Serial data:",buf)
        #TODO: send via dirq to Sportident parser
        #TBD: how to include radio id?

#TODO: pick up serial data from sportident parser to send to the radio with given id
#TBD: how to send to a given SRR sportident station??

from dirq.QueueSimple import QueueSimple
import os
qdirFromSerialPort = "C:\\temp\\tmsi\\port_in"
qdirFromSerialPortBkp = "C:\\temp\\tmsi\\port_in_backup"
qdirToSerialPort = "C:\\temp\\tmsi\\port_out"
def assert_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
assert_directory_exists(qdirFromSerialPort)
assert_directory_exists(qdirFromSerialPortBkp)
assert_directory_exists(qdirToSerialPort)


# queue with received packets
dirq = QueueSimple(qdirFromSerialPort)


radioStatus={} #keep a dictionary of dictionaries
while True:
    for name in dirq:
        if not dirq.lock(name):
            continue
        print("# reading element %s" % name)
        buf = dirq.get(name)
        d=ReceivedPacket.parse(buf)

        radioStatus[d.OriginId]={
            "OriginRssi": d.OriginRssi,
            "OriginNetworkLevel": d.OriginNetworkLevel,
            "HopCounter": d.HopCounter,
            "MessageCounter": d.MessageCounter,
            "LatencyCounter": d.LatencyCounter,
            "ReceivedTime": d.ReceivedTime
            }
#        print(d.OriginId,d.MessageCounter, d.PacketType, d.ReceivedTime, d.OriginRssi, sep="\t",end="")
        if(d.PacketType=="ReceiveEvent" and d.PacketContents.MessageDetail in ["DigitalInputChangeDetected","Analogue0InputTrig","Analogue1InputTrig","RfJammingDetected","DeviceReset",
                              "StatusIma", "ChannelBusySimilarId", "ChannelIsFree", "ChannelIsJammed", "OtherTmActiveOnChannel","StatusNid", "StatusNextReceiver"]):
            radioStatus[d.OriginId].update({
                    "ModuleTemperature": d.PacketContents.Footer.ModuleTemperature,
                    "ModuleVoltage": d.PacketContents.Footer.ModuleVoltage,
                    "DigitalInputs": d.PacketContents.Footer.DigitalInputs,
                    "Analogue0": d.PacketContents.Footer.Analogue0,
                    "Analogue1": d.PacketContents.Footer.Analogue1,
                    "HwVersion": d.PacketContents.Footer.HwVersion,
                    "FwVersion": d.PacketContents.Footer.FwVersion
                    })
        if(d.PacketType=="ReceiveSerial"):
            processSerialData(d.PacketContents.SerialData)
        dirq.remove(name)

    print("Radio","Signal","Since last contact",sep="\t")
    for radioid,status in radioStatus.items():
        print(radioid,
              "{0:.0f}%".format((255-status["OriginRssi"])/2.55),
              (datetime.now() - status["ReceivedTime"]).seconds,sep="\t")
    sleep(1)
