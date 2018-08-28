import telegram
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import logging
import configparser
import time
import sqlitedb
import parseutils

# Strings
add_ych_str = (
    '*You\'ve added Ych to watchlist.*\nYchID: '
    '#{}\nLink: {}\nLast bid: *{}* - *{}$*'
)
start_str = (
    'Hi! I\'m a bot that does some work for you\n'
    'You can send me link to Ych you want to get updates '
    'about and I will notify you about changes.'
)
stop_str = (
    'Thanks for using this bot. I\'ve cleaned all your subscriptions'
    ', so I won\'t message you anymore. Goodbye.'
)
new_bid_str = '*New bid on Ych #{}.*\nLink: {}\nUser: *{} - {}$*'
ych_fin_str = '*Ych #{} finished.*\nLink: {}\nWinner: *{} - {}$*'
error_str = 'You probably made mistake somewhere'

# Initialisation
logging.basicConfig(
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level = logging.INFO
)
config = configparser.ConfigParser()
config.read('config.ini')
updater = Updater(token=config['bot']['token'])
dispatcher = updater.dispatcher
db = sqlitedb.YchDb(config['bot']['dbpath'])

def reply_to_message(bot, update):
    id = parseutils.get_ychid_by_link(update.message.text)
    if id == 0:
        bot.send_message(
            chat_id = update.message.chat_id,
            text = error_str
        )
        return
    data = parseutils.get_ych_info(id)
    bid, endtime = data["payload"][0], data["auction"]["ends"]
    name, b = bid["name"], float(bid["bid"])
    ychdata = list(
        update.message.chat.id,
        data["id"],
        bid["bid"],
        endtime,
        update.message.text
    )
    db.add_new_ych(ychdata)
    bot.send_message(
        chat_id = update.message.chat_id, 
        text = add_ych_str.format(data["id"],ychdata[4], name, b), 
        parse_mode=telegram.ParseMode.MARKDOWN
    )

def start(bot, update):
    bot.send_message(chat_id = update.message.chat_id, text = start_str)

def stop(bot, update):
    ychs = list(db.get_all_user_watches(update.message.chat.id))
    for y in ychs:
        db.delete_watch(y[0])
    bot.send_message(chat_id = update.message.chat_id, text = stop_str)

# Register Handlers
handlers = list(
    CommandHandler('start', start),
    CommandHandler('stop', stop),
    MessageHandler(Filters.all, reply_to_message)
)
for handler in handlers:
    dispatcher.add_handler(handler)
updater.start_polling()
# updater. Some method for graceful terminate

# ID, Chat.ID, YchID, MaxPrice, EndTime
while True:
    time.sleep(60)
    for val in db.get_all_watches():
        val = list(val)
        newinfo = parseutils.get_ych_info(val[1])
        newbid = newinfo["payload"][0]
        newendtime = newinfo["auction"]["ends"]
        newvals = [val[0], val[1], newbid["bid"], newendtime, val[4]]
        print(newbid["bid"], val[2])
        if float(newbid["bid"]) > val[2]:
            updater.bot.send_message(
                chat_id = val[0],
                text = new_bid_str.format(
                    val[1], 
                    val[4], 
                    newbid["name"], 
                    newbid["bid"]
                ), 
                parse_mode=telegram.ParseMode.MARKDOWN
            )
        db.add_new_ych(newvals)
        if newendtime < newinfo["time"]:
            updater.bot.send_message(
                chat_id = val[0],
                text = ych_fin_str.format(
                    val[1], 
                    val[4], 
                    newbid["name"], 
                    newbid["bid"]
                ), 
                parse_mode=telegram.ParseMode.MARKDOWN
            )
            db.delete_watch(val[1])
        print(val)