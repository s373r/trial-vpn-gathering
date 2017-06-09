# Trial-vpn-gathering

## :lock: Prepare

In this repo directory:
```bash
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

## :unlock: Gathering:

```bash
python get-vpn.py
```

If all test are pass, `credentials.txt` will be created :crystal_ball:

Type `cat credentials.txt`to see them 


## :key: Selenium troubleshooting:

The WebDriver is really capricious.

So, just try again if you have the "TimeoutException" :ok_hand:
