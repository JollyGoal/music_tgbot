import telebot
import asyncio
import config as conf  # custom configurations
import datetime
import os
import math

bot = telebot.AsyncTeleBot(conf.BOT_TOKEN, parse_mode=None)

pages_dict = {}


class EmptyResponse(Exception):
    pass


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
            overall_pages = math.ceil(len(audios) / conf.ELEMENTS_PER_PAGE)

            if pages_dict[call.message.chat.id] - 1 <= 0:
                pages_dict[call.message.chat.id] = overall_pages
            else:
                pages_dict[call.message.chat.id] -= 1

            audios_paginated = []
            for i in range((conf.ELEMENTS_PER_PAGE * (pages_dict[call.message.chat.id] - 1)),
                           (conf.ELEMENTS_PER_PAGE * pages_dict[call.message.chat.id])):
                try:
                    audios_paginated.append(audios[i])
                except Exception as e:
                    print(e)

            try:
                bot.edit_message_text(call.message.text, chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      reply_markup=set_response_markup(audios_paginated, overall_pages,
                                                                       pages_dict[call.message.chat.id], ))
            except Exception as e:
                print(e)
            bot.answer_callback_query(call.id)
        except Exception as e:
            print(e)
            bot.answer_callback_query(call.id, text="Something went wrong. Please try again later")
    elif call.data == "NEXT_PAGE":
        try:
            audios = audio_handler.find_music(call.message.text)
            overall_pages = math.ceil(len(audios) / conf.ELEMENTS_PER_PAGE)

            if pages_dict[call.message.chat.id] + 1 > overall_pages:
                pages_dict[call.message.chat.id] = 1
            else:
                pages_dict[call.message.chat.id] += 1

            audios_paginated = []
            for i in range((conf.ELEMENTS_PER_PAGE * (pages_dict[call.message.chat.id] - 1)),
                           (conf.ELEMENTS_PER_PAGE * pages_dict[call.message.chat.id])):
                try:
                    audios_paginated.append(audios[i])
                except Exception as e:
                    print(e)

            try:
                bot.edit_message_text(call.message.text, chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      reply_markup=set_response_markup(audios_paginated, overall_pages,
                                                                       pages_dict[call.message.chat.id], ))
            except Exception as e:
                print(e)
            bot.answer_callback_query(call.id)
        except Exception as e:
            print(e)
            bot.answer_callback_query(call.id, text="Something went wrong. Please try again later")
    elif call.data == "PAGES":
        bot.answer_callback_query(call.id)
    else:
        try:
            audio, file_path = audio_handler.get_audio(call.data)
            send_audio(audio, file_path, call.message.chat.id)
            bot.answer_callback_query(call.id)
        except Exception as e:
            print(e)


# TODO If count of objects is equal to zero than move to 1st page
# TODO If count of objects is less than conf.ELEMENTS_PER_PAGE => next page should be the 1st
@bot.message_handler(content_types=["text"])
def search_music(message):
    search_message = bot.send_message(message.chat.id, "Searching...").wait()
    try:
        msg = message.text
        audios = app.run(find_audio(message.text))
        pages_dict[message.chat.id] = 1
        if len(audios) == 0:
            raise EmptyResponse

        bot.send_message(message.chat.id, msg, reply_markup=set_response_markup(audios, pages_dict[message.chat.id]))
    except EmptyResponse:
        bot.reply_to(message, "Please send valid query")
    except Exception as e:
        print(e)
        msg = "Something went wrong, please try again later"
        bot.reply_to(message, f'{msg}')
    bot.delete_message(search_message.chat.id, search_message.message_id)


async def save_user_in_db(user):
    msg = f"ID: {user.id}\nIs bot?: {user.is_bot}\nFirst name: {user.first_name}" \
          f"\nLast name: {user.last_name}\nUsername: @{user.username}"
    bot.send_message(conf.USERS_DATABASE_CHANNEL_ID, msg)


async def send_audio(audio, file_path, chat_id):
    file = open(file_path, "rb")
    bot.send_audio(chat_id=chat_id, audio=file, caption="@kekmusic_bot", performer=audio.artist, title=audio.title,
                   thumb=audio.image, duration=int(audio.duration),
                   )
    file.close()
    os.remove(file_path)


def set_response_markup(elements, curr_page):
    markup = telebot.types.InlineKeyboardMarkup()
    for elem in elements:
        elem_title = f"{elem.title} - {elem.artist}"
        try:
            time = str(datetime.timedelta(seconds=elem.duration))
            if time.startswith("0:"):
                elem_title += f" | {time[2:]}"
            else:
                elem_title += f" | {time}"
        except Exception as e:
            print(e)
        audio_btn = telebot.types.InlineKeyboardButton(text=elem_title, callback_data=f"{elem.owner_id}_{elem.id}")
        markup.add(audio_btn)
    if elements == conf.ELEMENTS_PER_PAGE and curr_page == 1:
        markup.add(
            telebot.types.InlineKeyboardButton(text="<<", callback_data="PREV_PAGE"),
            telebot.types.InlineKeyboardButton(text=f"{curr_page}", callback_data="PAGES"),
            telebot.types.InlineKeyboardButton(text=">>", callback_data="NEXT_PAGE"),
        )
    return markup


if __name__ == '__main__':
    bot.polling(none_stop=True)
