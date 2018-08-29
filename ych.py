import telegram
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import logging
import configparser
import time
import sqlitedb
import parseutils
import timeutils

class YchBot:
    # Strings
    __add_ych_str = (
        '*You\'ve added Ych to watchlist.*\nYchID: '
        '#{}\nLink: {}\nTime left: *{}*\nLast bid: *{}* - *${}*'
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
    __new_bid_str = (
        '*New bid on Ych #{}.*\nLink: {}\n'
        'Time left: *{}*\nUser: *{} - ${}*'
    )
    __cancel_bid_str = (
        '*Previous bid on Ych #{} has been cancelled.*\n'
        'Link: {}\n\nTime left: *{}*\n*Current bid*\nUser: *{} - {}$*'
    )
    __ych_fin_str = '*Ych #{} finished.*\nLink: {}\nWinner: *{} - ${}*'
    __error_str = 'You probably made mistake somewhere'
    __watchlist_start_str = '*Your watchlist:*'
    __watchlist_watch_str = (
        '*\n{}) Ych #*[{}]({})\nTime left: *{}*\nCurrent bid: *{} - ${}*'
    )
    __delete_str = 'Deleted Ych #{}'
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
        # ych = [Chat.ID, YchID, Name, MaxPrice, EndTime, Link]
        chatid, ychid, oldname, oldbid, _, link = ych
        newinfo = parseutils.get_ych_info(ychid)
        # Getting info about last bid from JSON
        lastbid = newinfo["payload"][0]
        newbid, newname = lastbid["bid"], lastbid["name"]
        # Getting bid end time from JSON
        newendtime = newinfo["auction"]["ends"]
        curtime = newinfo["time"]
        # Setting values for DB
        newvals = [chatid, ychid, newname, newbid, newendtime, link]
        print(newbid, oldbid)
        # Time difference stuff
        remtime = timeutils.get_rdbl_timediff(newendtime)
        # If bid from new JSON in not equal to old bid
        if float(newbid) != oldbid or oldname != newname:
            # Add new info to DB
            self.db.add_new_ych(newvals)
            # Check if bid has been cancelled
            msg = ''
            if float(newbid) >= oldbid:
                msg = self.__new_bid_str
            else:
                msg = self.__cancel_bid_str
            # Send message about new bid(or cancel of prev bid)
            self.updater.bot.send_message(
                chat_id = chatid,
                text = msg.format(
                    ychid, 
                    link, 
                    remtime,
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
            self.db.delete_watch(ychid, chatid)
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
            name,                   # 2: Bidder Name
            bid,                    # 3: Last bid value
            endtime,                # 4: Auction ending time
            ychlink                 # 5: A link to auction
        ]
        # Send data to DB
        self.db.add_new_ych(ychdata)
        # Time difference stuff
        remtime = timeutils.get_rdbl_timediff(endtime)
        # Send message to user
        bot.send_message(
            chat_id = update.message.chat_id, 
            text = self.__add_ych_str.format(ychid, ychlink, remtime, name, bid), 
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
            self.db.delete_watch(y[0], update.message.chat.id) # y[0] - YchID
        bot.send_message(chat_id = update.message.chat_id, text = self.__stop_str)

    def watchlist(self, bot, update):
        message = self.__watchlist_start_str
        ychs = list(self.db.get_all_user_watches(update.message.chat.id))
        for i, ych in enumerate(ychs, start = 1):
            ychid, name, bid, endtime, link  = ych
            # Time difference stuff
            remtime = timeutils.get_rdbl_timediff(endtime)
            # Send a message
            message += self.__watchlist_watch_str.format(
                i,
                ychid,
                link,
                remtime,
                name,
                bid
            )
        bot.send_message(
            chat_id = update.message.chat_id,
            text = message,
            parse_mode=self.__parse_mode
        )

    def delete(self, bot, update, args):
        userid = update.message.chat.id
        try:
            ychid = int(args[0])
        except Exception:
            self.send_err(bot, update)
        else:
            self.db.delete_watch(ychid, userid)
            bot.send_message(
                chat_id = userid,
                text = self.__delete_str.format(ychid),
            )

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
            CommandHandler('list', self.watchlist),
            CommandHandler('del', self.delete, pass_args=True),
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
