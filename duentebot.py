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
# main_text = []
# sent1 = None

class VoteCounter(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(VoteCounter, self).__init__(*args, **kwargs)

        global votes
        if self.id in votes:
            self._ballot_box, self._keyboard_msg_ident, self._expired_event, self._member_count = votes[self.id]
            self._editor = telepot.aio.helper.Editor(self.bot, self._keyboard_msg_ident) if self._keyboard_msg_ident else None
        else:
            self._ballot_box = None
            self._keyboard_msg_ident = None
            self._editor = None
            self._expired_event = None
            self._member_count = None

    async def on_chat_message(self, msg):
        content_type, chat_type, chat_id = glance(msg)

        if content_type != 'text':
            print('Not a text message.')
            return

        if msg['text'] == '/comesa':
            await self._init_ballot()

        elif msg['text'] == '/sortia':
            result = self._draw()
            await self._close_ballot()
            await self.sender.sendMessage('O sorteio foi realizado!')

        else:
            print('Not a command')
            return

            
    def _draw(self):

        copy = draw.copy()

        for user in draw:
            chosen = random.choice(copy)
            while chosen == user:
                chosen = random.choice(copy)
            
            data = requests.get(
                'https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}'
                .format(TOKEN, user["id"]
                    , "vose tirou " + chosen["first_name"] + " " + chosen["last_name"] + " (@" + chosen["username"] + ")")
            ).json()

            copy.remove(chosen)

        return 

    async def _init_ballot(self):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                       InlineKeyboardButton(text='partisipa', callback_data='yes'),
                   ]])
        sent = await self.sender.sendMessage("vamo partisipa do sorteio", reply_markup=keyboard)
        self._member_count = await self.administrator.getChatMembersCount() - 1  # exclude myself, the bot

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

    async def on_callback_query(self, msg):
        query_id, from_id, query_data = glance(msg, flavor='callback_query')

        if from_id in self._ballot_box:
            await self.bot.answerCallbackQuery(query_id, text='vose ja voto animau')
        else:
            data = requests.get(
                'https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}'
                .format(TOKEN, from_id, "hm vose ta participano")
            ).json()

            user = {}

            user["username"] = ""
            user["first_name"] = ""
            user["last_name"] = ""
            user["id"] = None

            try:
                user["username"] = data["result"]["chat"]["username"]
                user["first_name"] = data["result"]["chat"]["first_name"]
                user["last_name"] = data["result"]["chat"]["last_name"]
            except Exception as exception:
                print(exception)

            user["id"] = from_id
            # copy = ""

            # if not draw:
            #     main_text.append("pesoas:\n" + "@" +user["username"] + " ")
            #     sent1 = await self.sender.sendMessage("".join(main_text))
            #     print(sent1)
            # if draw:
            #     main_text.append("@" + user["username"] + " ")
            #     edited = bot.editMessageText(telepot.message_identifier(sent1),"".join(main_text))
            #     sent1 = edited

            # print(main_text)
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
            votes[self.id] = (self._ballot_box, self._keyboard_msg_ident, self._expired_event, self._member_count)

        from pprint import pprint
        print('%d closing ...' % self.id)
        pprint(votes)


TOKEN = '678582209:AAGdYnxxV3SkRKzWm8BBR8ur4ozAcozzxQo'

bot = telepot.aio.DelegatorBot(TOKEN, [
    include_callback_query_chat_id(
        pave_event_space())(
            per_chat_id(types=['group']), create_open, VoteCounter, timeout=10),
])

loop = asyncio.get_event_loop()
loop.create_task(MessageLoop(bot).run_forever())
print('Listening ...')

loop.run_forever()