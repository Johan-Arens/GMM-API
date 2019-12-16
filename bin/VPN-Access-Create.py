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
from datetime import datetime

if os.path.exists("../conf/VPN-Access-Create.conf"):
    with open("../conf/VPN-Access-Create.conf", 'r') as configFileRead:
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
routerToConnect = '829-2lte'

openVPN ('829-2lte')


def openVPN(routerToConnect):

    url = "https://us.ciscokinetic.io/api/v2/organizations/3178/gate_ways"

    headers = {
        'accept': "application/json",
        'Authorization': "Token " + GMM_Key,
        'cache-control': "no-cache"
        }

    response = requests.request("GET", url, headers=headers)



    data = json.loads(response.text)

    print 'Getting router id for 829-2lte'
    print 'Return Code is ' + str(response.status_code)


    for p in data['gate_ways']:
        if p['name'] == routerToConnect:
            routerID = str(p['id'])
            print 'Router ID is ' + str(routerID)



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
    print 'my access token is ' + token
    print 'WT token is ' + WT_Key

    print "Getting my ID"
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
    print 'my ID is ' + myID



    print 'Validating VPN access'
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
        print 'VPN Access already exists, reading'
        print 'Access creation return code ' + str(response.status_code)
    else:
        print 'VPN Access doens\'t exists, creating'
        response = requests.request("POST", url, data=payload, headers=headers)
        data = json.loads(response.text)
        print 'Access creation return code ' + str(response.status_code)


    print 'Duration ' +  str(data['duration'])
    print 'VPN Access will expired at ' + str(datetime.fromtimestamp(data['remote_access_expires_at']/1000))
    print 'VPN Userid ' + data['remote_access_username']
    print 'VPN Password ' + data['remote_access_password']
    print 'VPN Acces server ' + data['remote_access_router']['public_dns_name']

    TextForWT = ["0", "1", "2", "3", "4"]
    TextForWT[0] = 'Duration ' +  str(data['duration'])
    TextForWT[1] = 'VPN Access will expire at ' + str(datetime.fromtimestamp(data['remote_access_expires_at']/1000))
    TextForWT[2] = 'VPN Userid ' + data['remote_access_username']
    TextForWT[3] = 'VPN Password ' + data['remote_access_password']
    TextForWT[4] = 'VPN Acces server ' + data['remote_access_router']['public_dns_name']

    print 'Webex Team Room Creation'
    headers = {
        'Content-Type': "application/json",
        'Authorization': "Bearer " + WT_Key
        }

    RoomID = 'empty'
    print "Finding Existing Rooms"
    url = 'https://api.ciscospark.com/v1/rooms'
    roomName = "Incident RouterID " + routerID + " - Router name " + routerToConnect
    response = requests.request("GET", url, headers=headers, data=payload)
    if response.status_code == 200:
      data = json.loads(response.text)
      print 'Room Name ' + roomName
      for p in data['items']:

          if p['title'] == roomName:
              RoomID = str(p['id'])
              print 'Room ID is ' + str(RoomID)

    print 'Room finding return code ' + str(response.status_code)


    if RoomID == 'empty':
        print "Creating Room"
        payload  = "{ \"title\": \"" + roomName + "\"}"
        url      = 'https://api.ciscospark.com/v1/rooms'
        response = requests.request("POST", url, headers=headers, data=payload)

        print "Webex Team Room Creation response " + str(response.status_code)
        if response.status_code == 200:
            data =json.loads(response.text)
            RoomID = data['id']
            print 'Room ID is ' + RoomID
        else:
            print 'Failed to create room'
    else:
        print 'Room already exists'

    print 'Adding people to the room'

    url = 'https://api.ciscospark.com/v1/memberships'
    payload  = "{ \"roomId\":\"" + RoomID + "\",\"personEmail\": \"joarens@cisco.com\"}"

    response = requests.request("POST", url, headers=headers, data=payload)
    print 'Add user response code ' + str(response.status_code)
    if response.status_code == 200:
      data =json.loads(response.text)

    #payload  = "{ \"roomId\":\"" + RoomID + "\",\"personEmail\": \"smignacc@cisco.com\"}"
    #response = requests.request("POST", url, headers=headers, data=payload)

    url = 'https://api.ciscospark.com/v1/messages'
    print "Posting VPN access info in Room"
    payload  = "{ \"roomId\": \"" + RoomID + "\",\"text\":\"VPN Access information\"}"
    response = requests.request("POST", url, headers=headers, data=payload)
    for line in TextForWT:
        payload  = "{ \"roomId\": \"" + RoomID + "\",\"text\":\"" + line + " \"}"
        response = requests.request("POST", url, headers=headers, data=payload)

    print 'Posting in the Room return code ' + str(response.status_code)