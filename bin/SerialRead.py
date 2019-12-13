import serial
serBarCode = serial.Serial('/dev/ttyS1', 9600, timeout=1)

while True:

    #read data from serial port
    data = serBarCode.readline()

    #if there is smth do smth
    if len(data) >= 1:
        print(dataBarCode.decode("utf-8"))