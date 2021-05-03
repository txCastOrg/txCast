# txCast Staggered broadcast

import time
import requests
from datetime import datetime
from datetime import timedelta
from stem import Signal
from stem.control import Controller
import secrets

tor_password = "test" # Change this to your tor password
tx_list = []
time_list = []
next_broadcast_time = ""
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
        controller.authenticate(password=tor_password)
        controller.signal(Signal.NEWNYM)
    time.sleep(1) # Wait to ensure a new IP is in use

def fuzz(exact_value, lower_limit_fraction, upper_limit_fraction):
    lower_limit = int(exact_value * lower_limit_fraction)
    upper_limit = int(exact_value * upper_limit_fraction)
    fuzzed_value = exact_value + secrets.SystemRandom().randint(lower_limit, upper_limit)
    return fuzzed_value

def get_tx_list():
    global tx_next
    global tx_list
    finished = False
    print("--- Enter Signed Transactions ---")
    print("Paste signed transaction (CTRL-SHIFT-V) then press ENTER")
    print("")
    while not finished:
        tx_next = input('tx: ')
        if tx_next == "X" or tx_next == "x":
            finished = True
        else:
            tx_list.append(tx_next)
            print("")
            print("Paste next transaction and press ENTER or Type X then press ENTER to END")
    return


def build_lists():
    # Create randomly sorted list of transactions to broadcast:
    get_tx_list()
    print("Number of Signed Transactions Entered: " + str(len(tx_list)))
    secrets.SystemRandom().shuffle(tx_list)

    # Create ordered random times at which to broadcast:
    print("--- Set Delay ---")
    user_input_minutes = int(input('Minutes: '))
    user_input_hours = int(input('Hours: '))
    user_input_days = int(input('Days: '))

    start = datetime.now()
    min_delay = timedelta(minutes=1)
    min_time = start + min_delay

    max_delay = timedelta(minutes=user_input_minutes, hours=user_input_hours, days=user_input_days)
    max_time = min_time + max_delay

    number_of_times = len(tx_list)
    max_duration = max_time - min_time

    for i in range(0, number_of_times):
        random_time = secrets.SystemRandom().uniform(0, 1) * max_duration
        time_list.append(min_time + random_time)

    time_list.sort()

    # Print list of transactions & target broadcast times
    print("--- txCast Schedule ---")
    for i in range(0, len(tx_list)):
        print("Time: " + str(time_list[i]) + " | tx: " + str(tx_list[i])[:20] + "...")

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

def process_tx(i):
    global next_broadcast_time

    renew_tor_ip()  # Renew tor IP address

    # Set broadcast values
    next_broadcast_tx = tx_list[i]
    next_broadcast_time = time_list[i]

    current_time = datetime.now()

    if current_time > next_broadcast_time:
        time_remaining = next_broadcast_time - next_broadcast_time
    else:
        time_remaining = next_broadcast_time - current_time

    time.sleep(time_remaining.total_seconds())
    push_tx(next_broadcast_tx)
    push_time = datetime.now()

    return push_time


def process_all():
    for i in range(0, len(tx_list)):
        print("")
        print("Transaction " + str(i+1) + " broadcast at " + str(process_tx(i)))
        print(str(len(tx_list)-i-1) + " Transactions Remaining")


def main():
    print("--- Performing tor check ---")
    get_ip()
    renew_tor_ip()  # Renew tor IP address
    get_ip_tor()
    if ip != ip_tor:
        print("Success! tor is running")
        set_endpoint()
    else:
        print("Aborted, tor Not Connected")
    build_lists()
    process_all()
    print("")
    print("############################# TXCAST COMPLETE #############################")


main()
