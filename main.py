from bs4 import BeautifulSoup as bs
import requests
import json
import re
import telebot
from telebot import types
import time
from datetime import datetime
import os
from server import server

API_KEY = os.environ.get('API_KEY')
CHATID = os.environ.get('CHATID')

headers = {
    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    }

bot = telebot.TeleBot(API_KEY)
server()

def get_suggestions(word):
    url = 'https://www.almaany.com/suggest.php?term={}&lang=arabic&t=d'.format(word)
    r = requests.get(url, headers=headers)
    suggestions = []
    if r.status_code == 200:
        soup = bs(r.content, features='lxml')
        data = soup.text
        parsed_json = json.loads(data)
        results_counter = len(parsed_json)
        for x in range(results_counter):
            suggestions.append(parsed_json[x])
        return suggestions

def get_markup(suggestions):
        markup = types.InlineKeyboardMarkup()
        count = 0
        for suggestion in suggestions:
            markup.add(types.InlineKeyboardButton(text=suggestion, callback_data='Maany' + suggestion), row_width=8)
            count += 1
        markup.add(types.InlineKeyboardButton(text='إغلاق', callback_data='close'), row_width=8)
        return markup
    
def add_dict_markup(markup, selected_word):
        maany_btn = types.InlineKeyboardButton(text='المعاني الجامع', callback_data='Maany' + selected_word)
        mokhtar_btn = types.InlineKeyboardButton(text='مختار الصحاح', callback_data='Mokhtar' + selected_word)
        waseet_btn = types.InlineKeyboardButton(text='المعجم الوسيط', callback_data='Waseet' + selected_word)
        moaaser_btn = types.InlineKeyboardButton(text='العربيّة المعاصر', callback_data='Moaaser' + selected_word)
        ghani_btn = types.InlineKeyboardButton(text='الغني', callback_data='AlGhani' + selected_word)
        moheet_btn = types.InlineKeyboardButton(text='القاموس المحيط', callback_data='Moheet' + selected_word)
        markup.row(waseet_btn, mokhtar_btn, maany_btn)
        markup.row(moheet_btn, ghani_btn, moaaser_btn)
        markup.row(types.InlineKeyboardButton(text='إغلاق', callback_data='close_arrow'))
        return markup


def get_maany(selected_word: str) -> []:
        url = 'https://www.almaany.com/ar/dict/ar-ar/{}/'.format(selected_word)
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            soup = bs(r.content, features='lxml')
            maany_raw = soup.find("ol", class_=re.compile("^meaning$|results"))
            pattern = re.compile('^<span id="w$|\d{3,7}+')
            res = pattern.findall(str(maany_raw))
            maany_fixed = str(maany_raw)
            REPLACEMENTS = []
            for x in res:
                x_set = ('<span id="w{}">'.format(str(x)), "@*")
                REPLACEMENTS.append(x_set)
            for old, new in REPLACEMENTS:
                maany_fixed = maany_fixed.replace(old, new)
            maany_fixed = maany_fixed.replace('</li>', '\n')
            convert = bs(maany_fixed, features='lxml')
            maany = convert.text.strip()
            maany_list = maany.split("@*")
            maany_list.pop(0)
            return maany_list
            
def get_maany_else(url: str) -> []:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            soup = bs(r.content, features='lxml')
            maany_raw = soup.find("ol", class_=re.compile("^meaning$|results"))
            maany_fixed = str(maany_raw).replace("<span><b>", "@*")
            maany_fixed = maany_fixed.replace('<br/>', '\n')
            convert = bs(maany_fixed, features='lxml')
            maany = convert.text.strip()
            maany_list = []
            maany_list = maany.split("@*")
            maany_list.pop(0)
            return maany_list

def chat(message):
    userId = message.chat.id
    nameUser = str(message.chat.first_name) + ' ' + str(message.chat.last_name)
    username = message.chat.username
    text = message.text
    date = datetime.now()
    data = f'User id: {userId}\nUsername: @{username}\nName: {nameUser}\nText: {text}\nDate: {date}'
    bot.send_message(chat_id=CHATID, text=data)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_chat_action(message.chat.id, action='typing')
    chat(message)
    smsg = "بوت المعاني يعمل!\nأرسل كلمة لأبحث عن معناها في ستّة قواميس عربيّة."
    bot.reply_to(message, smsg)
    
@bot.message_handler(commands=['contact'])
def contact(message):
    bot.send_chat_action(message.chat.id, action='typing')
    chat(message)
    smsg = "تواصل مع صانع البوت للإبلاغ عن خطأ أو اقتراح فكرة جديدة:\n@TheAtef\nhttps://t.me/TheAtef"
    bot.reply_to(message, smsg, disable_web_page_preview=True)

@bot.message_handler(commands=['donate'])
def donate(message):
    chat(message)
    bot.send_chat_action(message.chat.id, action='typing')
    smsg = "شكراً لدعمك!\nhttps://www.buymeacoffee.com/TheAtef"
    bot.reply_to(message, smsg, disable_web_page_preview=True)     

@bot.message_handler(commands=None)
def reply(message):
    bot.send_chat_action(message.chat.id, action='typing')
    suggestions = get_suggestions(message.text)
    markup = get_markup(suggestions)
    bot.send_message(message.chat.id, 'اختر الكلمة:', reply_markup=markup, reply_to_message_id=message.message_id)

@bot.callback_query_handler(func=lambda call: True)
def callback_data(call):
    global counter
    global selected_word
    print(call.data)
    def sender(maany_list: []):
            global counter
            global maany__list
            maany__list = maany_list
            counter = 0
            max_counter = len(maany_list)
            maana_text = str(counter + 1) + "- " + maany_list[counter].strip()
            counter += 1
            markup = types.InlineKeyboardMarkup()       
            if(max_counter > 1):
                markup.row(types.InlineKeyboardButton(text='➡️', callback_data='right'))
            markup = add_dict_markup(markup, selected_word)
            bot.edit_message_text(maana_text, call.message.chat.id, call.message.message_id, reply_markup=markup)

    if call.message:
        if call.data == 'close':
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

        if call.data == 'close_arrow':
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

        if re.match('^Maany', call.data):
            selected_word = call.data.replace('Maany','')
            sender(get_maany(selected_word))

        if re.match('^Mokhtar', call.data):
            selected_word = call.data.replace('Mokhtar','')
            url = 'https://www.almaany.com/ar/dict/ar-ar/{}/?c=مختار%20الصحاح'.format(selected_word)
            sender(get_maany_else(url))
            
        if re.match('^Waseet', call.data):
            selected_word = call.data.replace('Waseet','')
            url = 'https://www.almaany.com/ar/dict/ar-ar/{}/?c=المعجم%20الوسيط'.format(selected_word)
            sender(get_maany_else(url))

        if re.match('^Moaaser', call.data):
            selected_word = call.data.replace('Moaaser','')
            url = 'https://www.almaany.com/ar/dict/ar-ar/{}/?c=اللغة%20العربية%20المعاصر'.format(selected_word)
            sender(get_maany_else(url))

        if re.match('^AlGhani', call.data):
            selected_word = call.data.replace('AlGhani','')
            url = 'https://www.almaany.com/ar/dict/ar-ar/{}/?c=الغني'.format(selected_word)
            sender(get_maany_else(url))

        if re.match('^Moheet', call.data):
            selected_word = call.data.replace('Moheet','')
            url = 'https://www.almaany.com/ar/dict/ar-ar/{}/?c=القاموس%20المحيط'.format(selected_word)
            sender(get_maany_else(url))


        if call.data == 'right':
            max_counter = len(maany__list)
            if (counter < max_counter):
                maana_text = str(counter + 1) + "- " + maany__list[counter].strip()
                counter += 1
                markup = types.InlineKeyboardMarkup()
                if(max_counter > counter):
                    markup.row(types.InlineKeyboardButton(text='⬅️', callback_data='left'), types.InlineKeyboardButton(text='➡️', callback_data='right'))
                else: markup.row(types.InlineKeyboardButton(text='⬅️', callback_data='left'))
                markup = add_dict_markup(markup, selected_word)
                bot.edit_message_text(maana_text, call.message.chat.id, call.message.message_id, reply_markup=markup)


        if call.data == 'left':
            if (counter > 1):
                counter -= 2
                maana_text = str(counter + 1) + "- " + maany__list[counter].strip()
                markup = types.InlineKeyboardMarkup()
                if(counter != 0):
                    markup.row(types.InlineKeyboardButton(text='⬅️', callback_data='left'), types.InlineKeyboardButton(text='➡️', callback_data='right'))
                else: markup.row(types.InlineKeyboardButton(text='➡️', callback_data='right'))
                markup = add_dict_markup(markup, selected_word)
                counter += 1
                bot.edit_message_text(maana_text, call.message.chat.id, call.message.message_id, reply_markup=markup)


print('Bot is running...')
while True:
    try:
        bot.infinity_polling()
    except:
        time.sleep(10)
