# txCast Staggered broadcast

import time
import requests
import secrets
import json
from datetime import datetime
from datetime import timedelta
from stem import Signal
from stem.control import Controller

tx_list = []
failed_tx_list = []
time_list = []

class RPCHost(object):
    def __init__(self, url):
        self._session = requests.Session()
        self._url = url
        self._headers = {'content-type': 'application/json'}
    def call(self, rpcMethod, *params):
        payload = json.dumps({"method": rpcMethod, "params": list(params), "jsonrpc": "2.0"})
        tries = 5
        hadConnectionFailures = False
        while True:
            try:
                response = self._session.post(self._url, headers=self._headers, data=payload)
            except requests.exceptions.ConnectionError:
                tries -= 1
                if tries == 0:
                    raise Exception('Failed to connect for remote procedure call.')
                hadFailedConnections = True
                print("Couldn't connect for remote procedure call, will sleep for five seconds and then try again ({} more tries)".format(tries))
                time.sleep(10)
            else:
                if hadConnectionFailures:
                    print('Connected for remote procedure call after retry.')
                break
        if not response.status_code in (200, 500):
            raise Exception('RPC connection failure: ' + str(response.status_code) + ' ' + response.reason)
        responseJSON = response.json()
        if 'error' in responseJSON and responseJSON['error'] != None:
            raise Exception('Error in RPC call: ' + str(responseJSON['error']))
        return responseJSON['result']

def main():
    global tor_password
    tor_password = input("Enter tor password (set in .torrc): ")
    print("--- Performing tor check ---")
    renew_tor_ip()
    ip_tor = get_ip_tor()
    ip = get_ip()
    print("IP without tor: " + str(ip))
    print("IP with tor: " + str(ip_tor))
    if ip != ip_tor:
        print("Success! tor is running")
        set_endpoint()
        set_node()
        build_lists()
        process_all()
        print("")
        print("############################# TXCAST COMPLETE #############################")
    else:
        print("")
        print("Aborted, tor Not Connected")

def renew_tor_ip():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password=tor_password)
        controller.signal(Signal.NEWNYM)
    time.sleep(1) # Wait to ensure a new IP is in use
    # What if next time is within 1 second?

def get_ip_tor():
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
        return ip_tor

def get_ip():
    ip = requests.get('http://httpbin.org/ip').text
    ip = ip.partition('\"origin\": \"')[2]
    ip = ip.rpartition('\"')[0]
    return ip

def set_endpoint():
    global endpoint
    print("--- Service Selection ---")
    service = input("Enter m for mempool.space / b for blockstream.info then press ENTER: ")
    if service == "m" or "M":
        endpoint = "http://mempoolhqx4isw62xs7abwphsq7ldayuidyx2v2oethdhhj6mlo2r6ad.onion/testnet/api/tx"
    elif service == "b" or "B":
        endpoint = "http://explorerzydxu5ecjrkwceayqybizmpjjznk5izmitf2modhcusuqlid.onion/testnet/api/tx"
    else:
        print("Input not recognized")
        set_endpoint()
    return    

def set_node():
    global rpcPort
    global rpcUser
    global rpcPassword
    global host
    global ownNode
    print("--- Own Node Config ---")
    ownNode = input("Are you running bitcoind on this machine? Enter Y if yes, n press ENTER: ")
    if ownNode == "Y" or "y":
        ownNode = True
        # Get node info
        print("rpcPort defaults:")
        print("     mainnet: 8332")
        print("     testnet: 18332")
        print("     signet:  38332")
        print("     regtest: 18443")
        rpcPort = input("Enter bitcoin rpcPort (e.g. 8332): ")
        rpcUser = input("Enter bitcoin rpcUser: ")
        rpcPassword = input("Enter bitcoin rpcPassword: ")
        # Access RPC local server
        serverURL = 'http://' + rpcUser + ':' + rpcPassword + '@localhost:' + str(rpcPort)
        
        # Using the class defined in the bitcoin_rpc_class.py
        host = RPCHost(serverURL)
    else:
        ownNode = False
        print("Download, install and configure bitcoin core.")
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

def process_all():
    for i in range(0, len(tx_list)):
        print("")
        result = process_tx(i)

        if ownNode:
            if result[1] == False:
                print("Transaction " + str(i+1) + "not detected in local mempool")
                failed_tx_list.append(i)
            else:
                print("Transaction seen in local mempool")
        else:
            print("Transaction " + str(i+1) + "pushed to endpoint at " + str(result[0]))
        
        print(str(len(tx_list)-i-1) + " Transactions Remaining")

def process_tx(i):
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

    if ownNode:
        # Decode txid from raw transaction (using local node)
        txid = host.call('decoderawtransaction', next_broadcast_tx)['txid']
        
        # Check if transaction has hit mempool
        inMempool = False
        attempts = 0
        while not inMempool and attempts < 10:
            inMempool = check_local_mempool(txid)
            time.sleep(6)
            attempts += 1
            # What if next time is within 6 seconds?
    else:
       inMempool = False

    return push_time, inMempool

def get_tx_list():
    global tx_list
    print("--- Enter Signed Transactions ---")
    print("Paste signed transaction (CTRL-SHIFT-V) then press ENTER")
    print("")
    finished = False
    while not finished:
        tx_next = input('tx: ')
        if tx_next == "X" or tx_next == "x":
            finished = True
        else:
            tx_list.append(tx_next)
            print("")
            print("Paste next transaction and press ENTER or Type X then press ENTER to END")
    return

def push_tx(payload):
    session = requests.session()

    # TO Request URL with SOCKS over TOR
    session.proxies = {}
    session.proxies['http']='socks5h://localhost:9050'
    session.proxies['https']='socks5h://localhost:9050'

    requests.post(endpoint, data=payload, proxies=session.proxies) 
    print("Transaction Uploaded") 

def check_local_mempool(txid):
    try:
        host.call('getrawtransaction', txid)
        inMempool = True
    except:
        inMempool = False
    return inMempool

main()
