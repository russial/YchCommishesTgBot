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
    __cancel_bid_str = (
        '*Previous bid on Ych #{} has been cancelled.*\n'
        'Link: {}\n\n*Current bid*\nUser: *{} - {}$*'
    )
    __ych_fin_str = '*Ych #{} finished.*\nLink: {}\nWinner: *{} - {}$*'
    __error_str = 'You probably made mistake somewhere'

    # Constants
    __parse_mode = telegram.ParseMode.MARKDOWN

    # Functions
    def update_cycle(self):
        logging.log(logging.INFO, "Started Ych Update Cycle")
        while True:
            for ych in self.db.get_all_watches():
                self.update_ych(list(ych))
            time.sleep(60)            

    # Updates info about single Ych
    def update_ych(self, ych):
        # ych = [Chat.ID, YchID, MaxPrice, EndTime, Link]
        chatid, ychid, oldbid, _, link = ych
        newinfo = parseutils.get_ych_info(ychid)
        # Getting info about last bid from JSON
        lastbid = newinfo["payload"][0]
        newbid, newname = lastbid["bid"], lastbid["name"]
        # Getting bid end time from JSON
        newendtime = newinfo["auction"]["ends"]
        curtime = newinfo["time"]
        # Setting values for DB
        newvals = [chatid, ychid, newbid, newendtime, link]
        print(newbid, oldbid)
        # If bid from new JSON in not equal to old bid
        if float(newbid) != oldbid:
            # Add new info to DB
            self.db.add_new_ych(newvals)
            # Check if bid has been cancelled
            msg = ''
            if float(newbid) > oldbid:
                msg = self.__new_bid_str
            else:
                msg = self.__cancel_bid_str
            # Send message about new bid(or cancel of prev bid)
            self.updater.bot.send_message(
                chat_id = chatid,
                text = msg.format(
                    ychid, 
                    link, 
                    newname, 
                    newbid
                ), 
                parse_mode = self.__parse_mode
            )
        # If auction end time is less than curtime
        if newendtime < curtime:
            # Send message that auction is over
            self.updater.bot.send_message(
                chat_id = chatid,
                text = self.__ych_fin_str.format(
                    ychid, 
                    link, 
                    newname, 
                    newbid
                ), 
                parse_mode = self.__parse_mode
            )
            # Delete from DB
            self.db.delete_watch(YchBot)
        # Log
        logging.log(logging.INFO, "Updated Ych: {}".format(ych))

    # Bot Handlers
    def reply(self, bot, update):
        # User should send us a link to Ych auction
        ychlink = update.message.text
        ychid = parseutils.get_ychid_by_link(ychlink)
        # Parseutils method returns 0 if there was an error. Checking.
        if ychid == 0:
            # Sending Error message
            self.send_err(bot, update)
            return
        # data - JSON
        data = parseutils.get_ych_info(ychid)
        # Getting info from JSON
        last_bid, endtime = data["payload"][0], data["auction"]["ends"]
        name, bid = last_bid["name"], float(last_bid["bid"])
        # Set ychdata array for DB function
        ychdata = [
            update.message.chat.id, # 0: ChatID
            ychid,                  # 1: YchID
            bid,                    # 2: Last bid value
            endtime,                # 3: Auction ending time
            ychlink                 # 4: A link to auction
        ]
        # Send data to DB
        self.db.add_new_ych(ychdata)
        # Send message to user
        bot.send_message(
            chat_id = update.message.chat_id, 
            text = self.__add_ych_str.format(ychid, ychlink, name, bid), 
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
        # Probably there's a need to start these two in different threads
        # self.updater.idle()
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
