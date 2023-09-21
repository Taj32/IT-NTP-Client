#!/usr/bin/env python

'''
CS352 Assignment 1: Network Time Protocol
You can work with 1 other CS352 student

DO NOT CHANGE ANY OF THE FUNCTION SIGNATURES BELOW
'''

from socket import socket, AF_INET, SOCK_DGRAM
import struct
from datetime import datetime


fs = "!BBBbBBii4sQQQQ" #"!3Bb2B2i4s4Q" 


"""
!: Specifies network byte order (big-endian).
3B -> leap indicator (2 bits), version number (3 bits), and mode (3 bits).
b -> 8-bit integer for the stratum.
2B -> two 8-bit (1-byte) integers for the poll and precision fields.
2i -> two 32-bit (4-byte) integer for root delay & root dispersion.
4s ->  a 32-bit (4-byte) string for reference identifier.
4Q ->  four 64-bit (8-byte)  for reference timestamp, originate timestamp, receive timestamp, and transmit timestamp.

-------

unpack[0]: Leap Indicator (LI) - 8-bit unsigned integer (1 byte).
unpack[1]: Version Number (VN) - 8-bit unsigned integer (1 byte).
unpack[2]: Mode - 8-bit unsigned integer (1 byte).
unpack[3]: Stratum - 8-bit signed integer (1 byte).
unpack[4]: Poll - 8-bit unsigned integer (1 byte).
unpack[5]: Precision - 8-bit unsigned integer (1 byte).
unpack[6]: Root Delay - 32-bit signed integer (4 bytes).
unpack[7]: Root Dispersion - 32-bit unsigned integer (4 bytes).
unpack[8]: Reference Identifier - 32-bit string (4 bytes).
unpack[9]: T2 Timestamp Seconds - 32-bit unsigned integer (4 bytes).
unpack[10]: T2 Timestamp Fraction - 32-bit unsigned integer (4 bytes).
unpack[11]: T3 Timestamp Seconds - 32-bit unsigned integer (4 bytes).
unpack[12]: T3 Timestamp Fraction - 32-bit unsigned integer (4 bytes).
unpack[13]: Reference Timestamp Seconds - 64-bit unsigned integer (8 bytes).
unpack[14]: Reference Timestamp Fraction - 64-bit unsigned integer (8 bytes).
unpack[15]: Originate Timestamp Seconds - 64-bit unsigned integer (8 bytes).
unpack[16]: Originate Timestamp Fraction - 64-bit unsigned integer (8 bytes).
unpack[17]: Receive Timestamp Seconds - 64-bit unsigned integer (8 bytes).
unpack[18]: Receive Timestamp Fraction - 64-bit unsigned integer (8 bytes).
unpack[19]: Transmit Timestamp Seconds - 64-bit unsigned integer (8 bytes).
unpack[20]: Transmit Timestamp Fraction - 64-bit unsigned integer (8 bytes)
"""

#
# 8 bit integer --> B
#"!4c3i4d" #"!cccciii"

"""
Recitation Notes:
- Unix Time will be represented as python floating point number
- NTP uses a fixed-point representation of unitx time, which is a fixed point number
"""

def getNTPTimeValue(server="time.apple.com", port=123) -> (bytes, float, float):
    # add your code here 

    # open socket
    current_socket = socket(socket.AF_INET, socket.SOCK_DGRAM)

    #take a time stamp - t1
    time_difference = datetime.utcnow() - datetime(1970, 1, 1, 0, 0, 0)
    secs = time_difference.days*24.0*60.0*60.0 + time_difference.seconds
    timestamp_float = secs + float(time_difference.microseconds / 1000000.0)

    t1_frac = timestamp_float % 1
    t1_second = timestamp_float - t1_frac
    T1 = t1_frac + t1_second

    # pack t1 into the packet
    pkt = struct.pack(fs, 0, 3, 3, 0,
                              0, 0, 0, 0, b'',
                               t1_frac, t1_second, 
                               0, 0,
                               0, 0, 
                               0, 0)
    

    #send the ntp packet
    current_socket.sendto(pkt, (server, port))

    #wait for the response packet
    # Assume 48 bytes for an NTP response packet
    ntp_response = current_socket.recvfrom(48)  

    # get timestamp t4
    time_difference = datetime.utcnow() - datetime(1970, 1, 1, 0, 0, 0)
    secs = time_difference.days*24.0*60.0*60.0 + time_difference.seconds
    timestamp_float = secs + float(time_difference.microseconds / 1000000.0)

    t4_frac = timestamp_float % 1
    t4_second = timestamp_float - t1_frac
    T4 = t1_frac + t1_second

    # take a timestamp, T1 = current_time
    # send packet to the server,port address
    # receive the response packet
    # take a timestamp, T4 = current_time
    # return a 3-tuple:
    # return (pkt, T1, T4)

    #make sure to close the socket
    current_socket.close()

    return (pkt, T1, T4)


def ntpPktToRTTandOffset(pkt: bytes, T1: float, T4: float) -> (float, float):
    # Define the format string for unpacking the NTP packet
    #fs = "!BBBbBBii4sQQQQ"

    # Check the length of the packet
    packet_length = len(pkt)
    print("Packet length:", packet_length)

    # Unpack the NTP packet
    unpacked_data = struct.unpack(fs, pkt)

    # Concatenate bytes for seconds and fraction parts
    T2_seconds = unpacked_data[9]
    T2_fraction = unpacked_data[10] / 2**32
    T2 = T2_seconds + T2_fraction

    T3_seconds = unpacked_data[11]
    T3_fraction = unpacked_data[12] / 2**32
    T3 = T3_seconds + T3_fraction

    # Calculate RTT and offset
    RTT = (T4 - T1) - (T3 - T4)
    offset = ((T2 - T1) + (T3 - T4)) / 2

    return (RTT, offset)



def getCurrentTime(server="time.apple.com", port=123, iters=20) -> float:
    # add your code here


    #time since 1970..
    time_difference = datetime.utcnow() - datetime(1970, 1, 1, 0, 0, 0)
    secs = time_difference.days *24.0*60.0*60.0 + time_difference.seconds
    timestamp_float = secs + float(time_difference.microseconds / 1000000.0)
    print(timestamp_float)

    #temp = struct.pack(fs, b'a',b'b',b'c', 63,654)

    #print(temp)
    
    return 7 #currentTime



if __name__ == "__main__":

    # sample packet --> test 1 (ntpPkt...)
    ntp_packet_data = b'\x1C\x03\x03\xFA\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x03\x41\x42\x43\x44\xE8\x3C\xCD\x28\x41\x42\x43\x44\xE8\x3C\xCD\x28' + b'\x00' * 18

    T1 = 1234567890.123456  # T1 (before sending request)
    T4 = 1234567890.456789  # T4 (after receiving response)

    result = ntpPktToRTTandOffset(ntp_packet_data, T1, T4)

    print(result)

    # test 2: getNTPTimeValue

    ntp_server = 'pool.ntp.org'
    ntp_port = 123

    result2 = getNTPTimeValue(ntp_server, ntp_port)
    if result2:
        response_packet, T1, T4 = result2
        print("Response Packet:", response_packet)
        print("T1 (Before sending request):", T1)
        print("T4 (After receiving response):", T4)



    
