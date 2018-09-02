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

def get_ychid_by_link(url):
    url = url.split('/')
    if len(url) >= 6:
        return baseutils.get_10(url[5])
    else:
        return 0

def get_ych_info(id):
    while True:
        try:
            ych_json = requests.get(ych_url.format(id), headers)
            break
        except ConnectionError:
            print("Except ConnectionError")
            time.sleep(3)
    data = ych_json.json()
    data['id'] = id
    return data
