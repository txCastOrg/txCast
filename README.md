# txCast

Commandline tool to quickly broadcast signed transactions over tor (at random times to break timing analysis).

## Motivation
When a user broadcasts their transaction through their own node their peers could notice that this transaction is new to the network, and is likely being made by a wallet connected to a particular node.

To minimise this risk users attempting to use bitcoin privately often broadcast their transactions over tor.

Work is ongoing by bitcoin core developers to mitigate this risk by making changes at the p2p level, however until those changes are merged less technical users must resort to downloading and installing the tor browser, finding an explorer with a .onion domain, navigating to the broadcast transaction page, entering their signed transaction and clicking broadcast. 
This is time consuming.
For users making frequent transactions a command-line tool may be useful. 

This tool also randomises the broadcasts of multiple transactions, allowing you to break timing analysis.

**Note: Currently configured for testnet.**
Once reviewed the code will be modified to default to mainnet. To switch to mainnet now, remove `/testnet` from relevant lines.

## Install bitcoin core in testnet
1. Edit your bitcoin.conf to incude
```
testnet=1
[test]
rpcport=18332
rpcuser=username
rpcpassword=password
```
2. Run bitcoin core (it will be in testnet mode, it might take some time to sync)

## Install tor. 
These are the instructions for linux:
1. `sudo apt install tor`
2. `sudo service tor start`
3. Hash a password using `tor --hash-password test` (Don't use the password `test` outside of testing)
4. `sudo nano /etc/tor/torrc`
- Uncomment `ControlPort 9051`
- Enter your password hash `HashedControlPassword 16:00000` <- Change 16:00000 to the output of step 3
5. `sudo service tor stop`
6. `sudo service tor start`

## Get txCast & Install Dependencies
1. Download the repo `git clone https://github.com/txCastOrg/txCast`
2. Install requirements
- `sudo apt install python3-venv python3-pip` to install pip 
- `python3 -m pip install requests` to install [requests](https://2.python-requests.org/en/master/)
- `sudo pip install stem` to install [Stem](https://stem.torproject.org/) to use tor 
- `pip install PySocks` to install [PySocks](https://pypi.org/project/PySocks/) (? Perhaps required? )
3. Run the script with `python3 txCast-stagger.py` (or basic script with python3 txCast.py)

# Python Screenshot (txCast basic)
![](/txCast.png)

# Python Screenshot (txCast Stagger)
![](/txCast_stagger.png)
