# Trial-vpn-gathering

Automatically getting a trial vpn account

## :lock: Prepare

After `git clone` in this repo directory:
```bash
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

## :unlock: Gathering

```bash
python get-vpn.py
```

If all test are passed, `credentials.txt` will be created :crystal_ball:

Type `cat credentials.txt` to see them

## :closed_lock_with_key: Setup

[How can I complete a manual OpenVPN setup for Linux (Ubuntu)?](https://www.safervpn.com/support/articles/214083725-How-can-I-complete-a-manual-OpenVPN-setup-for-Linux-Ubuntu-)

---

## :key: Selenium troubleshooting

The WebDriver is really capricious.

So, just try again if you have the `TimeoutException` :ok_hand:
