#!/usr/bin/python
#
# Script to detect if a serial port has been looped back on itself.
# Assumption is that serial Tx and Rx are connected to a distress
# button. The button is normally closed, that is Tx and Rx are normally
# connected. If the button is pressed then the loop is broken.
#
# The serial port os configured with a timeout of 0.2 seconds. if the loop
# is broken then a timeout will occur on a read and the button press detected.
#
# The command takes one command line argument which is the serial device to
# connect to. If the string matches more than one device then the first
# matching device will be used.
#
# The user running the program may need to be in the unix group that has
# rad write access to the serial ports. For some distributions this may
# be the group 'dialout'
#

import serial.tools.list_ports
import serial
import argparse
import sys
import time

# byte to send
BYTE = b'\x55'

# parse arguments for optional device identifier
parser = argparse.ArgumentParser(description="detect serial loopback")
parser.add_argument("serialPort")
args = parser.parse_args()

# try to find device that matches
ports = serial.tools.list_ports.comports()
for p in ports:
    if args.serialPort == p.device:
        device = p.device
        break
    if args.serialPort == p.name:
        device = p.device
        break

# did we find a matching device
try:
    print "Using device", device
except:
    print "No device found, exiting"
    sys.exit(1)

# open device with read timeout enabled
port = serial.Serial(device, 9600, timeout=1)

# write a byte and try to read back, timeout indicates
# open circuit
while True:
    port.write(BYTE)
    i = port.read(1)
    if len(i) == 1 and i == BYTE:
        print "*** Button Pressed ***"
    else:
        print "Button Not Pressed", i

    time.sleep(0.1)

