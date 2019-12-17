#!/usr/bin/python
# Script to detect if a serial port has been used as a dry-contact.
# The button is connected to RX and TX (pins 2 and 3).
# It sends constantly the same byte and if received, it will trigger some actions.
# Actions of this script is to enable remote access for the router it is running on with
# Cisco Kinetic GMM, creates a Cisco Webex Team inciddent room, invite some people in it
# and posts the VPN access informations in the room.
#
# This script is provided with no warranty and using it at your own risks.
# Author : Johan Arens - Systems Engineer - Cisco Systems
# joarens@cisco.com - 514-602-1883
#
import requests
import json
import os.path
import serial.tools.list_ports
import serial
import argparse
import sys
import time
import datetime
import socket


if os.path.exists("/VPN-Access-Create.conf"):
    with open("/VPN-Access-Create.conf", 'r') as configFileRead:
        configReadJson = configFileRead.read()
        configFileRead.close()
        configReadJson = json.loads(configReadJson)
        GMM_Key         = configReadJson['GMM-Key']
        GMM_User        = configReadJson['GMM-User']
        GMM_password    = configReadJson['GMM-password']
        WT_Key          = configReadJson['WT-Key']
        configOK = True
else:
    configOK = False

if not configOK:
    PrintThis("No valid config found")
    exit(1)

try:
    if sys.argv[2] is not None:
      if sys.argv[2] == "debug":
        printToConsole=True
      else:
        printToConsole=False
    else:
        printToConsole=False
except:
    printToConsole=False

printToConsole=True


def PrintThis (StringToPrint):
   global printToConsole
   if printToConsole:
      print str(datetime.datetime.now()) + " - " + str(StringToPrint)



def openVPN(routerToConnect):

    global GMM_Key
    global GMM_User
    global GMM_password
    global WT_Key
    url = "https://us.ciscokinetic.io/api/v2/organizations/3178/gate_ways"

    headers = {
        'accept': "application/json",
        'Authorization': "Token " + GMM_Key,
        'cache-control': "no-cache"
        }

    response = requests.request("GET", url, headers=headers)



    data = json.loads(response.text)

    PrintThis ('Getting router id for ' + routerToConnect)
    PrintThis ('Return Code is ' + str(response.status_code))


    for p in data['gate_ways']:
        if p['uuid'] == routerToConnect:
            routerID = str(p['id'])
            routerName = str(p['name'])
            PrintThis ('Router ID is ' + str(routerID))



    url = "https://us.ciscokinetic.io/api/v2/users/access_token"

    payload = "{ \"email\": \"" + GMM_User + "\", \"password\": \"" + GMM_password + "\", \"otp\": \"string\"}"

    headers = {
        'accept': "application/json",
        'Content-Type': "application/json",
        'cache-control': "no-cache"
        }

    response = requests.request("POST", url, data=payload, headers=headers)

    #print(response.text)
    data = json.loads(response.text)
    token = data['access_token']
    PrintThis ('my access token is ' + token)
    PrintThis ('WT token is ' + WT_Key)

    PrintThis ("Getting my ID")
    url = "https://us.ciscokinetic.io/api/v2/users/me"

    headers = {
        'accept': "application/json",
        'Content-Type': "application/json",
        'Authorization': "Token " + token,
        'cache-control': "no-cache"
        }
    response = requests.request("GET", url, headers=headers)
    data = json.loads(response.text)
    myID = str(data['id'])
    PrintThis ('my ID is ' + myID)



    PrintThis ('Validating VPN access')
    url = 'https://us.ciscokinetic.io/api/v2/gate_ways/' + str(routerID) + '/remote_access'

    payload = "{ \"user_id\": \"" + myID + "\", \"duration\": \"60\"}"
    headers = {
        'accept': "application/json",
        'Authorization': "Token " + token,
        'Content-Type': "application/json",
        'cache-control': "no-cache"
        }

    response = requests.request("GET", url, data=payload, headers=headers)
    data =json.loads(response.text)

    if data['remote_access_exists'] == True:
        PrintThis ('VPN Access already exists, reading')
        PrintThis ('Access creation return code ' + str(response.status_code))
    else:
        PrintThis ('VPN Access doens\'t exists, creating')
        response = requests.request("POST", url, data=payload, headers=headers)
        data = json.loads(response.text)
        PrintThis ('Access creation return code ' + str(response.status_code))


    PrintThis ('Duration ' +  str(data['duration']))
    PrintThis ('VPN Access will expired at ' + str(datetime.datetime.fromtimestamp(data['remote_access_expires_at']/1000)))
    PrintThis ('VPN Userid ' + data['remote_access_username'])
    PrintThis ('VPN Password ' + data['remote_access_password'])
    PrintThis ('VPN Acces server ' + data['remote_access_router']['public_dns_name'])

    TextForWT = ["0", "1", "2", "3", "4"]
    TextForWT[0] = 'Duration ' +  str(data['duration'])
    TextForWT[1] = 'VPN Access will expire at ' + str(datetime.datetime.fromtimestamp(data['remote_access_expires_at']/1000))
    TextForWT[2] = 'VPN Userid ' + data['remote_access_username']
    TextForWT[3] = 'VPN Password ' + data['remote_access_password']
    TextForWT[4] = 'VPN Acces server ' + data['remote_access_router']['public_dns_name']

    PrintThis ('Webex Team Room Creation')
    headers = {
        'Content-Type': "application/json",
        'Authorization': "Bearer " + WT_Key
        }

    RoomID = 'empty'
    PrintThis ("Finding Existing Rooms")
    url = 'https://api.ciscospark.com/v1/rooms'
    roomName = "Incident RouterID " + routerID + " - Router name " + routerName
    response = requests.request("GET", url, headers=headers, data=payload)
    if response.status_code == 200:
      data = json.loads(response.text)
      PrintThis ('Room Name ' + roomName)
      for p in data['items']:

          if p['title'] == roomName:
              RoomID = str(p['id'])
              PrintThis ('Room ID is ' + str(RoomID))

    PrintThis ('Room finding return code ' + str(response.status_code))


    if RoomID == 'empty':
        PrintThis ("Creating Room")
        payload  = "{ \"title\": \"" + roomName + "\"}"
        url      = 'https://api.ciscospark.com/v1/rooms'
        response = requests.request("POST", url, headers=headers, data=payload)

        PrintThis("Webex Team Room Creation response " + str(response.status_code))
        if response.status_code == 200:
            data =json.loads(response.text)
            RoomID = data['id']
            PrintThis ('Room ID is ' + RoomID)
        else:
            PrintThis ('Failed to create room')
    else:
        PrintThis ('Room already exists')

    PrintThis ('Adding people to the room')

    url = 'https://api.ciscospark.com/v1/memberships'
    payload  = "{ \"roomId\":\"" + RoomID + "\",\"personEmail\": \"joarens@cisco.com\"}"

    response = requests.request("POST", url, headers=headers, data=payload)
    PrintThis ('Add user response code ' + str(response.status_code))
    if response.status_code == 200:
      data =json.loads(response.text)

    #payload  = "{ \"roomId\":\"" + RoomID + "\",\"personEmail\": \"smignacc@cisco.com\"}"
    #response = requests.request("POST", url, headers=headers, data=payload)

    url = 'https://api.ciscospark.com/v1/messages'
    PrintThis ("Posting VPN access info in Room")
    payload  = "{ \"roomId\": \"" + RoomID + "\",\"text\":\"VPN Access information\"}"
    response = requests.request("POST", url, headers=headers, data=payload)
    for line in TextForWT:
        payload  = "{ \"roomId\": \"" + RoomID + "\",\"text\":\"" + line + " \"}"
        response = requests.request("POST", url, headers=headers, data=payload)

    PrintThis ('Posting in the Room return code ' + str(response.status_code))



#### Main ####

routerToConnect = '829-2lte'

PrintThis ('Running on ' + socket.gethostname())

GosHostname = socket.gethostname()
#GosHostname = 'IR829_FTX2246Z0FF-GOS-1'
GosHostname = GosHostname.replace("-","_",2)
routerToConnect = GosHostname.split('_')[1]
print routerToConnect
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
    print ("Using device", device)
except:
    print ("No device found, exiting")
    sys.exit(1)

# open device with read timeout enabled
port = serial.Serial(device, 9600, timeout=1)
PrintThis('Waiting for events on button connected on ' + device)

# write a byte and try to read back, timeout indicates
# open circuit
buttonPressed = 0
while True:

    port.write(BYTE)
    i = port.read(1)
    #print  len(i) == 1 and i == BYTE and buttonPressed == 0
    if len(i) == 1 and i == BYTE and buttonPressed == 0:
        PrintThis ("*** Button Pressed ***")
        openVPN(routerToConnect)
        # Shun the function for 300 sec
        buttonPressed = int(time.time())
        PrintThis('Shun for 300 sec')
    else:
        if buttonPressed+300 < int(time.time()) and buttonPressed != 0:
            buttonPressed = 0
            PrintThis('Reseting shun timer')
            #PrintThis(str(buttonPressed))
        #else:
            #PrintThis("Button Not Pressed"), i
    #print "apres else"
    if str(round(time.time()) % 10) == '0.0':
        PrintThis('No event detected')
    time.sleep(0.1)
