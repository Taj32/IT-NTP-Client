#!/usr/bin/env python

'''
CS352 Assignment 1: Network Time Protocol
You can work with 1 other CS352 student

DO NOT CHANGE ANY OF THE FUNCTION SIGNATURES BELOW
'''

from socket import socket, AF_INET, SOCK_DGRAM
import struct
from datetime import datetime


#fs = "!BBBbBBii4sQQQQ"
fs = "!BBBb11I"


"""
!: Specifies network byte order (big-endian).
3B b -> leap indicator (2 bits), version number (3 bits), and mode (3 bits), 8-bit integer for the stratum, poll and precision fields.
3I -> two 32-bit (4-byte) integer for root delay & root dispersion.
         ->  a 32-bit (4-byte) string for reference identifier.
4B 8I ->  four 64-bit (8-byte)  for reference timestamp, originate timestamp, receive timestamp, and transmit timestamp.

-------

unacounted --- unpack[0]: Leap Indicator (LI) - 8-bit unsigned integer (1 byte).
B - unpack[0]: Version Number (VN) - 8-bit unsigned integer (1 byte).  combined - unpack[1]: Mode - 8-bit unsigned integer (1 byte).
B - unpack[1]: Stratum - 8-bit signed integer (1 byte).
b - unpack[2]: Poll - 8-bit unsigned integer (1 byte).
I - unpack[3]: Precision - 8-bit unsigned integer (1 byte).
I - unpack[4]: Root Delay - 32-bit signed integer (4 bytes).
I - unpack[5]: Root Dispersion - 32-bit unsigned integer (4 bytes).
I - unpack[6]: Reference Identifier - 32-bit string (4 bytes).
I - unpack[7]: Reference Timestamp Seconds - 64-bit unsigned integer (8 bytes). -----
I - unpack[8]: Reference Timestamp Fraction - 64-bit unsigned integer (8 bytes).
I - unpack[9]: Originate Timestamp Seconds - 64-bit unsigned integer (8 bytes). -----
I - unpack[10]: Originate Timestamp Fraction - 64-bit unsigned integer (8 bytes).
I - unpack[11]: Receive Timestamp Seconds - 64-bit unsigned integer (8 bytes). ----- T3
I - unpack[12]: Receive Timestamp Fraction - 64-bit unsigned integer (8 bytes).
I - unpack[13]: Transmit Timestamp Seconds - 64-bit unsigned integer (8 bytes).  ---- T4
I - unpack[14]: Transmit Timestamp Fraction - 64-bit unsigned integer (8 bytes)
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

    # open socket
    server_sock = socket(AF_INET, SOCK_DGRAM)

    #take a time stamp - t1
    time_difference = datetime.utcnow() - datetime(1970, 1, 1, 0, 0, 0)
    secs = time_difference.days*24.0*60.0*60.0 + time_difference.seconds
    timestamp_float = secs + float(time_difference.microseconds / 1000000.0)

    t1_frac = timestamp_float % 1
    t1_frac_i = int(t1_frac)
    t1_second = timestamp_float - t1_frac
    t1_second_i = int(t1_second)
    T1 = t1_frac + t1_second

    transmit_timestamp = (t1_frac_i, t1_second_i)

    # pack t1 into the packet
    ntp_packet = struct.pack('!B', 0x1b) + 39 * b'\0'  # Version and mode, followed by 39 zeros
    ntp_packet += struct.pack('!I', t1_second_i)
    ntp_packet += struct.pack('!I', t1_frac_i)

    #send the ntp packet
    value_sentto = server_sock.sendto(ntp_packet, (server, port))

    #wait for the response packet
    # Assume 48 bytes for an NTP response packet
    pkt, addr = server_sock.recvfrom(48)  

    # get timestamp t4
    time_difference = datetime.utcnow() - datetime(1970, 1, 1, 0, 0, 0)
    secs = time_difference.days*24.0*60.0*60.0 + time_difference.seconds
    timestamp_float = secs + float(time_difference.microseconds / 1000000.0)

    t4_frac = timestamp_float % 1
    t4_second = timestamp_float - t1_frac
    T4 = t1_frac + t1_second

    # take a timestamp, T1 = current_time
    # send packet to the server,port address
    # receive the response packet --- this is the packet
    # take a timestamp, T4 = current_time
    # return a 3-tuple:
    # return (pkt, T1, T4)
    

    #make sure to close the socket
    server_sock.close()

    return (pkt, T1, T4)


def ntpPktToRTTandOffset(pkt: bytes, T1: float, T4: float) -> (float, float):
    # Define the format string for unpacking the NTP packet
    #fs = "!BBBbBBii4sQQQQ"

    # Check the length of the packet
    packet_length = len(pkt)
    #print("Packet length:", packet_length)

    # Unpack the NTP packet
    unpacked_data = struct.unpack(fs, pkt)


    # Concatenate bytes for seconds and fraction parts
    T2_seconds = unpacked_data[11]
    T2_fraction = float(unpacked_data[12]) / 2**32
    # turn T2_fraction into float then divide by 2**32
    #T2_fraction = unpacked_data[12] / 2**32

    #unix time format: unix= NTP - 2208988800
    T2 = T2_seconds + T2_fraction - 2208988800
    print("T2: reference timestamp: ", T2)
       
    T3_seconds = unpacked_data[13]
    T3_fraction = float(unpacked_data[14] ) / 2**32
    T3 = T3_seconds + T3_fraction - 2208988800
    print("T3: Transmission timestamp: ", T3)

    # Calculate RTT-round trip delay and offset-time difference
    RTT = (T4 - T1) - (T3 - T2)
    offset = ((T2 - T1) + (T4 - T3)) / 2

    return (RTT, offset)



def getCurrentTime(server="time.apple.com", port=123, iters=20) -> float:

    #time since 1970..
    time_difference = datetime.utcnow() - datetime(1970, 1, 1, 0, 0, 0)
    secs = time_difference.days *24.0*60.0*60.0 + time_difference.seconds
    timestamp_float = secs + float(time_difference.microseconds / 1000000.0)
    print("current time according to datetime: ", timestamp_float)

    offsets = []
    for _ in range(iters):
        pkt, T1, T4 = getNTPTimeValue()
        RRT, offset = ntpPktToRTTandOffset(pkt, T1, T4)
        offsets.append(offset)

    #syncing 
    currentTime = sum(offsets)/len(offsets) + timestamp_float
    
    return currentTime


if __name__ == "__main__":

   
    # test 2: getNTPTimeValue - test with default server and port
    response_pkt, t1, t4 = getNTPTimeValue()
    print("Default server and port")
    print("T1 sending packet:", t1)
    print("T4 response packet arived:", t4)
    # testing default (ntpPkt...)
    result = ntpPktToRTTandOffset(response_pkt, t1, t4)
    print("DEFAULT: RRT - send request till recieve request  & offset: ", result)

    #testing default get current time
    #currentTime = getCurrentTime()
    #print("current time is: ", currentTime)

    #test 1
    # sample packet --> test 1 (ntpPkt...)
    '''    
    ntp_packet_data = b'\x1C\x03\x03\xFA\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x03\x41\x42\x43\x44\xE8\x3C\xCD\x28\x41\x42\x43\x44\xE8\x3C\xCD\x28' + b'\x00' * 18
    T1 = 1234567890.123456  # T1 (before sending request)
    T4 = 1234567890.456789  # T4 (after receiving response)
    result = ntpPktToRTTandOffset(ntp_packet_data, T1, T4)

    print("RRT - send request till recieve request  & offset: ", result)
    '''

    '''
    ntp_server = 'pool.ntp.org'
    ntp_port = 123

    result2 = getNTPTimeValue(ntp_server, ntp_port)
    if result2:
        response_packet, T1, T4 = result2
        print("Response Packet:", response_packet)
        print("T1 (Before sending request):", T1)
        print("T4 (After receiving response):", T4)
    '''



