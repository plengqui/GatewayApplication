from datetime import *
from struct import *
import socket

def buildmsg():    # private static void sendSirapPunch(int chipNo, DateTime punchTime, DateTime zeroTime, int control, TcpClient client)
    chipNo = 778100
    #tested toward ola with zero time 2016-08-20 k08:00
    # 2016-08-20 08:00:00 shows up as 2016-08-20 08:00:00 in OLA
    # 2016-08-20 07:59:59 shows up as 2016-08-20 19:59:59 in OLA (since 07:59:59 is before OLA's zero time!)
    # 2016-08-20 12:00:00 shows up as 2016-08-20 12:00:00 in OLA
    # 2016-08-20 11:59:59 shows up as 2016-08-20 11:59:59 in OLA

    punchTime = datetime(2016,8,20,hour=8,minute=0,second=0)
    print(punchTime)
    zero12h = datetime(punchTime.year,punchTime.month,punchTime.day,12 if (punchTime.hour>11) else 0,0,0)
    #the nearest noon or midnight before the punchTime
    print(zero12h)


    #zeroTime = time(0,0,0
    # )
    control = 44


    # 0=0
    # 1=control

    # 2=0
    # 3 right,4,5,6 left = chipNo
    # 7,8,9,10=0
    # t = number of tenths of seconds between zero12h and punchTime
    # where zero12h is the nearest noon or midnight before the punchTime


    t = (punchTime-zero12h).seconds * 10
    # right 11,12,13,14 left = t
    msg = pack('<BHLLL', 0, control,chipNo,0,t)
    return msg


#write msg to the tcp connection
def send(msg):
    host = '192.168.1.49'
    port = 10001
    mySocket = socket.socket()

    mySocket.connect((host, port))
    mySocket.send(msg)
    #response = mySocket.recv(1024).decode()
    #print('Received from server: ' + response)
    mySocket.close()


if __name__ == '__main__':
    msg = buildmsg()
    send(msg)