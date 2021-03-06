import time
import baseutils
import requests

# Using these headers to look like a browser for web-server
headers = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit' 
        '/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    )
}

ych_url = 'https://ych.commishes.com/auction/getbids/{}'

def get_ychid_by_link(url: str) -> int:
    url = url.split('/')
    if len(url) >= 6:
        return baseutils.get_10(url[5])
    return 0

def get_ych_info(id: int) -> list:
    while True:
        try:
            ych_json = requests.get(ych_url.format(id), headers)
            data = ych_json.json()
            break
        except (ConnectionError, ValueError) as e:
            print("Except " + str(e))
            time.sleep(2)
            print("Slept for 2 seconds, trying again")
    data['id'] = id
    return data
