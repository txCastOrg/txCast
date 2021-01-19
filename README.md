# txCast

Commandline tool to quickly broadcast signed transactions over tor.

Install tor. These are the instructions for linux:
1. `sudo apt install tor`
2. `sudo service tor start`
3. Hash a password using `tor --hash-password test` (Don't use the password `test`)
4. `sudo nano /etc/tor/torrc`
- Uncomment `ControlPort 9051`
- Enter your password hash `HashedControlPassword 16:00000` <- Change 16:00000 to the output of step 3
5. `sudo service tor stop`
6. `sudo service tor start`
7. Set password on line 8 of the txCast.py script to the password you entered in Step 3 (e.g. `password = "test"`)
8. [Download](https://github.com/txCast/txCastOrg/blob/master/txCast.py) the python script
9. Install requirements
- `sudo apt install python3-venv python3-pip` to install pip 
- `python3 -m pip install requests` to install [requests](https://2.python-requests.org/en/master/)
- `sudo pip install stem` to install [Stem](https://stem.torproject.org/) to use tor 
- `pip install PySocks` to install [PySocks](https://pypi.org/project/PySocks/) (? Perhaps required? )
10. Run the script with `python3 txCast.py`

# Python Screenshot
![](/txCast.png)