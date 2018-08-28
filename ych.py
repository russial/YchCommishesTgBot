import telegram
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import logging
import configparser
import time
import sqlitedb
import parseutils

class YchBot:
    # Strings
    __add_ych_str = (
        '*You\'ve added Ych to watchlist.*\nYchID: '
        '#{}\nLink: {}\nLast bid: *{}* - *{}$*'
    )
    __start_str = (
        'Hi! I\'m a bot that does some work for you\n'
        'You can send me link to Ych you want to get updates '
        'about and I will notify you about changes.'
    )
    __stop_str = (
        'Thanks for using this bot. I\'ve cleaned all your subscriptions'
        ', so I won\'t message you anymore. Goodbye.'
    )
    __new_bid_str = '*New bid on Ych #{}.*\nLink: {}\nUser: *{} - {}$*'
    __ych_fin_str = '*Ych #{} finished.*\nLink: {}\nWinner: *{} - {}$*'
    __error_str = 'You probably made mistake somewhere'

    # Constants

    __parse_mode = telegram.ParseMode.MARKDOWN

    # Functions

    def update_cycle(self):
        # TODO: Refactoring of this function
        while True:
            time.sleep(60)
            for val in self.db.get_all_watches():
                # ID, Chat.ID, YchID, MaxPrice, EndTime
                val = list(val)
                newinfo = parseutils.get_ych_info(val[1])
                newbid = newinfo["payload"][0]
                newendtime = newinfo["auction"]["ends"]
                newvals = [val[0], val[1], newbid["bid"], newendtime, val[4]]
                print(newbid["bid"], val[2])
                if float(newbid["bid"]) > val[2]:
                    self.updater.bot.send_message(
                        chat_id = val[0],
                        text = self.__new_bid_str.format(
                            val[1], 
                            val[4], 
                            newbid["name"], 
                            newbid["bid"]
                        ), 
                        parse_mode=self.__parse_mode
                    )
                self.db.add_new_ych(newvals)
                if newendtime < newinfo["time"]:
                    self.updater.bot.send_message(
                        chat_id = val[0],
                        text = self.__ych_fin_str.format(
                            val[1], 
                            val[4], 
                            newbid["name"], 
                            newbid["bid"]
                        ), 
                        parse_mode=self.__parse_mode
                    )
                    self.db.delete_watch(val[1])
                print(val)

    # Bot Handlers

    def reply(self, bot, update):
        # TODO: Refactoring of this function
        id = parseutils.get_ychid_by_link(update.message.text)
        if id == 0:
            # Sending Error message
            self.send_err(bot, update)
            return
        data = parseutils.get_ych_info(id)
        bid, endtime = data["payload"][0], data["auction"]["ends"]
        name, b = bid["name"], float(bid["bid"])
        ychdata = [
            update.message.chat.id,
            data["id"],
            bid["bid"],
            endtime,
            update.message.text
        ]
        self.db.add_new_ych(ychdata)
        bot.send_message(
            chat_id = update.message.chat_id, 
            text = self.__add_ych_str.format(data["id"],ychdata[4], name, b), 
            parse_mode=self.__parse_mode
        )
    
    def send_err(self, bot, update):
        bot.send_message(
            chat_id = update.message.chat_id,
            text = self.__error_str
        )

    def start(self, bot, update):
        bot.send_message(chat_id = update.message.chat_id, text = self.__start_str)

    def stop(self, bot, update):
        ychs = list(self.db.get_all_user_watches(update.message.chat.id))
        for y in ychs:
            self.db.delete_watch(y[0])
        bot.send_message(chat_id = update.message.chat_id, text = self.__stop_str)

    # Init
    def __init__(self):
        # Initialisation
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.updater = Updater(token=self.config['bot']['token'])
        self.dispatcher = self.updater.dispatcher
        self.db = sqlitedb.YchDb(self.config['bot']['dbpath'])

        # Register Handlers
        self.handlers = [
            CommandHandler('start', self.start),
            CommandHandler('stop', self.stop),
            MessageHandler(Filters.all, self.reply)
        ]
        for handler in self.handlers:
            self.dispatcher.add_handler(handler)
        
    # Run function
    def run(self):
        # Start polling 
        self.updater.start_polling()
        # Waiting for graceful terminate
        self.updater.idle()
        # Start update cycle
        self.update_cycle()

# If running as main function
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level = logging.INFO
    )

    # Creating Bot instance and running it
    ych = YchBot()
    ych.run()
