import telebot
from telebot import types
from deep_translator import GoogleTranslator
from functions_bot import (is_valid_date, get_location, JsonController, get_prayer_times, get_user_data,
                           get_prayer_times_for_next_7_days)
import datetime
import re

print("Run Update")
BOT_TOKEN = '7724222873:AAEzTg66dKavN9EEnTe7YBMwWCQixuDjRBw'
bot = telebot.TeleBot(token=BOT_TOKEN)

language = 'en'
data_user = {
    "name": "",
    "username": "",
    "phone": "",
    "location": "",
    "notify": True,
    "birthday": "",
    "language": language
}

welcome_txt = '''Hello! Welcome to Praying Times Bot.'''
reg_txt = '''Please register. What is your full name?'''
bday_txt = '''When is your birthday? (dd.mm.yyyy) or click Skip.'''
phone_txt = '''What is your Phone Number? Or click Skip.'''
loc_txt = '''What is your location?

It is mandatory because I will tell the praying times based in the location😊'''
not_txt = '''Would you like notifications before praying times?'''
t1 = '''Something went wrong.'''
help_txt = '''
I can help you to know praying times!

You can control me by sending these commands:

{time_cmd} - to know praying times for today
{settings_cmd} - to open settings page
{times_cmd} - to know praying times for tomorrow or other days
{help_cmd} - to know all controlling commands

'''
commands = ['/help', '/start', '/times', '/time', '/settings']


def translater(text, target):
    return GoogleTranslator(source='en', target=target).translate(text)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    main = get_user_data()
    flag = False
    for i in main:
        if i == str(message.from_user.id):
            bot.send_message(message.chat.id,
                             translater(f"You already have an account. Welcome back {main[i]['name']}!",
                                        target=main[i]['Language']))
            flag = True
            print("User exists")
            break
    if not flag:
        print("User does not exist")
        user_id = message.chat.id
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('🇬🇧', callback_data='en'),
                   types.InlineKeyboardButton('🇷🇺', callback_data='ru'),
                   types.InlineKeyboardButton('🇩🇪', callback_data='de'),
                   types.InlineKeyboardButton('🇸🇦', callback_data='ar'))
        bot.send_message(user_id, 'Language:', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, translater(welcome_txt, target=main[message.from_user.id]['Language']))
        formatted_help_txt = translater(help_txt, target=main[message.from_user.id]['Language']).format(
            time_cmd=commands[3],
            settings_cmd=commands[4],
            times_cmd=commands[2],
            help_cmd=commands[0]
        )
        bot.send_message(message.chat.id, formatted_help_txt)


@bot.message_handler(commands=['times'])
def send_times(message):
    main = get_user_data()
    user_id = str(message.from_user.id)
    if user_id not in main:
        bot.send_message(message.chat.id, "You need to register first. Use /start to begin.")
        return
    tzt = '''Prayer Times for the Next 7 Days:'''
    bot.send_message(message.chat.id, translater(tzt, target=main[user_id]['Language']))
    tzt = ''''''
    prayer_times = get_prayer_times_for_next_7_days(main[user_id]['LL'][0], main[user_id]['LL'][1])
    for date, timings in prayer_times.items():
        print(f"\nDate: {date}")
        tzt += f"\n\nDate: {date}"
        for prayer, time in timings.items():
            c_time = re.sub(r'\s*\(.*?\)', '', time)
            print(f"  {prayer}:   {c_time}")
            tzt += f"\n  {prayer}:   {c_time}"
        bot.send_message(message.chat.id, translater(tzt, target=main[user_id]['Language']))
        tzt = ''''''



@bot.message_handler(commands=['settings'])
def send_settings(message):
    bot.send_message(message.chat.id, "settings")


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, "help")


@bot.message_handler(commands=['time'])
def send_time(message):
    main = get_user_data()
    user_id = str(message.from_user.id)
    if user_id not in main:
        bot.send_message(message.chat.id, "You need to register first. Use /start to begin.")
        return
    try:
        ll = main[user_id]["LL"]
        prayer_times = get_prayer_times(ll[0], ll[1])
        praying_times = f'''Praying times for {datetime.date.today()}\n\n'''
        for prayer, time in prayer_times.items():
            if prayer in ['Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']:
                praying_times += f"{prayer}:   {time}\n"
        bot.send_message(message.chat.id, translater(praying_times, target=main[user_id]['Language']))
    except KeyError as e:
        bot.send_message(message.chat.id, f"Missing data for key: {e}. Please complete your profile.")


@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    global language
    language = callback.data
    send_message(callback.message)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def send_message(message):
    main = get_user_data()
    bot.delete_message(message.chat.id, message.message_id)
    translated_text = translater(welcome_txt, target=main[message.from_user.id]['Language'])
    bot.send_message(message.chat.id, translated_text)
    register(message)


def register(message):
    main = get_user_data()
    tr_txt = translater(reg_txt, target=main[message.from_user.id]['Language'])
    bot.send_message(message.chat.id, tr_txt)
    bot.register_next_step_handler(message, name_handler)


def name_handler(message, flag=False):
    main = get_user_data()
    if not flag:
        data_user['name'] = message.text
        data_user['username'] = message.from_user.username
    tr_txt = translater(bday_txt, target=main[message.from_user.id]['Language'])
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton(text=translater('⏭️Skip', target=main[message.from_user.id]['Language'])))
    bot.send_message(message.chat.id, tr_txt, reply_markup=markup)
    bot.register_next_step_handler(message, date_handler)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def date_handler(message, flag=False):
    main = get_user_data()
    if message.text != translater('⏭️Skip', target=main[message.from_user.id]['Language']) and is_valid_date(
            message.text):
        data_user['birthday'] = message.text
        request_phone(message)
    elif message.text == translater('⏭️Skip', target=main[message.from_user.id]['Language']) or flag:
        request_phone(message)
    else:
        txt = translater('Invalid date entered.', target=main[message.from_user.id]['Language'])
        bot.send_message(message.chat.id, txt)
        name_handler(message, flag=True)


def request_phone(message):
    main = get_user_data()
    tr_txt = translater(phone_txt, target=main[message.from_user.id]['Language'])
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(
        types.KeyboardButton(text=translater('📞Send Phone Number', target=main[message.from_user.id]['Language']),
                             request_contact=True),
        types.KeyboardButton(text=translater('⏭️Skip', target=main[message.from_user.id]['Language'])))
    bot.send_message(message.chat.id, tr_txt, reply_markup=markup)
    bot.register_next_step_handler(message, callback_phone)


@bot.message_handler(content_types=['contact'])
def callback_phone(message, flag=False):
    main = get_user_data()
    if message.contact and not flag:
        data_user['phone'] = message.contact.phone_number
        request_location(message)
    elif message.text == translater('⏭️Skip', target=main[message.from_user.id]['Language']) or flag:
        request_location(message)
    else:
        txt = translater(t1, target=main[message.from_user.id]['Language'])
        bot.send_message(message.chat.id, txt)
        date_handler(message, flag=True)


def request_location(message):
    main = get_user_data()
    txt = translater(loc_txt, target=main[message.from_user.id]['Language'])
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton(text=translater('📍Send Location', target=main[message.from_user.id]['Language']),
                                    request_location=True))
    bot.send_message(message.chat.id, txt, reply_markup=markup)
    bot.register_next_step_handler(message, location_handler)


@bot.message_handler(content_types=['location'])
def location_handler(message):
    main = get_user_data()
    if message.location:
        lo = get_location(latitude=message.location.latitude, longitude=message.location.longitude)
        txt = translater(f"Your current city is {lo}. Correct?", target=main[message.from_user.id]['Language'])
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton(text=translater('Yes', target=main[message.from_user.id]['Language'])),
                   types.KeyboardButton(text=translater('No', target=main[message.from_user.id]['Language'])))
        bot.send_message(message.chat.id, txt, reply_markup=markup)
        bot.register_next_step_handler(message, loc_check, location=lo)
    else:
        txt = translater('Invalid Location', target=main[message.from_user.id]['Language'])
        bot.send_message(message.chat.id, txt)
        callback_phone(message, flag=True)


def loc_check(message, location=None):
    main = get_user_data()
    if message.text == translater('Yes', target=main[message.from_user.id]['Language']):
        data_user['location'] = location
        request_notification(message)
    elif message.text == translater('No', target=main[message.from_user.id]['Language']):
        callback_phone(message, flag=True)
    else:
        txt = translater('Please use buttons below.', target=main[message.from_user.id]['Language'])
        bot.send_message(message.chat.id, txt)
        location_handler(message, flag=True)


def request_notification(message):
    main = get_user_data()
    txt = translater(not_txt, main[message.from_user.id]['Language'])
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton(text=translater('Yes', target=main[message.from_user.id]['Language'])),
               types.KeyboardButton(text=translater('No', target=main[message.from_user.id]['Language'])))
    bot.send_message(message.chat.id, txt, reply_markup=markup)
    bot.register_next_step_handler(message, notify_handler)


def notify_handler(message):
    main = get_user_data()
    if message.text in [translater('Yes', target=main[message.from_user.id]['language']),
                        translater('No', target=main[message.from_user.id]['Language'])]:
        data_user['notify'] = message.text == translater('Yes', target=main[message.from_user.id]['Language'])
        main1 = JsonController(file_path="data.json")
        main1.edit_json(key=message.from_user.id, value=data_user)
        bot.send_message(message.chat.id,
                         translater("You have successfully registered)", target=main[message.from_user.id]['Language']))
        bot.send_message(message.chat.id,
                         translater("Welcome to Praying times!", target=main[message.from_user.id]['Language']))
        translated_text = translater(help_txt, target=main[message.from_user.id]['Language'])
        formatted_help_txt = translated_text.format(
            time_cmd=commands[3],
            settings_cmd=commands[4],
            times_cmd=commands[2],
            help_cmd=commands[0]
        )
        bot.send_message(message.chat.id, formatted_help_txt)
    else:
        txt = translater('Please use buttons below.', target=main[message.from_user.id]['Language'])
        bot.send_message(message.chat.id, txt)
        request_notification(message)


bot.infinity_polling()
