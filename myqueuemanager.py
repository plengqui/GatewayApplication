from dirq.QueueSimple import QueueSimple
import os

class MyQueue(QueueSimple):
    """Implement store-and-forward queues for received serial packets using QueueSimple(http://dirq.readthedocs.io/)
    Each packet will be stored in a file in the directories defined below.
    """
    qdirFromSerialPort = "C:\\temp\\tmsi\\port_in"
    qdirFromSerialPortBkp = "C:\\temp\\tmsi\\port_in_backup"
    qdirToSerialPort = "C:\\temp\\tmsi\\port_out"
    def assert_directory_exists(self,directory):
        if not os.path.exists(directory):
            os.makedirs(directory)
    SUBJECT_NETWORKPACKETS_IN = "Tinymesh network packets incoming from serial port"
    SUBJECT_NETWORKPACKETS_OUT = "Tinymesh network packets going out to serial port"

    def __init__(self, subject):
        if subject == self.SUBJECT_NETWORKPACKETS_IN:
            self.assert_directory_exists(MyQueue.qdirFromSerialPort)
            self.assert_directory_exists(MyQueue.qdirFromSerialPortBkp)
            #TODO: add writing to qdirFromSerialPortBkp as well, by overriding add()
            super(MyQueue, self).__init__(MyQueue.qdirFromSerialPort)
        elif subject == self.SUBJECT_NETWORKPACKETS_OUT:
            self.assert_directory_exists(MyQueue.qdirToSerialPort)
            super(MyQueue, self).__init__(MyQueue.qdirToSerialPort)
        #todo else: throw exception


# name = self.dirq.add(buf)
# print("# added element %s" % (name))
# name = self.dirq2.add(buf)
# print("# added backup element %s" % (name))
# print(buf)
