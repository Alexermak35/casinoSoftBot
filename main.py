import requests
import telebot
from telebot import types

token = '8183845101:AAF0MeCkqaSafaGWarLj_mt_P8mWnREragA'
BASE_URL = "http://localhost:8080"
bot = telebot.TeleBot(token)
added_to_db = False


@bot.message_handler(commands=['start'])
def start(message):
    url = f"{BASE_URL}/users/{message.from_user.id}"

    global added_to_db
    if added_to_db:
        resp = requests.post(url, json=None, timeout=5)
        resp.raise_for_status()
        response = resp.json()
        print(response)
    added_to_db = True

    # Create button
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton('Start playing tower rush', callback_data="tower_rush")
    markup.add(btn1)

    # Send picture with button
    with open("download.jpg", "rb") as photo:
        bot.send_photo(
            message.chat.id,
            photo=photo,
            caption=f'Hi, {message.from_user.first_name}',
            reply_markup=markup
        )


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "tower_rush":
        bot.send_message(
            call.message.chat.id,
        "📖 Инструкция:\n\n"
        "1️⃣ Открой мини приложение\n"
        "2️⃣ Введи ID игры, в которой ты играешь.\n"
        "3️⃣ Используй 3 бесплатных попытки.\n\n"
        "4️⃣ После того как попытки закончились, зарегистрируйся по ссылке и введи ID, который ты получил на сайте\n"
"5️⃣ Используй бота чтобы заработать✅\n"

        "Команды в чате:\n"
        "/instruction — инструкция\n"
        "/help - обратиться к администратору за помощью"
        )


@bot.message_handler(commands=['site', 'website'])
def site(message):
    bot.send_message(message.chat.id, "https://1whecs.life/casino/list?open=register&p=t0p9")


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(
        message.chat.id,
        'Contact <b>@alerm11</b> to get <em><u>help</u></em>',
        parse_mode='HTML'
    )


@bot.message_handler()
def information(message):
    if message.text.lower() == 'hi':
        bot.send_message(message.chat.id, f'Hi, {message.from_user.first_name}')
    elif message.text.lower() == 'id':
        bot.reply_to(message, f'ID: {message.from_user.id}')


bot.polling(none_stop=True)
