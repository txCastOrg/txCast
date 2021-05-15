# txCast Staggered broadcast

import time
import requests
import secrets
import json
import getpass
from datetime import datetime
from datetime import timedelta
from stem import Signal
from stem.control import Controller

tx_list = []
failed_tx_list = []
not_in_mempool_tx_list = []
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
    setup_tor()
    setup_endpoint()
    setup_node()
    build_lists()
    process_all()
    conclude() 

def setup_tor():
    tor_ready = False
    while tor_ready == False:
        configure_tor()
        tor_ready = check_tor()

def setup_endpoint():
    endpoint_ready = False
    while endpoint_ready == False:
        configure_endpoint()
        endpoint_ready = check_endpoint()

def setup_node():
    node_ready = False
    while node_ready == False:
        configure_node()
        node_ready = check_node()
 
def configure_tor():
    while True:
        global tor_password
        tor_password = getpass.getpass(prompt="Enter tor password (set in .torrc): ")
        # Check tor is accessible
        try: 
            renew_tor_ip()
            break
        except:
            print("Could not connect to tor node. Please try again.")
    return

def check_tor():
    print("\n--- Performing tor check ---")
    renew_tor_ip()
    ip_tor = get_ip_tor()
    ip = get_ip()
    print("IP without tor   : " + str(ip))
    print("IP with tor      : " + str(ip_tor))
    if ip != ip_tor:
        tor_ready = True
    else:
        tor_ready = False
    return tor_ready

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

def configure_endpoint():
    while True:
        global endpoint
        print("\n--- Service Selection ---")
        service = input("Enter m for mempool.space / b for blockstream.info then press ENTER: ")
        if service in ("m","M"):
            endpoint = "http://mempoolhqx4isw62xs7abwphsq7ldayuidyx2v2oethdhhj6mlo2r6ad.onion/testnet/api/tx"
            print("Endpoint Set: Mempool.Space | " + endpoint)
            break
        elif service in ("b","B"):
            endpoint = "http://explorerzydxu5ecjrkwceayqybizmpjjznk5izmitf2modhcusuqlid.onion/testnet/api/tx"
            print("Endpoint Set: Blockstream.Info | " + endpoint)
            break
        else:
            print("Input not recognized. Please try again.")
    return    

def check_endpoint():
    #
    # to-do
    #
    # Check endpoint connects rather than it exists?
    try:
        endpoint
        endpoint_ready = True
    except:
        endpoint_ready = False
    return endpoint_ready

def configure_node():
    while True:
        global rpcPort
        global rpcUser
        global rpcPassword
        global host
        global ownNode
        print("\n--- Own Node Config ---")
        ownNode = input("Are you running bitcoind on this machine? Enter Y if yes, n press ENTER: ")
        if ownNode in ("Y","y"):
            ownNode = True
            # Get node info
            print("\nrpcPort defaults:")
            print("     mainnet: 8332")
            print("     testnet: 18332")
            print("     signet:  38332")
            print("     regtest: 18443\n")
            rpcPort = input("Enter bitcoin rpcPort (e.g. 8332): ")
            rpcUser = input("Enter bitcoin rpcUser            : ")
            rpcPassword = getpass.getpass(prompt="Enter bitcoin rpcPassword        : ")
            # Access RPC local server
            serverURL = 'http://' + rpcUser + ':' + rpcPassword + '@localhost:' + str(rpcPort)
            # Using the class defined in the bitcoin_rpc_class.py
            host = RPCHost(serverURL)
            break
        else:
            ownNode = False
            print("Not checking local mempool.")
            break
    return  

def check_node():
    # If using own node, check node is accessible
    if ownNode == True:
        try: 
            host.call('getblockcount')
            node_ready = True
        except:
            print("\nCould not connect to node. Please try again.\n")
            node_ready = False
    # If not using own node, proceed
    else:
        node_ready = True

    return node_ready

def build_lists():
    # Create randomly sorted list of transactions to broadcast:
    get_tx_list()
    print("\nNumber of Signed Transactions Entered: " + str(len(tx_list)))
    secrets.SystemRandom().shuffle(tx_list)

    # Create ordered random times at which to broadcast:
    print("\n--- Set Delay ---")
    while True:
        try:
            user_input_minutes = int(input('Minutes: '))
            #
            # to-do
            #
            # How do cleanly deal with negative values here?
            break
        except ValueError:
            print("Not an integer! Try again.")

    while True:
        try:
            user_input_hours = int(input('Hours  : '))
            break
        except ValueError:
            print("Not an integer! Try again.")
    
    while True:
        try:
            user_input_days = int(input('Days   : '))
            break
        except ValueError:
            print("Not an integer! Try again.")


    start = datetime.now()
    min_delay = timedelta(minutes=0)
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
    print("\n--- txCast Schedule ---")
    for i in range(0, len(tx_list)):
        print("Time: " + str(time_list[i]) + " | tx: " + str(tx_list[i])[:20] + "...")

    return

def get_tx_list():
    global tx_list
    print("\n--- Enter Signed Transactions ---")
    print("Paste signed transaction (CTRL-SHIFT-V) then press ENTER\n")
    finished = False
    while not finished:
        tx_next = input('tx: ')
        if tx_next in ("X","x"):
            finished = True
        else:
            tx_list.append(tx_next)
            print("\nPaste next transaction and press ENTER or Type X then press ENTER to END")
    return

def process_all():
    for i in range(0, len(tx_list)):
        print("")
        result = process_tx(i)
        push_time = result[0]
        inMempool = result[1]
        valid = result[2]

        if valid:
            if ownNode:
                if inMempool == False:
                    print("Transaction " + str(i+1) + "not detected in local mempool")
                    not_in_mempool_tx_list.append(tx_list[i])
                else:
                    print("Transaction seen in local mempool")
            else:
                print("Transaction " + str(i+1) + "pushed to endpoint at " + str(push_time))
        else:
            print("Invalid Transaction: " + tx_list[i])
            failed_tx_list.append(tx_list[i])

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


    if ownNode:
        # Decode txid from raw transaction (using local node)
        try:
            valid = host.call('testmempoolaccept', [next_broadcast_tx])[0]['allowed']    
            txid = host.call('testmempoolaccept', [next_broadcast_tx])[0]['txid']
        except:
            valid = False
        
        if valid:
            push_tx(next_broadcast_tx)
            push_time = datetime.now()
            # Check if transaction has hit mempool
            inMempool = False
            attempts = 0
            while not inMempool and attempts < 10:
                inMempool = check_local_mempool(txid)
                time.sleep(6)
                attempts += 1
                #
                # to-do
                # 
                # What if next time is within 6 seconds?
        else:
            inMempool = False
            push_time = "not pushed"
            
    else:
        push_tx(next_broadcast_tx)
        push_time = datetime.now() 
        inMempool = False

    return push_time, inMempool, valid

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
        # host.call('getrawtransaction', txid)
        host.call('getmempoolentry', txid)
        inMempool = True
    except:
        inMempool = False
    return inMempool

def conclude():
    print("\n############################# TXCAST COMPLETE #############################")
    if failed_tx_list:
        print("\nThe Following transactions were invalid:")
        for tx in failed_tx_list:
            print(tx)
    if not_in_mempool_tx_list:
        print("\nThe Following transactions were broadcast but were not seen in local mempool...")
        for tx in not_in_mempool_tx_list:
            print(tx)

main()
