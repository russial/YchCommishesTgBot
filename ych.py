import requests
from bs4 import BeautifulSoup
from lxml import html
import telegram
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import logging
import configparser
import os.path
import sqlite3
import time

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
ych_url = 'https://ych.commishes.com/auction/getbids/{}'

dic32 = '0123456789ABCDEFGHIJKLMNOPQRSTUV'

# Initialisation
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)

config = configparser.ConfigParser()
config.read('config.ini')
updater = Updater(token=config['bot']['TOKEN'])
dispatcher = updater.dispatcher
dbexists = os.path.isfile("shorobot.db")

# Connect to DB
conn = sqlite3.connect("shorobot.db")
cursor = conn.cursor()

# Init DB if not exists
if not dbexists:
    cursor.execute("""
    CREATE TABLE ychs
    (chatid bigint, ychid int, maxprice float, endtime bigint, link varchar,
    PRIMARY KEY (chatid, ychid))
    """)
conn.commit()

def get_32(id):
    rem = list()
    while id > 0:
        rem.append(id % 32)
        id = id // 32
    rem.reverse()
    id32 = ''
    for i in rem:
        id32 += dic32[i]
    return id32

def get_10(id32):
    l = len(id32) - 1
    pos = 0
    id = 0
    for sym in id32:
        i = dic32.find(sym)
        id += i*(32**(l-pos))
        pos += 1
    return id

def add_new_ych_to_db(ychdata):
    conn = sqlite3.connect("shorobot.db")
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO ychs (chatid, ychid, maxprice, endtime, link) VALUES (?,?,?,?,?)
    """, ychdata)
    # TODO: INSERT OR DO NOTHING
    conn.commit()    

def get_all_watched_yches():
    conn = sqlite3.connect("shorobot.db")
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ychs')
    return cursor.fetchall()

def get_all_watched_yches_by_user(id):
    conn = sqlite3.connect("shorobot.db")
    cursor = conn.cursor()
    cursor.execute('SELECT (ychid) FROM ychs WHERE chatid=?', (id,))
    return cursor.fetchall()

def delete_ych(id):
    conn = sqlite3.connect("shorobot.db")
    cursor = conn.cursor()
    cursor.execute('DELETE FROM ychs WHERE ychid = ?', (id,))
    # TODO: INSERT OR DO NOTHING
    conn.commit()    

def get_ychid_by_link(url):
    url = url.split('/')
    if len(url) >= 6:
        return get_10(url[5])
    else:
        return 0

def get_ych_info(id):
    ych_json = requests.get(ych_url.format(id), headers)
    data = ych_json.json()
    data["id"] = id
    return data

def reply_to_message(bot, update):
    id = get_ychid_by_link(update.message.text)
    if id == 0:
        bot.send_message(chat_id = update.message.chat_id, text = "You probably made mistake somewhere")
        return
    data = get_ych_info(id)
    bid, endtime = data["payload"][0], data["auction"]["ends"]
    name, b = bid["name"], float(bid["bid"])
    ychdata=[update.message.chat.id, data["id"], bid["bid"], endtime, update.message.text]
    add_new_ych_to_db(ychdata)
    bot.send_message(chat_id = update.message.chat_id, text = '*You\'ve added Ych to watchlist.*\nYchID: #{}\nLink: {}\nLast bid: *{}* - *{}$*'.format(data["id"],ychdata[4], name, b), parse_mode=telegram.ParseMode.MARKDOWN)

def start(bot, update):
    bot.send_message(chat_id = update.message.chat_id, text = """Hi! I'm a bot that does some work for you
You can send me link to Ych you want to get updates about and I will notify you about changes.""")

def stop(bot, update):
    ychs = list(get_all_watched_yches_by_user(update.message.chat.id))
    for y in ychs:
        delete_ych(y[0])
    bot.send_message(chat_id = update.message.chat_id, text = 'Thanks for using this bot. I\'ve cleaned all your subscriptions, so I won\'t message you anymore. Goodbye.')

# Register Handlers
start_handler = CommandHandler('start', start)
stop_handler = CommandHandler('stop', stop)
echo_handler = MessageHandler(Filters.all, reply_to_message)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(stop_handler)
dispatcher.add_handler(echo_handler)
updater.start_polling()

# ID, Chat.ID, YchID, MaxPrice, EndTime
while True:
    time.sleep(60)
    for val in get_all_watched_yches():
        val = list(val)
        newinfo = get_ych_info(val[1])
        newbid = newinfo["payload"][0]
        newendtime = newinfo["auction"]["ends"]
        newvals = [val[0], val[1], newbid["bid"], newendtime, val[4]]
        print(newbid["bid"], val[2])
        if float(newbid["bid"]) > val[2]:
            updater.bot.send_message(chat_id = val[0], text = '*New bid on Ych #{}.*\nLink: {}\nUser: *{} - {}$*'.format(val[1], val[4], newbid["name"], newbid["bid"]), parse_mode=telegram.ParseMode.MARKDOWN)
        add_new_ych_to_db(newvals)
        if newendtime < newinfo["time"]:
            updater.bot.send_message(chat_id = val[0], text = '*Ych #{} finished.*\nLink: {}\nWinner: *{} - {}$*'.format(val[1], val[4], newbid["name"], newbid["bid"]), parse_mode=telegram.ParseMode.MARKDOWN)
            delete_ych(val[1])
        print(val)