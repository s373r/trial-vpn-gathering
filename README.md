# trial-vpn-gathering

Automatically getting a trial VPN account


## :lock: Prepare

```
$ git clone https://github.com/s373r/trial-vpn-gathering
$ cd trial-vpn-gathering
$ virtualenv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

## :unlock: Gathering

```
$ python trial-vpn-gathering.py
```

## :closed_lock_with_key: Setup

After gathering credentials you can use a VPN account for a day :clock2:

To install VPN-connections into NetworkManager:

```
$ sudo bash vpn-connections-install.sh
```

Now you can run a VPN-session via the VPN tray icon :crystal_ball:

---

## :key: Selenium troubleshooting

The WebDriver is really capricious.

So, just try again if you have the `TimeoutException` :ok_hand:
