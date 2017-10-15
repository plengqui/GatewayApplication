"""Defines a parser for Tinymesh radio packets using Construct(http://construct.readthedocs.io/en/latest/) available on pypi(https://pypi.python.org/pypi/construct/).
The Tinymesh packet format is specified in the document	RCXXXX(HP)-TM Data Sheet 1.48
available from https://radiocrafts.com/resources/product-documentation/
"""



from construct import *
from datetime  import datetime

class NodeIdAdapter(Adapter):
     def _encode(self, obj, context):
         return list(map(int, obj.split(":")))
     def _decode(self, obj, context):
         return "{0}:{1}:{2}:{3}".format(*obj)
NodeId = NodeIdAdapter(Byte[4])

class VersionAdapter(Adapter):
     def _encode(self, obj, context):
         return list(map(int, obj.split(".")))
     def _decode(self, obj, context):
         return "{0}.{1}".format(*obj)
Version = VersionAdapter(Byte[2])

PacketType = Enum(Byte, SendCommand=3, SendSerial=17,
                  ReceiveEvent=2, ReceiveSerial=16)
CommandArgument = Enum(Byte, SetOutputs=1, SetPwm=2,SetGwInConfig=3,
                       GetNid=16, GetStatus=17, GetDidStatus=18,
                       GetConfigurationMemory=19, GetCalibrationMemory=20,
                       ForceRouterReset=21, GetPacketPath=22)

CommandData=Struct(
    "Data1"/Int8ub,
    "Data2"/Int8ub)
ConfigRecord=Struct( "address"/Int8ub, "value"/Int8ub)
ConfigData=ConfigRecord[16]
CommandPacket=Struct(
    "Len"/Int8ub,
    "NodeId"/NodeId,
    "CmdNo"/Int8ub,
    "PacketType"/PacketType,
    "CommandArgument"/CommandArgument,
    "Data"/ Switch(this.CommandArgument, {
        "SetGwInConfig":ConfigData,
        "SetPwm":CommandData,
        },default=CommandData)
    )
#--------RECEIVED PACKET FORMATS-----------------
MessageDetail=Enum(Byte,DigitalInputChangeDetected=1,Analogue0InputTrig=2,Analogue1InputTrig=3,RfJammingDetected=6,DeviceReset=8,
                   StatusIma=9, ChannelBusySimilarId=10, ChannelIsFree=11, ChannelIsJammed=12, OtherTmActiveOnChannel=13,
                   Ack=16,Nak=17,StatusNid=18, StatusNextReceiver=19,
                   GetPathResponse=32, ConfigMemoryDump=33)
Hop=Struct("Rssi"/Int8ub,"Node"/NodeId)
EventFooter=Struct(
    "ModuleTemperature"/Int8ub,
    "ModuleVoltage"/Int8ub,
    "DigitalInputs"/Byte,
    "Analogue0"/Int16ub,
    "Analogue1"/Int16ub,
    "HwVersion"/Version,
    "FwVersion"/Version,
    )
MessageData=Struct(
    "MessageDataMsb"/Int8ub,
    "MessageDataLsb"/Int8ub,
    "AddressIdData"/NodeId
    )
EventData=Struct(
    "MessageDetail"/MessageDetail,
    "MessageData"/Switch(this.MessageDetail,{
        "GetPathResponse":Hop[:],
        "ConfigMemoryDump":Int8ub[:],
        "StatusIma":MessageData,

        },default=MessageData),
    "Footer"/IfThenElse(lambda ctx: ctx.MessageDetail in ["DigitalInputChangeDetected","Analogue0InputTrig","Analogue1InputTrig","RfJammingDetected","DeviceReset",
                              "StatusIma", "ChannelBusySimilarId", "ChannelIsFree", "ChannelIsJammed", "OtherTmActiveOnChannel","StatusNid", "StatusNextReceiver"]
       ,EventFooter,Pass)
    )
SerialData=Struct(
    "DataBlockCounter"/Int8ub,
    "SerialData"/Byte[1:120]
    )
ReceivedPacket=Struct(
    "Len"/Int8ub,
    "SystemId"/NodeId,
    "OriginId"/NodeId,
    "OriginRssi"/Int8ub,
    "OriginNetworkLevel"/Int8ub,
    "HopCounter"/Int8ub,
    "MessageCounter"/Int16ub,
    "LatencyCounter"/Int16ub,
    "PacketType"/PacketType,
    "PacketContents"/Switch(this.PacketType,{
        "ReceiveEvent":EventData,
        "ReceiveSerial":SerialData,
        },default=Pass),
    "ReceivedTime"/Computed(lambda ctx: datetime.now())
    )



