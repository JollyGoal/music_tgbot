import telebot
import asyncio
import config as conf  # custom configurations
import audio_handler
import datetime
import os
import math

ELEMENTS_PER_PAGE = 8

bot = telebot.TeleBot(conf.TOKEN, parse_mode=None)

pages_dict = {}


@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    if message.text == "/start":
        asyncio.run(save_user_in_db(message.from_user))
    bot.send_message(message.chat.id,
                     f'Hello, {message.from_user.first_name}'
                     f' I can find any music you want\nJust send me the search query')


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "PREV_PAGE":
        try:
            audios = audio_handler.find_music(call.message.text)
            overall_pages = math.ceil(len(audios) / ELEMENTS_PER_PAGE)

            if pages_dict[call.message.chat.id] - 1 <= 0:
                pages_dict[call.message.chat.id] = overall_pages
            else:
                pages_dict[call.message.chat.id] -= 1

            audios_paginated = []
            for i in range((ELEMENTS_PER_PAGE * (pages_dict[call.message.chat.id] - 1)),
                           (ELEMENTS_PER_PAGE * pages_dict[call.message.chat.id])):
                try:
                    audios_paginated.append(audios[i])
                except:
                    pass

            try:
                bot.edit_message_text(call.message.text, chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      reply_markup=set_response_markup(audios_paginated, overall_pages,
                                                                       pages_dict[call.message.chat.id], ))
            except:
                pass
            bot.answer_callback_query(call.id)
        except:
            bot.answer_callback_query(call.id, text="Something went wrong. Please try again later")
    elif call.data == "NEXT_PAGE":
        try:
            audios = audio_handler.find_music(call.message.text)
            overall_pages = math.ceil(len(audios) / ELEMENTS_PER_PAGE)

            if pages_dict[call.message.chat.id] + 1 > overall_pages:
                pages_dict[call.message.chat.id] = 1
            else:
                pages_dict[call.message.chat.id] += 1

            audios_paginated = []
            for i in range((ELEMENTS_PER_PAGE * (pages_dict[call.message.chat.id] - 1)),
                           (ELEMENTS_PER_PAGE * pages_dict[call.message.chat.id])):
                try:
                    audios_paginated.append(audios[i])
                except:
                    pass

            try:
                bot.edit_message_text(call.message.text, chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      reply_markup=set_response_markup(audios_paginated, overall_pages,
                                                                       pages_dict[call.message.chat.id], ))
            except:
                pass
            bot.answer_callback_query(call.id)
        except:
            bot.answer_callback_query(call.id, text="Something went wrong. Please try again later")
    elif call.data == "PAGES":
        bot.answer_callback_query(call.id)
    else:
        try:
            audio, file_path = audio_handler.get_audio(call.data)
            send_audio(audio, file_path, call.message.chat.id)
            bot.answer_callback_query(call.id)
        except:
            pass


@bot.message_handler(content_types=["text"])
def check_users(message):
    search_message = bot.send_message(message.chat.id, "Searching...")
    try:
        # msg = f"Results for {message.text}:"
        msg = message.text
        audios = audio_handler.find_music(message.text)
        pages_dict[message.chat.id] = 1

        overall_pages = math.ceil(len(audios) / ELEMENTS_PER_PAGE)

        first_page_audios = []
        for i in range((ELEMENTS_PER_PAGE * (pages_dict[message.chat.id] - 1)),
                       (ELEMENTS_PER_PAGE * pages_dict[message.chat.id])):
            first_page_audios.append(audios[i])

        bot.send_message(message.chat.id, msg, reply_markup=set_response_markup(first_page_audios, overall_pages,
                                                                                pages_dict[message.chat.id]))
    except Exception as e:
        print(e)
        msg = "Please send valid query"
        bot.reply_to(message, f'{msg}')
    bot.delete_message(search_message.chat.id, search_message.message_id)


async def save_user_in_db(user):
    msg = f"ID: {user.id}\nIs bot?: {user.is_bot}\nFirst name: {user.first_name}" \
          f"\nLast name: {user.last_name}\nUsername: @{user.username}"
    bot.send_message(conf.DATABASE_CHANNEL_ID, msg)


def send_audio(audio, file_path, chat_id):
    file = open(file_path, "rb")
    bot.send_audio(chat_id=chat_id, audio=file, caption="@kekmusic_bot", performer=audio.artist, title=audio.title,
                   thumb=audio.image, duration=int(audio.duration),
                   )
    file.close()
    os.remove(file_path)


def set_response_markup(elements, overall_pages, curr_page):
    markup = telebot.types.InlineKeyboardMarkup()
    for elem in elements:
        elem_title = f"{elem.title} - {elem.artist}"
        try:
            time = str(datetime.timedelta(seconds=elem.duration))
            if time.startswith("0:"):
                elem_title += f" | {time[2:]}"
            else:
                elem_title += f" | {time}"
        except:
            pass
        audio_btn = telebot.types.InlineKeyboardButton(text=elem_title, callback_data=f"{elem.owner_id}_{elem.id}")
        markup.add(audio_btn)
    if overall_pages > 1:
        markup.add(
            telebot.types.InlineKeyboardButton(text="<<", callback_data="PREV_PAGE"),
            telebot.types.InlineKeyboardButton(text=f"{curr_page}/{overall_pages}", callback_data="PAGES"),
            telebot.types.InlineKeyboardButton(text=">>", callback_data="NEXT_PAGE"),
        )
    return markup


if __name__ == '__main__':
    bot.polling(none_stop=True)
