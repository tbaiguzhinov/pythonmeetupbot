import json
import logging
import random

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram import error as telegram_error
from telegram.ext import CallbackContext, ConversationHandler


from bot.static_text import greetings_message
import requests
from django.conf import settings

def send_notifications_to_user(message: str) -> None:
    telegram_token='5351272328:AAFM9KbcH2pRFei9j0oaEV7XX0kNm1__tGw'
    user_telegram_chat_id = 377157791
    url = f'https://api.telegram.org/bot{telegram_token}/sendMessage'
    try:
        requests.post(url, json={'chat_id': user_telegram_chat_id, 'text': message})
    except requests.HTTPError as err:
        print(err)



send_notifications_to_user('Danm you')
