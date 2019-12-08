import requests
import json
import os.path

if os.path.exists("../conf/VPN-Access-Create.conf"):
    with open("../conf/VPN-Access-Create.conf", 'r') as configFileRead:
        configReadJson = configFileRead.read()
        configFileRead.close()
        print configReadJson
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


url = "https://us.ciscokinetic.io/api/v2/organizations/3178/gate_ways"
 
headers = {
    'accept': "application/json",
    'Authorization': "Token " + GMM_Key,
    'cache-control': "no-cache"
    }
 
response = requests.request("GET", url, headers=headers)
 
 
 
data = json.loads(response.text)
 
print 'Return Code is ' + str(response.status_code)

print 'Gateways ID'
for p in data['gate_ways']:
  print 'ID ' + str(p['id']) + ' Name ' + p['name']
 
 
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
 
 
 
#url = "https://us.ciscokinetic.io/api/v2/gate_ways/43830/remote_access"
#response = requests.request("GET", url, headers=headers)
#print(response.text)
 
print 'Validating VPN access'
url = 'https://us.ciscokinetic.io/api/v2/gate_ways/43830/remote_access'
 
payload = "{ \"user_id\": \"" + myID + "\", \"duration\": \"1\"}"
headers = {
    'accept': "application/json",
    'Authorization': "Token " + token,
    'Content-Type': "application/json",
    'cache-control': "no-cache"
    }
 
#response = requests.request("POST", url, data=payload, headers=headers)

response = requests.request("POST", url, data=payload, headers=headers)

#print (response.text)
if response.status_code == 200:
  print 'Access is not created yet, creating...'
  print 'Access creation return code ' + str(response.status_code)
else:
  response = requests.request("GET", url, data=payload, headers=headers)
  print 'Access is already created, reading...'
 
 
data = json.loads(response.text)
 
print 'Duration ' +  str(data['duration'])
print 'VPN Userid ' + data['remote_access_username']
print 'VPN Password ' + data['remote_access_password']
print 'VPN Acces server ' + data['remote_access_router']['public_dns_name']
 
