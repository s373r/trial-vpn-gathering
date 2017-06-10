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
$ python get-vpn.py
```

If all test are passed, `credentials.txt` will be created :crystal_ball:

Type `cat credentials.txt` to see them

## :closed_lock_with_key: Setup

After gathering credentials you can use a VPN account for a day :clock2:

[How can I complete a manual OpenVPN setup for Linux (Ubuntu)?](https://www.safervpn.com/support/articles/214083725-How-can-I-complete-a-manual-OpenVPN-setup-for-Linux-Ubuntu-)

---

## :key: Selenium troubleshooting

The WebDriver is really capricious.

So, just try again if you have the `TimeoutException` :ok_hand:
