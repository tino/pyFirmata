import serial
import serial.tools.list_ports

print("Serial devices available:")
l = serial.tools.list_ports.comports()
for ll in l:
    print(ll.device, ll.description)
