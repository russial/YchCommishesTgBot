import requests
from bs4 import BeautifulSoup
from lxml import html
import telegram
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import logging
import configparser
import os.path
import time
import linkutils
import sqlitedb

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
ych_url = 'https://ych.commishes.com/auction/getbids/{}'

# Initialisation
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)

config = configparser.ConfigParser()
config.read('config.ini')
updater = Updater(token=config['bot']['TOKEN'])
dispatcher = updater.dispatcher
db = sqlitedb.YchDb('shorobot.db')

def get_ychid_by_link(url):
    url = url.split('/')
    if len(url) >= 6:
        return linkutils.get_10(url[5])
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
    db.add_new_ych(ychdata)
    bot.send_message(chat_id = update.message.chat_id, text = '*You\'ve added Ych to watchlist.*\nYchID: #{}\nLink: {}\nLast bid: *{}* - *{}$*'.format(data["id"],ychdata[4], name, b), parse_mode=telegram.ParseMode.MARKDOWN)

def start(bot, update):
    bot.send_message(chat_id = update.message.chat_id, text = """Hi! I'm a bot that does some work for you
You can send me link to Ych you want to get updates about and I will notify you about changes.""")

def stop(bot, update):
    ychs = list(db.get_all_user_watches(update.message.chat.id))
    for y in ychs:
        db.delete_watch(y[0])
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
    for val in db.get_all_watches():
        val = list(val)
        newinfo = get_ych_info(val[1])
        newbid = newinfo["payload"][0]
        newendtime = newinfo["auction"]["ends"]
        newvals = [val[0], val[1], newbid["bid"], newendtime, val[4]]
        print(newbid["bid"], val[2])
        if float(newbid["bid"]) > val[2]:
            updater.bot.send_message(chat_id = val[0], text = '*New bid on Ych #{}.*\nLink: {}\nUser: *{} - {}$*'.format(val[1], val[4], newbid["name"], newbid["bid"]), parse_mode=telegram.ParseMode.MARKDOWN)
        db.add_new_ych(newvals)
        if newendtime < newinfo["time"]:
            updater.bot.send_message(chat_id = val[0], text = '*Ych #{} finished.*\nLink: {}\nWinner: *{} - {}$*'.format(val[1], val[4], newbid["name"], newbid["bid"]), parse_mode=telegram.ParseMode.MARKDOWN)
            db.delete_watch(val[1])
        print(val)