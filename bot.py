import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import requests

load_dotenv()

TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')
bot = telebot.TeleBot(TELEGRAM_API_KEY)

questionNumber = 0
chained_lyrics = []
songChosen = False

markup = InlineKeyboardMarkup()
learnButton = InlineKeyboardButton("Learn", callback_data="learn")
backButton = InlineKeyboardButton("Back", callback_data="back")
markup.add(learnButton, backButton)

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, 'Welcome to SingoLingo! Choose a hindi song and translate it\'s lyrics one line at a time.')

@bot.message_handler(func=lambda message: not songChosen)
def get_song(message):
    global songChosen, chained_lyrics, questionNumber

    if not songChosen:    
        response = requests.get('http://127.0.0.1:8000/get-song-id', params={'title': message.text})
        if response.status_code == 200:
            data = response.json()
            
            formatted_hindi_lyrics = data['hindi_lyrics'].split('\n')
            formatted_english_lyrics = data['english_lyrics'].split('\n')
            chained_lyrics = list(zip(formatted_hindi_lyrics, formatted_english_lyrics))[0:-2]
            songChosen = True
            question = chained_lyrics[questionNumber][0]

            bot.send_message(message.chat.id, f'{message.text} was found! Translate the each line to english as closely as possible.')
            bot.send_message(message.chat.id, question, reply_markup=markup)
        
        elif response.status_code == 404:
            bot.send_message(message.chat.id, f'The song {message.text} was not found.')
            # Autosuggest songs the user might have been trying to search

@bot.message_handler(func=lambda answer: songChosen)
def handle_answer(answer):
    global songChosen, chained_lyrics, questionNumber
    if songChosen:
        response = requests.get('http://127.0.0.1:8000/check-answer', params={'question': chained_lyrics[questionNumber][0], 'user_answer': answer.text, 'model_answer': chained_lyrics[questionNumber][1]})
        if response.status_code == 200:
            ai_response = response.json()
            if ai_response['response'].lower() == 'no':
                bot.send_message(answer.chat.id, '❌')
            else:
                if questionNumber == len(chained_lyrics) - 1:
                    reset()
                    bot.send_message(answer.chat.id, 'Congratulations, the song is complete!')
                    bot.send_message(answer.chat.id, 'To choose another song, type in the name of the song.')
                else:
                    questionNumber += 1
                    question = chained_lyrics[questionNumber][0]
                    bot.send_message(answer.chat.id, '✅')
                    bot.send_message(answer.chat.id, question, reply_markup=markup)
        else:
            bot.send_message(answer.chat.id, 'An error occurred during the checking process')

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    global songChosen, chained_lyrics, questionNumber
    if call.data == "learn":
        bot.send_message(call.message.chat.id, chained_lyrics[questionNumber][1])
        if questionNumber == len(chained_lyrics) - 1:
            reset()
            bot.send_message(call.message.chat.id, 'Congratulations, the song is complete!')
            bot.send_message(call.message.chat.id, 'To choose another song, type in the name of the song.')
        else:
            questionNumber += 1
            question = chained_lyrics[questionNumber][0]
            bot.send_message(call.message.chat.id, question, reply_markup=markup)

    elif call.data == "back":
        reset()
        bot.send_message(call.message.chat.id, 'To choose another song, type in the name of the song.')

def reset():
    global songChosen, chained_lyrics, questionNumber
    songChosen = False
    questionNumber = 0
    chained_lyrics = []

bot.polling()