import serial
import time
import os
import json
import requests



if os.path.exists("../conf/VPN-Access-Create.conf"):
    with open("../conf/VPN-Access-Create.conf", 'r') as configFileRead:
        configReadJson = configFileRead.read()
        configFileRead.close()
        configReadJson = json.loads(configReadJson)
        GMM_Key = configReadJson['GMM-Key']
        GMM_User = configReadJson['GMM-User']
        GMM_password = configReadJson['GMM-password']
        WT_Key = configReadJson['WT-Key']
        configOK = True
else:
    configOK = False

if not configOK:
    PrintThis("No valid config found")
    exit(1)

print 'Webex Team Room Creation'
headers = {
    'Content-Type': "application/json",
    'Authorization': "Bearer " + WT_Key
}
print 'Webex Team Key is ' + WT_Key
RoomID = 'empty'
print "Finding Existing Rooms"
url = 'https://api.ciscospark.com/v1/rooms'
roomName = "Johan Arens Debug Room"
response = requests.request("GET", url, headers=headers)
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
    payload = "{ \"title\": \"" + roomName + "\"}"
    url = 'https://api.ciscospark.com/v1/rooms'
    response = requests.request("POST", url, headers=headers, data=payload)

    print "Webex Team Room Creation response " + str(response.status_code)
    if response.status_code == 200:
        data = json.loads(response.text)
        RoomID = data['id']
        print 'Room ID is ' + RoomID
    else:
        print 'Failed to create room'
else:
    print 'Room already exists'

print 'Adding people to the room'

url = 'https://api.ciscospark.com/v1/memberships'
payload = "{ \"roomId\":\"" + RoomID + "\",\"personEmail\": \"joarens@cisco.com\"}"

response = requests.request("POST", url, headers=headers, data=payload)
print 'Add user response code ' + str(response.status_code)
if response.status_code == 200:
    data = json.loads(response.text)


url = 'https://api.ciscospark.com/v1/messages'
print "Starting Monitoring Serial Port"

with serial.serial_for_url('/dev/ttyUSB0') as s:
    while 1 == 1:
       print s.cts
       time.sleep(1)
       if s.cts:
         payload = "{ \"roomId\": \"" + RoomID + "\",\"text\":\"Button Pressed !\"}"
         response = requests.request("POST", url, headers=headers, data=payload)
         print 'Posting in the Room return code ' + str(response.status_code)
