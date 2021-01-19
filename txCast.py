# txCast easy broadcast

import time
import requests
from stem import Signal
from stem.control import Controller

password = "test" # Change this to your tor password
tx = ""
ip = ""
ip_tor = ""

def get_ip():
    global ip
    ip = requests.get('http://httpbin.org/ip').text
    ip = ip.partition('\"origin\": \"')[2]
    ip = ip.rpartition('\"')[0] # Get only IP
    print("IP without tor: " + str(ip))
    return ip

def get_ip_tor():
    global ip_tor
    session = requests.session()

    # TO Request URL with SOCKS over TOR
    session.proxies = {}
    session.proxies['http']='socks5h://localhost:9050'
    session.proxies['https']='socks5h://localhost:9050'

    try:
        ip_tor = session.get('http://httpbin.org/ip').text
        ip_tor = ip_tor.partition('\"origin\": \"')[2]
        ip_tor = ip_tor.rpartition('\"')[0] # Get only IP
    except Exception as e:
        print(str(e))
    else:
        print("IP with tor: " + str(ip_tor))
        return ip_tor

def renew_tor_ip():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password=password)
        controller.signal(Signal.NEWNYM)
    time.sleep(1) # Wait to ensure a new IP is in use

def get_tx():
    global tx
    print("--- Enter Transaction ---")
    tx = input('Paste signed transaction (CTRL-SHIFT-V) then press ENTER: ')
    return

def push_tx(payload):
    session = requests.session()

    # TO Request URL with SOCKS over TOR
    session.proxies = {}
    session.proxies['http']='socks5h://localhost:9050'
    session.proxies['https']='socks5h://localhost:9050'

    requests.post(endpoint, data=payload, proxies=session.proxies) 
    print("Transaction Uploaded") 

def set_endpoint():
    global endpoint
    print("--- Service Selection ---")
    service = input("Enter m for mempool.space / b for blockstream.info then press ENTER: ")
    if service == "m" or "M":
        endpoint = "http://mempoolhqx4isw62xs7abwphsq7ldayuidyx2v2oethdhhj6mlo2r6ad.onion/testnet/api/tx"
    elif service == "b" or "B":
        endpoint = "http://explorerzydxu5ecjrkwceayqybizmpjjznk5izmitf2modhcusuqlid.onion/testnet/api/tx"
    else:
        set_endpoint()
    return    

def main():
    print("--- Performing tor check ---")
    get_ip()
    renew_tor_ip()  # Renew tor IP address
    get_ip_tor()
    if ip != ip_tor:
        print("Success! tor is running")
        set_endpoint()
        get_tx()
        push_tx(tx)
    else:
        print("Aborted, tor Not Connected")

main()
