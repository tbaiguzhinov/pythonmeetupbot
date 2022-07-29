
import os
#import time
#from functools import partial
from datetime import datetime
from django.core.exceptions import FieldError
from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)
from bot.static_text import greetings_message
from bot.models import User, Meetup, Flow, Report, Question
import json
import logging


START, HANDLE_MENU, HANDLE_PROGRAMS, SEND_QUESTION,\
    HANDLE_FORM, HANDLE_QUESTION, HANDLE_FLOW, CLOSE = range(8)


logger = logging.getLogger(__name__)


def create_greetings_menu():
    keyboard = []
    programs_button = [InlineKeyboardButton('Программа', callback_data='programs')]
    keyboard.append(programs_button)
    questions_keyboard = [InlineKeyboardButton('Вопросы спикерам', callback_data='questions')]
    keyboard.append(questions_keyboard)
    form_keyboard = [InlineKeyboardButton('Заполнить анкету', callback_data='form')]
    keyboard.append(form_keyboard)
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def create_menu(products):
    keyboard = []
    callback_data, items = products
    for product in items:
        product_button = [InlineKeyboardButton(product.name, callback_data=f'{callback_data}{product.id}')]
        keyboard.append(product_button) 
    back_button = [InlineKeyboardButton('Назад', callback_data='back')]
    keyboard.append(back_button)
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup    


def start(update: Update, context: CallbackContext) -> None:
    clean_message(update, context)
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=greetings_message,
        reply_markup=create_greetings_menu()
        )
    return HANDLE_MENU


def flow_handle_menu(update: Update, context: CallbackContext) -> None:
    #flows = Flow.objects.all()
    clean_message(update, context)
    query = update.callback_query
    if query.data == 'programs':
        #flows = Program.objects.flows
        flows = ('flow', [])
        context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Пожалуйста выберите поток',
        reply_markup=create_menu(flows)
        )
        return HANDLE_PROGRAMS
    elif query.data == 'questions':
        today = datetime.today()
        current_meetup = Meetup.objects.filter(date__gte=today).first()
        flows = current_meetup.streams.all()
        flows = ('flow|', list(flows))
        context.bot.send_message(
            chat_id=update.effective_message.chat_id,
            text='Пожалуйста выберите поток',
            reply_markup=create_menu(flows)
        )
        return HANDLE_QUESTION


def flow_question_timeline(update: Update, context: CallbackContext):
    pass


def program_handle_menu(update: Update, context: CallbackContext) -> None:
    #programs = Programms.objects.all()
    programs = ('program', [])
    clean_message(update, context)
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Пожалуйста выберите поток необходимой программы',
        reply_markup=create_menu(programs)
        )
    return HANDLE_PROGRAMS


def select_speaker_menu(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    flow_id = query.data.rsplit('|')
    reports = Report.objects.filter(flow_id=flow_id).select_related('speaker')
    keyboard = []
    for report in reports:
        speaker_details = f'{report.speaker.first_name}, {report.speaker.last_name}' \
                          f', {report.speaker.job_title}, {report.speaker.company_name}'
        product_button = [InlineKeyboardButton(
            speaker_details,
            callback_data=f'speaker|{report.speaker.telegram_id}'
        )]
        keyboard.append(product_button)
    back_button = [InlineKeyboardButton('Назад', callback_data='back')]
    keyboard.append(back_button)
    reply_markup = InlineKeyboardMarkup(keyboard)
    clean_message(update, context)
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Пожалуйста, выберите спикера',
        reply_markup=reply_markup
        )
    return HANDLE_QUESTION


def save_chosen_speaker(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    speaker_id = query.data.rsplit('|')
    user_data = context.user_data
    user_data['speaker_to_ask'] = speaker_id
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Введите вопрос',
    )
    return SEND_QUESTION


def send_message_to_speaker(update: Update, context: CallbackContext) -> None:
    question_text = update.message.text
    speaker_to_ask_id = context.user_data['speaker_to_ask_id']
    context.bot.send_message(
        chat_id=speaker_to_ask_id,
        text=question_text,
    )
    Question.objects.create(
        author_id=update.effective_message.chat_id,
        recipient_id=speaker_to_ask_id,
        text=question_text
    )
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Спасибо за ваш вопрос!',
    )
    return HANDLE_MENU


def form_handle(update: Update, context: CallbackContext):
    clean_message(update, context)
    user_data = context.user_data
    user_data['poll_questions'] = read_poll_questions()
    user_data['answers'] = []
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=user_data['poll_questions'].pop('name'),
        )
    return HANDLE_FORM


def ask_form_questions(update: Update, context: CallbackContext):
    user_data = context.user_data
    if user_data['poll_questions']:
        for question in user_data['poll_questions']:
            user_data['answers'].extend([update.message.text])
            context.bot.send_message(
                chat_id=update.effective_message.chat_id,
                text=user_data['poll_questions'].pop(question),
                )
            return HANDLE_FORM
    else:
        user_data['answers'].extend([update.message.text])
        try:
            name, company, position, email, telegram = user_data['answers']
            try:
                first_name, last_name = name.split(' ')
            except ValueError:
                first_name = name
                last_name = None
            user, created = User.objects.get_or_create(
                first_name=first_name,
                last_name=last_name,
                company_name=company,
                job_title=position,
                email=email,
                telegram_id=update.effective_user.id,
                telegram_username=telegram,
                questionnaire_filled=True
            )
            if created:
                context.bot.send_message(
                        chat_id=update.effective_message.chat_id,
                        text='Опрос окончен, спасибо за участие!',
                        reply_markup=create_greetings_menu()
                        )
        except Exception as err:
            print(err)
            answers = user_data['answers']
            context.bot.send_message(
                        chat_id=update.effective_message.chat_id,
                        text=f'Ваша анкета уже есть в базе данных{answers}',
                        reply_markup=create_greetings_menu()
                        )
        return HANDLE_MENU


def read_poll_questions():
    with open('questions_to_clients.txt', 'r', encoding='utf8') as file_handler:
        poll_questions = json.load(file_handler)
    return poll_questions


def clean_message(update: Update, context: CallbackContext):
    message_id = update.effective_message.message_id
    chat_id = update.effective_message.chat_id
    context.bot.delete_message(chat_id=chat_id, message_id=message_id)


def handle_error(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""


def end_conversation(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Пока!'
        )
    return ConversationHandler.END
