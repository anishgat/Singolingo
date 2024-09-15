import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import requests
import re

load_dotenv()

TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')
bot = telebot.TeleBot(TELEGRAM_API_KEY)

user_data = {}

markup = InlineKeyboardMarkup()
learnButton = InlineKeyboardButton("Learn", callback_data="learn")
backButton = InlineKeyboardButton("Back", callback_data="back")
markup.add(learnButton, backButton)

@bot.message_handler(commands=['start'])
def welcome(message):
    user_id = message.chat.id
    reset(user_id)
    bot.send_message(message.chat.id, 'Welcome to SingoLingo! Choose a hindi song and translate it\'s lyrics one line at a time.')

@bot.message_handler(func=lambda message: not user_data[message.chat.id]['songChosen'])
def get_song(message):
    user_id = message.chat.id

    if not user_data[user_id]['songChosen']:    
        response = requests.get('https://singolingo.onrender.com/get-song-id', params={'title': message.text})
        if response.status_code == 200:
            data = response.json()
            
            formatted_hindi_lyrics = re.split('\n+', data['hindi_lyrics']) # Splits when there is one or more newlines
            formatted_english_lyrics = re.split('\n+', data['english_lyrics'])
            user_data[user_id]['chained_lyrics'] = list(zip(formatted_hindi_lyrics, formatted_english_lyrics))[0:-2]
            user_data[user_id]['songChosen'] = True
            question = user_data[user_id]['chained_lyrics'][user_data[user_id]['questionNumber']][0]

            bot.send_message(user_id, f'{message.text} was found! Translate the each line to english as closely as possible.')
            question_message = bot.send_message(user_id, question, reply_markup=markup)

            user_data[user_id]['prevMessageId'] = question_message.message_id
        
        elif response.status_code == 404:
            bot.send_message(user_id, f'The song {message.text} was not found.')
            # Autosuggest songs the user might have been trying to search

@bot.message_handler(func=lambda answer: user_data[answer.chat.id]['songChosen'])
def handle_answer(answer):
    user_id = answer.chat.id

    if user_data[user_id]['songChosen']:
        response = requests.get('https://singolingo.onrender.com/check-answer', params={'question': user_data[user_id]['chained_lyrics'][user_data[user_id]['questionNumber']][0], 'user_answer': answer.text, 'model_answer': user_data[user_id]['chained_lyrics'][user_data[user_id]['questionNumber']][1]})
        if response.status_code == 200:
            ai_response = response.json()
            if ai_response['response'].lower() == 'no':
                bot.send_message(user_id, '❌')
            else:
                if user_data[user_id]['questionNumber'] == len(user_data[user_id]['chained_lyrics']) - 1:
                    reset(user_id)
                    bot.send_message(user_id, 'Congratulations, the song is complete!')
                    bot.send_message(user_id, 'To choose another song, type in the name of the song.')
                else:
                    try:
                        user_data[user_id]['questionNumber'] += 1
                        question = user_data[user_id]['chained_lyrics'][user_data[user_id]['questionNumber']][0]
                        bot.edit_message_reply_markup(user_id, user_data[user_id]['prevMessageId'], reply_markup=None)
                        bot.send_message(user_id, '✅')
                        question_message = bot.send_message(user_id, question, reply_markup=markup)
                        user_data[user_id]['prevMessageId'] = question_message.message_id
                    
                    except IndexError:
                        bot.send_message(user_id, 'IndexError: list index out of range')
                        reset(user_id)
                        bot.send_message(user_id, 'To choose another song, type in the name of the song.')
        else:
            bot.send_message(user_id, 'An error occurred during the checking process')
            bot.send_message(user_id, response)

@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    user_id = call.message.chat.id

    if call.data == "learn":
        try:
            bot.send_message(user_id, user_data[user_id]['chained_lyrics'][user_data[user_id]['questionNumber']][1])
            bot.edit_message_reply_markup(user_id, user_data[user_id]['prevMessageId'], reply_markup=None)
            user_data[user_id]['prevMessageId'] = None
        except IndexError:
            bot.send_message(user_id, 'IndexError: list index out of range')
            reset(user_id)
            bot.send_message(user_id, 'To choose another song, type in the name of the song.')
        
        if user_data[user_id]['questionNumber'] == len(user_data[user_id]['chained_lyrics']) - 1:
            reset(user_id)
            bot.send_message(user_id, 'Congratulations, the song is complete!')
            bot.send_message(user_id, 'To choose another song, type in the name of the song.')
        else:
            user_data[user_id]['questionNumber'] += 1
            question = user_data[user_id]['chained_lyrics'][user_data[user_id]['questionNumber']][0]
            question_message = bot.send_message(user_id, question, reply_markup=markup)

            user_data[user_id]['prevMessageId'] = question_message.message_id

    elif call.data == "back":
        bot.edit_message_reply_markup(user_id, user_data[user_id]['prevMessageId'], reply_markup=None)
        user_data[user_id]['prevMessageId'] = None
        reset(user_id)
        bot.send_message(user_id, 'To choose another song, type in the name of the song.')

def reset(user_id):
    user_data[user_id] = {
        'songChosen': False,
        'chained_lyrics': [],
        'questionNumber': 0,
        'prevMessageId': None
    }

bot.polling()
