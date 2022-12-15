
# Simple urepl like module
# takes care of connecting to wifi or creating your own
# written for the Rapsberry Pi Pico W


import socket
import network
import time
import urepl_config

global ssid
global server_ip
global password
global client_ip
global port


# Default Network to connect using wificonnect()
# Change these settings or use the built in functions
ssid = urepl_config.ssid
password = urepl_config.password
port = 3145
server_ip = '0.0.0.0'
client_ip = '0.0.0.0'


def wificonnect(ssid=ssid,password=password):
    print('Use: like urepl.wificonnect(SSID,Password)')
    print('otherwise uses default global ssid,password')
    global server_ip
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    wlan.active(True)
    wlan.connect(ssid,password)
    while not wlan.isconnected():
        pass
    server_ip = wlan.ifconfig()[0]
    print('Wifi Connected!!')
    print(f'SSID: {ssid}')
    print('Local Ip Address, Subnet Mask, Default Gateway, Listening on...')
    print(wlan.ifconfig())
    return wlan

def wap(pico_ssid = "PicoW",pico_pass = "picopico"):
    global server_ip
    print('Use: like urepl.wap(SSID,Password)')
    print('otherwise uses default Picow,picopico')
    #Create a network and WAP Wireless Access Point
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=pico_ssid,password=pico_pass)
    ap.active(False) #rare instances keep this on
    ap.active(True)
    while ap.active == False:
        pass
    print('Wireless Access Point (WAP) Created!!')
    print(f'SSID: {pico_ssid}')
    print(f'PASSWORD: {pico_pass}')
    print('Local Ip Address, Subnet Mask, Default Gateway, Listening on...')
    server_ip = ap.ifconfig()[0]
    print(ap.ifconfig())

def send(data,client_ip=client_ip,port=port):
    d = b''
    d += data
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    #s.send(d,(client_ip,port))
    print(s)
    s.close

# Akin to input() on normal python
# Will open a UDP socket and wait for a packet
# Will keep code from running 
def receive():
    print('tried')
    global client_ip
    global port
    global server_ip
    print('Use like urepl.receive(server_ip,port)')
    r = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    r.bind((server_ip,port))
    print(f'waiting to receive on {server_ip}:{port}')
    data,addr = r.recvfrom(1024)
    client_ip = addr
    r.close()
    return data

def printdetails():
    global ssid
    global server_ip
    global password
    global client_ip
    global port
    print(f'ssid: {ssid}')
    print(f'server_ip: {server_ip}')
    print(f'client_ip: {client_ip}')
    print(f'port: {port}')
    
def set_client_ip(client):
    global client_ip
    client_ip = client
    print(f'You set the client_ip to: {client_ip}')
    printdetails()

def set_port(p):
    global port
    port = p
    print(f'You set the port to: {port}')
    printdetails()
    

print('--upython mini wifi and repl ish thing--')
print('wificonnect, wap, send, receive, getipaddress, printdetails')
