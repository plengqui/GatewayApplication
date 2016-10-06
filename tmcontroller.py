from datetime  import datetime
from tmparser import *
from comwrapper import *
from time import sleep
import serial.tools.list_ports

def processSerialData(data): #list of integers
        buf=bytes(data)
        print(buf)
        sleep(2)

ports=serial.tools.list_ports.comports()
for port in ports: print(port)
p=ComWrapper(port='COM4', port_baud=19200)
buf=''
radioStatus={} #keep a dictionary of dictionaries
while buf != b'\x05exit':
    buf=p.getPacket()
    if(buf != None):
        #print(buf)
        d=ReceivedPacket.parse(buf)
        #print(d)
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
    else:
        print('.',end='')
        sleep(0.8)

    print("Radio","Signal","Since last contact",sep="\t")
    for radioid,status in radioStatus.items():
        print(radioid,
              "{0:.0f}%".format((255-status["OriginRssi"])/2.55),
              datetime.now() - status["ReceivedTime"],sep="\t")

