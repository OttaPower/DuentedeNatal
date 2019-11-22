# import telepot

# bot = telepot.Bot('678582209:AAGdYnxxV3SkRKzWm8BBR8ur4ozAcozzxQo')
# bot.getMe()
import sys
import asyncio
from functools import reduce
from telepot import glance, message_identifier
import telepot.aio
import telepot.aio.helper
from telepot.aio.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.aio.delegate import (
    per_chat_id, create_open, pave_event_space, include_callback_query_chat_id)
import requests
import json
import random

votes = dict()
draw = []
main_text = []
sent1 = {}
owner = ""

class DuenteBot(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(DuenteBot, self).__init__(*args, **kwargs)
        global votes
        if self.id in votes:
            self._ballot_box, self._keyboard_msg_ident, self._expired_event = votes[self.id]
            self._editor = telepot.aio.helper.Editor(self.bot, self._keyboard_msg_ident) if self._keyboard_msg_ident else None
        else:
            self._ballot_box = None
            self._keyboard_msg_ident = None
            self._editor = None
            self._expired_event = None

    async def on_chat_message(self, msg):
        content_type, chat_type, chat_id = glance(msg)
        
        global owner


        if content_type != 'text':
            print('Not a text message.')
            return

        if msg['text'] == '/comesa':
            owner = msg["from"]["id"]
            await self._init_ballot()

        elif msg['text'] == '/sortia' and msg["from"]["id"] == owner:
            result = self._draw()
            await self._close_ballot()
            await self.sender.sendMessage('jah sortiei e mandei pra voses')
        
        elif msg['text'] == '/sortia' and msg["from"]["id"] != owner:
            await self.sender.sendMessage('soh a pesoa q crio podi sortia')

        else:
            print('Not a command')
            return
        
    def _draw(self):

        copy = draw.copy()

        for user in draw:
            chosen = random.choice(copy)
            while chosen == user:
                chosen = random.choice(copy)
            text = ["vose tirou ", chosen["first_name"]," ", chosen["last_name"]]
            if chosen["username"] != "":
                text.append(" (@" + chosen["username"] + ")")
            data = requests.get(
                'https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}'
                .format(TOKEN, user["id"]
                    , "".join(text))
            ).json()

            copy.remove(chosen)

        return 

    async def _init_ballot(self):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                       InlineKeyboardButton(text='partisipa', callback_data='yes'),
                   ]])
        sent = await self.sender.sendMessage("vamo partisipa do sorteio", reply_markup=keyboard)
        print(sent)

        self._ballot_box = {}
        self._keyboard_msg_ident = message_identifier(sent)
        self._editor = telepot.aio.helper.Editor(self.bot, self._keyboard_msg_ident)


    async def _close_ballot(self):
        self._expired_event = self.scheduler.event_later(1, ('_vote_expired', {'seconds': 1}))
        self.scheduler.cancel(self._expired_event)

        await self._editor.editMessageReplyMarkup(reply_markup=None)

        self._ballot_box = None
        self._keyboard_msg_ident = None
        self._editor = None
        draw = []
        main_text = []
        sent1 = {}
        owner = ""

    async def on_callback_query(self, msg):
        query_id, from_id, query_data = glance(msg, flavor='callback_query')
        global sent1

        if from_id in self._ballot_box:
            await self.bot.answerCallbackQuery(query_id, text='vose ja voto animau')
        else:
            i = False
            while i == False:
                # await self.bot.answerCallbackQuery(query_id, url='t.me/duente_de_natal_bot?start=XXXX')
                data = requests.get(
                    'https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}'
                    .format(TOKEN, from_id, "hm vose ta participano")
                ).json()
    
                if data["ok"] == False: 
                    await self.bot.answerCallbackQuery(query_id, url='t.me/duente_de_natal_bot?start=XXXX')
                    print(data)
                    i = False
                else:
                    i = True

            if i: 
                user = {}

                user["username"] = ""
                user["first_name"] = ""
                user["last_name"] = ""
                user["id"] = None

                try:
                    user["username"] = data["result"]["chat"]["username"]
                    user["last_name"] = data["result"]["chat"]["last_name"]
                except Exception as exception:
                    print(data)

                user["first_name"] = data["result"]["chat"]["first_name"]
                user["id"] = from_id
                copy = ""

                if not draw:
                    if user["username"] != "":
                        main_text.append("pesoas:\n" + "- @" +user["username"] + "\n")
                    else:
                        main_text.append("pesoas:\n" +user["first_name"] + user["last_name"]+ "\n")
                    sent1 = await self.sender.sendMessage("".join(main_text))
                else:
                    if user["username"] != "":
                        main_text.append("- @" + user["username"] + "\n")
                    else:
                        main_text.append("- " +user["first_name"] + user["last_name"]+ "\n")
                    identifier = telepot.message_identifier(sent1)
                    await self.bot.editMessageText(identifier,"".join(main_text))

                draw.append(user)

                await self.bot.answerCallbackQuery(query_id, text='Ok')
                self._ballot_box[from_id] = query_data


    def on_close(self, ex):
        global votes
        if self._ballot_box is None:
            try:
                del votes[self.id]
            except KeyError:
                pass
        else:
            votes[self.id] = (self._ballot_box, self._keyboard_msg_ident, self._expired_event)

        from pprint import pprint
        print('%d closing ...' % self.id)
        pprint(votes)


TOKEN = '903526202:AAHXCqcB34Dqgo8lOb3z5eZ2J_PUCtm1Q9o'

bot = telepot.aio.DelegatorBot(TOKEN, [
    include_callback_query_chat_id(
        pave_event_space())(
            per_chat_id(types=['group', 'supergroup']), create_open, DuenteBot, timeout=10),
])

loop = asyncio.get_event_loop()
loop.create_task(MessageLoop(bot).run_forever())
print('Listening ...')

loop.run_forever()
