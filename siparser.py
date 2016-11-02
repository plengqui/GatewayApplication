from construct import *
from datetime  import datetime, timedelta

class SportidentTimeAdapter(Adapter):
     def _decode(self, obj, context):
         REFERENCE_TIME = None
         #def _decode_time(raw_time, REFERENCE_TIME=None):
         """Decodes a raw time value read from an si card into a datetime object.
         The returned time is the nearest time matching the data before REFERENCE_TIME.
         obj is two bytes TH+TL = number of seconds since noon or midnight"""
         if REFERENCE_TIME is None:
             # Use current time as reference. Add two hours as a safety marging for cases where the
             # machine time runs a bit behind the stations time.
             REFERENCE_TIME = datetime.now() + timedelta(hours=2)
         # punchtime is in the range 0h-12h!
         punchtime = timedelta(seconds=Int16ub.parse(bytes(obj)))
         ref_day = REFERENCE_TIME.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
         ref_hour = REFERENCE_TIME - ref_day
         t_noon = timedelta(hours=12)

         if ref_hour < t_noon:
             # reference time is before noon
             if punchtime < ref_hour:
                 # t is between 00:00 and t_ref
                 return ref_day + punchtime
             else:
                 # t is afternoon the day before
                 return ref_day - t_noon + punchtime
         else:
             # reference is after noon
             if punchtime < ref_hour - t_noon:
                 # t is between noon and t_ref
                 return ref_day + t_noon + punchtime
             else:
                 # t is in the late morning
                 return ref_day + punchtime
SportidentTime = SportidentTimeAdapter(Byte[2])

class SportidentCardAdapter(Adapter):
    def _decode(self, obj, context):
        #TODO verify support for SI series 9 10 11 etc
        """Decodes a 4 byte cardnr (the "obj" parameter) to an int. SI-Card numbering is a bit odd:

           SI-Card 5:
              - byte 0:   always 0 (not stored on the card)
              - byte 1:   card series (stored on the card as CNS)
              - byte 2,3: card number
              - printed:  100'000*CNS + card number
              - nr range: 1-65'000 + 200'001-265'000 + 300'001-365'000 + 400'001-465'000

           SI-Card 6/6*/8/9/10/11/pCard/tCard/fCard/SIAC1:
              - byte 0:   card series (SI6:00, SI9:01, SI8:02, pCard:04, tCard:06, fCard:0E, SI10+SI11+SIAC1:0F)
              - byte 1-3: card number
              - printed:  only card number
              - nr range:
                  - SI6: 500'000-999'999 + 2'003'000-2'003'400 (WM2003) + 16'711'680-16'777'215 (SI6*)
                  - SI9: 1'000'000-1'999'999, SI8: 2'000'000-2'999'999
                  - pCard: 4'000'000-4'999'999, tCard: 6'000'000-6'999'999
                  - SI10: 7'000'000-7'999'999, SIAC1: 8'000'000-8'999'999
                  - SI11: 9'000'000-9'999'999, fCard: 14'000'000-14'999'999

           The card nr ranges guarantee that no ambiguous values are possible
           (500'000 = 0x07A120 > 0x04FFFF = 465'535 = highest technically possible value on a SI5)
        """
        buf=bytes(obj[0:4])
        if buf[0:1] != b'\x00':
            raise ValueError('Unknown card series')

        nr = Int24ub.parse(buf[1:4])
        if nr < 500000:
            # SI5 card
            ret = Int16ub.parse(buf[2:4])
            if buf[1] < 2:
                # Card series 0 and 1 do not have the 0/1 printed on the card
                return ret
            else:
                return buf[1] * 100000 + ret
        else:
            # SI6/8/9
            return nr
SportidentCard = SportidentCardAdapter(Byte[4])

SiPacket=Struct(
    "Wakeup"/Optional(Const(b"\xFF")),
    "Stx"/Const(b"\x02"),
    "Command"/Const(b"\xD3"),#maybe later: add switch to distinguish \xD3 and \x81 if we read backup
    "Len"/Int8ub, #Should be 13 bytes
    "Cn"/Int16ub,
    "SiNr"/SportidentCard,
    "Td"/Int8ub, #weekday, am/pm. Not used. Using reference time instead.
    "ThTl"/SportidentTime, #12h timer in seconds as two bytes
    "Tsubsec"/Int8ub, #1/256 sec
    "Mem"/Int24ub, #Data record start address in backup memory,
    "Crc1"/Int8ub,  #16 bit CRC value, computed including command byte and LEN
    "Crc2"/Int8ub,
    "Etx"/Const(b"\x03")
)

if __name__ == '__main__':
    # When this module is executed from the command-line:
    buf = bytes([255,2, 211, 13, 0, 44, 0, 3, 171, 90, 37, 102, 247, 13, 0, 1, 192, 251, 107, 3])
    d = SiPacket.parse(buf)
    print(d)
        # Wakeup = None
        # Stx = b'\x02'
        # Command = b'\xd3'
        # Len = 13
        # Cn = 44
        # SiNr = 343866
        # Td = 37
        # ThTl = 2016-11-01 19:19:19  (current date)
        # Tsubsec = 13
        # Mem = 448
        # Crc1 = 251
        # Crc2 = 107
        # Etx = b'\x03'

#maybe if possible with srr: implement 0x81 readout backup memory  SI2-SI1-SI0-DATE1-DATE0-TH-TL-MS
#PacketType = Enum(Byte, TransmitRecord=\xD3, BackupData=\x81)
