import os
from datetime import date, timedelta

import telebot
from telebot import types

from json_core import read_json, write_json


TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("Не найден BOT_TOKEN. Добавьте токен бота в переменные окружения.")

bot = telebot.TeleBot(TOKEN)

SERVICES = ["Маникюр", "Стрижка", "Покраска волос"]
WORKING_HOURS = ["10:00", "12:00", "15:00", "17:00"]


@bot.message_handler(commands=["start"])
def handle_start(message):
    bot.send_message(
        message.chat.id,
        "Привет! 💅 Это бот для записи в салон.\n"
        "Чтобы записаться, используй /make_appointment"
    )


@bot.message_handler(commands=["make_appointment"])
def handle_make_appointment(message):
    bot.send_message(
        message.chat.id,
        "Выберите услугу для записи:",
        reply_markup=generate_service_keyboard(),
    )


@bot.message_handler(commands=["set_name"])
def handle_set_name(message):
    bot.send_message(message.chat.id, "Введите ваше имя:")
    bot.register_next_step_handler(message, save_client)


@bot.message_handler(commands=["make_review"])
def handle_make_review(message):
    bot.send_message(message.chat.id, "Введите текст для отзыва:")
    bot.register_next_step_handler(message, save_review)


def save_client(message):
    data = read_json()
    data["clients"][str(message.chat.id)] = message.text.strip()
    write_json(data)

    bot.send_message(message.chat.id, "Ваше имя сохранено.")


def save_review(message):
    add_review(message.chat.id, message.text.strip())
    bot.send_message(message.chat.id, "Спасибо за ваш отзыв! 💖")


def generate_service_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)

    for service in SERVICES:
        button = types.InlineKeyboardButton(
            text=service,
            callback_data=f"service;{service}",
        )
        markup.add(button)

    return markup


def generate_day_keyboard(service):
    markup = types.InlineKeyboardMarkup(row_width=2)

    for days_from_now in range(3, 10):
        day = date.today() + timedelta(days=days_from_now)
        day_text = day.isoformat()

        button = types.InlineKeyboardButton(
            text=day_text,
            callback_data=f"day;{service};{day_text}",
        )
        markup.add(button)

    return markup


def generate_time_keyboard(service, day):
    markup = types.InlineKeyboardMarkup(row_width=2)
    data = read_json()

    busy_times = {
        appointment["time"]
        for appointment in data["appointments"]
        if appointment.get("date") == day
    }

    for appointment_time in WORKING_HOURS:
        if appointment_time in busy_times:
            continue

        button = types.InlineKeyboardButton(
            text=appointment_time,
            callback_data=f"app;{service};{day};{appointment_time}",
        )
        markup.add(button)

    return markup


def add_appointment(service, appointment_date, appointment_time, client):
    data = read_json()

    data["appointments"].append(
        {
            "service": service,
            "date": appointment_date,
            "time": appointment_time,
            "client": client,
        }
    )

    write_json(data)


def add_review(client, text):
    data = read_json()

    data["reviews"].append(
        {
            "client": client,
            "text": text,
        }
    )

    write_json(data)


@bot.callback_query_handler(func=lambda call: True)
def handle_button_click(call):
    bot.answer_callback_query(call.id)

    if call.data.startswith("service;"):
        service = call.data.split(";", 1)[1]

        bot.send_message(
            call.message.chat.id,
            "Выберите день для записи:",
            reply_markup=generate_day_keyboard(service),
        )

    elif call.data.startswith("day;"):
        _, service, day = call.data.split(";", 2)

        bot.send_message(
            call.message.chat.id,
            "Выберите время:",
            reply_markup=generate_time_keyboard(service, day),
        )

    elif call.data.startswith("app;"):
        _, service, appointment_date, appointment_time = call.data.split(";", 3)

        add_appointment(
            service,
            appointment_date,
            appointment_time,
            call.message.chat.id,
        )

        bot.send_message(
            call.message.chat.id,
            f"Вы записались на: {service}, {appointment_date} в {appointment_time} 💅",
        )


if __name__ == "__main__":
    bot.polling(none_stop=True)
