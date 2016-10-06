import unittest
from tmparser import *
from comwrapper import *
import time

class TestComWrapper(unittest.TestCase):
    def test_SimpleLoopback(self):
        buf=b'\x07foobar' #first byte is packet length
        p=ComWrapper()
        p.putPacket(buf)
#        time.sleep(1)
        buf2=p.getPacket()
        self.assertEqual(buf,buf2)

    def test_DoublePacket(self):
        buf=b'\x07foobar\x07foobar' #two packets at once
        p=ComWrapper()
        p.putPacket(buf)
        p1=p.getPacket()
        p2=p.getPacket()
        self.assertEqual(buf,p1+p2)

    def test_NoInput(self):
        p=ComWrapper()
        received=p.getPacket()
        self.assertEqual(received,None)

    def test_PartialPacket(self):
        buf1=b'\x07foo' #first part
        buf2=b'bar' #first part
        p=ComWrapper()
        p.putPacket(buf1)
        p1=p.getPacket()
        p.putPacket(buf2)
        p2=p.getPacket()
        self.assertEqual(p1,None)
        self.assertEqual(p2,buf1+buf2)

    def test_PartialPacket2(self):
        length=31
        p=ComWrapper()
        p.putPacket(bytes([length]))
        received=[]
        for x in range(5):
            p.putPacket(b'foobar')
            received.append(p.getPacket())
        for x in range(4):
            self.assertEqual(received[x],None)
        self.assertEqual(received[4],b'\x1Ffoobarfoobarfoobarfoobarfoobar')

class TestTmParsing(unittest.TestCase):
    def test_ParseSingleIma(self):
        b='40 1 2 3 4 6 3 3 16 0 23 3 28 2 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0'
        buf=bytes([int(s) for s in b.split(' ')])
        d=CommandPacket.parse(buf)
        self.assertEqual(d.Len, 40, "Wrong Len")


#--------------TEST EVENT PACKET-------------


    def test_SendSetPwmViaCom(self):
        b='10 1 2 3 4 6 3 2 50 0'
        buf=bytes([int(s) for s in b.split(' ')])
        p=ComWrapper()
        p.putPacket(buf)
        buf2=p.getPacket()
        d=CommandPacket.parse(buf)
        self.assertEqual(d.CommandArgument,"SetPwm")
        self.assertEqual(d.Data.Data1,50)
##Container: 
##    Len = 10
##    NodeId = 1:2:3:4
##    CmdNo = 6
##    PacketType = SendCommand
##    CommandArgument = SetPwm
##    Data = Container: 
##        Data1 = 50
##        Data2 = 0


    def test_ConfigMemoryDump(self):
        b='10 0 0 0 1 1 2 3 4 50 3 3 1 0 1 0 2 33 101 102 103'
        buf=bytes([int(s) for s in b.split(' ')])
        d=ReceivedPacket.parse(buf)
        self.assertEqual(d.PacketContents.MessageData[2], 103)
##Container: 
##    Len = 10
##    SystemId = 0:0:0:1
##    OriginId = 1:2:3:4
##    OriginRssi = 50
##    OriginNetworkLevel = 3
##    HopCounter = 3
##    MessageCounter = 256
##    LatencyCounter = 256
##    PacketType = ReceiveEvent
##    PacketContents = Container: 
##        MessageDetail = ConfigMemoryDump
##        MessageData = ListContainer: 
##            101
##            102
##            103
##        Footer = None

    def test_GetPathResponse(self):
        b='10 0 0 0 1 1 2 3 4 50 3 3 1 0 1 0 2 32 50 1 2 3 4 60 1 2 3 5'
        buf=bytes([int(s) for s in b.split(' ')])
        d=ReceivedPacket.parse(buf)
        self.assertEqual(d.PacketContents.MessageData[1].Node, "1:2:3:5")
##Container: 
##    Len = 10
##    SystemId = 0:0:0:1
##    OriginId = 1:2:3:4
##    OriginRssi = 50
##    OriginNetworkLevel = 3
##    HopCounter = 3
##    MessageCounter = 256
##    LatencyCounter = 256
##    PacketType = ReceiveEvent
##    PacketContents = Container: 
##        MessageDetail = GetPathResponse
##        MessageData = ListContainer: 
##            Container: 
##                Rssi = 50
##                Node = 1:2:3:4
##            Container: 
##                Rssi = 60
##                Node = 1:2:3:5
##        Footer = None


    def test_SerialPacket(self):
        b='10 0 0 0 1 1 2 3 4 50 3 3 1 0 1 0 16 6 51 52 53 54 55 56'
        buf=bytes([int(s) for s in b.split(' ')])
        d=ReceivedPacket.parse(buf)
        self.assertEqual(d.PacketContents.SerialData[5], 56)
##Container: 
##    Len = 10
##    SystemId = 0:0:0:1
##    OriginId = 1:2:3:4
##    OriginRssi = 50
##    OriginNetworkLevel = 3
##    HopCounter = 3
##    MessageCounter = 256
##    LatencyCounter = 256
##    PacketType = ReceiveSerial
##    PacketContents = Container: 
##        DataBlockCounter = 6
##        SerialData = ListContainer: 
##            51
##            52
##            53
##            54
##            55
##            56

    def ImaStatusPacket(self):
        b='10 0 0 0 1 1 2 3 4 50 3 3 1 0 1 0 2 9 2 0 1 2 3 5 100 100 0 0 1 1 0 2 0 0 2'
        buf=bytes([int(s) for s in b.split(' ')])
        d=ReceivedPacket.parse(buf)
        self.assertEqual(d.PacketContents.MessageData.AddressIdData,"1:2:3:5")
        self.assertEqual(d.PacketContents.Footer.FwVersion,"0.2")
##Container: 
##    Len = 10
##    SystemId = 0:0:0:1
##    OriginId = 1:2:3:4
##    OriginRssi = 50
##    OriginNetworkLevel = 3
##    HopCounter = 3
##    MessageCounter = 256
##    LatencyCounter = 256
##    PacketType = ReceiveEvent
##    PacketContents = Container: 
##        MessageDetail = StatusIma
##        MessageData = Container: 
##            MessageDataMsb = 2
##            MessageDataLsb = 0
##            AddressIdData = 1:2:3:5
##        Footer = Container: 
##            ModuleTemperature = 100
##            ModuleVoltage = 100
##            DigitalInputs = 0
##            Analogue0 = 1
##            Analogue1 = 256
##            HwVersion = 2.0
##            FwVersion = 0.2
##            ReceivedTime = 21:11:51.669142


#con = Container(Len=10, NodeId="1:2:3:5", CmdNo=6,PacketType='SendCommand',
#                CommandArgument='SetPwm',Data=Container(Data1=50, Data2=0))
#print(CommandPacket.build(con))
#print(con)

#--------------TEST COMMAND PACKET-------------
    def test_SendSetConfig(self):
        b='40 1 2 3 4 6 3 3 16 0 23 3 28 2 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0'
        buf=bytes([int(s) for s in b.split(' ')])
        d=CommandPacket.parse(buf)
        self.assertEqual(d.Data[1].address,23)
        self.assertEqual(d.Data[2].value,2)
##Container: 
##    Len = 40
##    NodeId = 1:2:3:4
##    CmdNo = 6
##    PacketType = SendCommand
##    CommandArgument = SetGwInConfig
##    Data = ListContainer: 
##        Container: 
##            address = 16
##            value = 0
##        Container: 
##            address = 23
##            value = 3
##        Container: 
##            address = 28
##            value = 2
##        Container: 
##            address = 0
##            value = 0

    def test_SendSetPwm(self):
        b='10 1 2 3 4 6 3 2 50 0'
        buf=bytes([int(s) for s in b.split(' ')])
        d=CommandPacket.parse(buf)
        self.assertEqual(d.CommandArgument,"SetPwm")
        self.assertEqual(d.Data.Data1,50)
##Container: 
##    Len = 10
##    NodeId = 1:2:3:4
##    CmdNo = 6
##    PacketType = SendCommand
##    CommandArgument = SetPwm
##    Data = Container: 
##        Data1 = 50
##        Data2 = 0

    def test_BuildCommandSetPwm(self):
        con = Container(Len=10, NodeId="1:2:3:5", CmdNo=6,PacketType='SendCommand',
                        CommandArgument='SetPwm',Data=Container(Data1=50, Data2=0))
        b=CommandPacket.build(con)
        self.assertEqual(b[6],3)
        self.assertEqual(b[9],0)
##b'\n\x01\x02\x03\x05\x06\x03\x022\x00'
##Container: 
##    NodeId = 1:2:3:5
##    CommandArgument = SetPwm
##    CmdNo = 6
##    Len = 10
##    Data = Container: 
##        Data1 = 50
##        Data2 = 0
##    PacketType = SendCommand






if __name__ == '__main__':
    # When this module is executed from the command-line, it runs all its tests
    unittest.main()
