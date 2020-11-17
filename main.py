import datetime
import re
from time import time
from os import environ

import requests
from pyrogram import Client, filters
from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent, \
    InlineKeyboardMarkup, InlineKeyboardButton
from vkaudiotoken import get_kate_token, get_vk_official_token

# import config as conf  # custom configurations
from pyrogram_audio import InlineQueryResultAudio

# api_id = conf.API_ID
# api_hash = conf.API_HASH
# bot_token = conf.BOT_TOKEN
# phone_number = conf.PHONE_NUMBER
# login = login
# password = password
# USERS_DATABASE_CHANNEL_ID = conf.USERS_DATABASE_CHANNEL_ID
# YT_MUSIC_DATABASE_CHANNEL_ID = conf.YT_MUSIC_DATABASE_CHANNEL_ID
# KEK_MUSIC_DATABASE_CHANNEL_ID = conf.KEK_MUSIC_DATABASE_CHANNEL_ID

api_id = int(environ["API_ID"])
api_hash = environ["API_HASH"]
bot_token = environ["BOT_TOKEN"]
phone_number = environ["PHONE_NUMBER"]
login = environ["LOGIN"]
password = environ["PASSWORD"]
USERS_DATABASE_CHANNEL_ID = int(environ["USERS_DATABASE_CHANNEL_ID"])
YT_MUSIC_DATABASE_CHANNEL_ID = int(environ["YT_MUSIC_DATABASE_CHANNEL_ID"])
KEK_MUSIC_DATABASE_CHANNEL_ID = int(environ["KEK_MUSIC_DATABASE_CHANNEL_ID"])

pages_dict = {}

ELEMENTS_PER_PAGE = 8
ADMINS_IDS = [174530324, 33908550]

app = Client("app", api_id, api_hash, phone_number=phone_number)
bot = Client("bot", api_id, api_hash, bot_token=bot_token)

_pattern = re.compile(r'/[a-zA-Z\d]{6,}(/.*?[a-zA-Z\d]+?)/index.m3u8()')


class EmptyResponse(Exception):
    pass


async def find_audio(query, chat_id, page=1, limit=ELEMENTS_PER_PAGE):
    page = page - 1
    # async with app:
    messages = []
    async for message in app.search_messages(chat_id, query=query, limit=limit,
                                             offset=page * limit):
        messages.append(message)
    return messages


def search_vk_audio(query: str, page=1, limit=ELEMENTS_PER_PAGE, performer_only: int = 0):
    try:
        client = get_vk_official_token(login, password)
        token = client['token']
        print(token)
        user_agent = client['user_agent']

        sess = requests.session()
        sess.headers.update({'User-Agent': user_agent})

        page = page - 1

        result = sess.get(
            "https://api.vk.com/method/audio.search",
            params=[
                ('access_token', token),
                ('v', '5.95'),
                ('q', query),
                ('performer_only', performer_only),
                ('offset', page * limit),
                ('count', limit)
            ]
        )
    except Exception as e:
        print(e)

        client = get_kate_token(login, password)
        token = client['token']
        user_agent = client['user_agent']

        sess = requests.session()
        sess.headers.update({'User-Agent': user_agent})

        page = page - 1

        result = sess.get(
            "https://api.vk.com/method/audio.search",
            params=[
                ('access_token', token),
                ('v', '5.95'),
                ('q', query),
                ('performer_only', performer_only),
                ('offset', page * limit),
                ('count', limit)
            ]
        )
    js = result.json()
    return result.json()['response']


def popular_vk_audio(page=1, limit=ELEMENTS_PER_PAGE):
    client = get_vk_official_token(login, password)
    token = client['token']
    user_agent = client['user_agent']

    sess = requests.session()
    sess.headers.update({'User-Agent': user_agent})

    page = page - 1

    result = sess.get(
        "https://api.vk.com/method/audio.getPopular",
        params=[
            ('access_token', token),
            ('v', '5.95'),
            ('offset', page * limit),
            ('count', limit)
        ]
    )
    return result.json()['response']


async def forward_audio(message_ids, chat_id, from_chat_id):
    # async with app:
    msg = await app.forward_messages(
        chat_id=chat_id,
        from_chat_id=from_chat_id,
        message_ids=message_ids,
        as_copy=False,
    )
    return msg


async def save_user_in_db(user):
    users_data = []
    async for message in app.search_messages(USERS_DATABASE_CHANNEL_ID, query=f"{user.id}",
                                             limit=999):
        try:
            if message.text.startswith(f"ID: {user.id}"):
                users_data.append(message)
        except Exception as e:
            print(e)
    msg = f"ID: {user.id}\nIs bot?: {user.is_bot}\nFirst name: {user.first_name}" \
          f"\nLast name: {user.last_name}\nUsername: @{user.username}\nIs active: True"
    if len(users_data) == 0:
        await bot.send_message(USERS_DATABASE_CHANNEL_ID, msg)
    elif len(users_data) == 1:
        try:
            await users_data[0].edit_text(msg)

        except Exception as e:
            print(e)
            pass
    else:
        for single_user_data in users_data:
            await single_user_data.delete()
        await bot.send_message(USERS_DATABASE_CHANNEL_ID, msg)


# TODO see pyrogram's get_chat()
# @bot.on_message(filters.new_chat_members & filters.left_chat_member)
# async def handle_groups(client, message):
#     pass


# @bot.on_message()
# async def message_info(client, message):
#     print(message)


@bot.on_inline_query()
async def answer(client, inline_query):
    try:
        if len(inline_query.query) == 0:
            raise Exception
        response = search_vk_audio(query=inline_query.query, limit=10)
        audios = response['items']
        if len(audios) == 0:
            raise EmptyResponse
        results = []
        for audio in audios:
            try:
                print(audio['url'])
                url = _pattern.sub(r'\1\2.mp3', audio['url'])
                results.append(
                    InlineQueryResultAudio(
                        title=audio['title'],
                        audio_url=url,
                        voice=False,
                        duration=int(audio['duration']),
                        performer=audio['artist'],
                        description=audio['artist'],
                        caption="[𝑺𝒂𝒍𝒗𝒂𝒕𝒐𝒓𝒆𝑴𝒖𝒛](https://t.me/salvatoremuzbot)🥀",
                    ),
                )
            except Exception as e:
                print(e)
        await inline_query.answer(
            results=results,
            cache_time=1,
        )
    except EmptyResponse:
        results = [
            InlineQueryResultArticle(
                title="Nothing found. Please type music artist name and music title",
                input_message_content=InputTextMessageContent("/help"),
            )
        ]
        await inline_query.answer(
            results=results,
            cache_time=1,
        )
    except Exception as e:
        print(e)
        results = [
            InlineQueryResultArticle(
                title="Please type music artist name and music title",
                input_message_content=InputTextMessageContent("/help"),
            )
        ]
        # audios = popular_vk_audio(limit=10)
        # for audio in audios:
        #     try:
        #         url = _pattern.sub(r'\1\2.mp3', audio['url'])
        #         results.append(
        #             InlineQueryResultAudio(
        #                 title=audio['title'],
        #                 audio_url=url,
        #                 voice=False,
        #                 duration=int(audio['duration']),
        #                 performer=audio['artist'],
        #                 description=audio['artist'],
        #                 caption="[𝑺𝒂𝒍𝒗𝒂𝒕𝒐𝒓𝒆𝑴𝒖𝒛](https://t.me/salvatoremuzbot)🥀",
        #             ),
        #         )
        #     except Exception as e:
        #         print(e)
        await inline_query.answer(
            results=results,
            cache_time=1,  # TODO
        )


async def get_all_users_count():
    users_count = 0
    active_users = 0
    inactive_users = 0
    groups_count = 0
    active_groups = 0
    inactive_groups = 0

    async for message in app.iter_history(USERS_DATABASE_CHANNEL_ID):
        try:
            if message.text.startswith("ID: "):
                users_count += 1
                if message.text.endswith("False"):
                    inactive_users += 1
                else:
                    active_users += 1
            elif message.text.startswith("GROUP ID: "):
                groups_count += 1
                if message.text.endswith("False"):
                    inactive_groups += 1
                else:
                    active_groups += 1
        except Exception as e:
            print(e)
    msg = f"Active: {active_users + active_groups} ({active_users}👤 {active_groups}👥)\n" \
          f"Inactive: {inactive_users + inactive_groups} ({inactive_users}👤 {inactive_groups}👥)\n" \
          f"Total: {users_count + groups_count} ({users_count}👤 {groups_count}👥)\n" \
          f"👤 - users\n👥 - group chats\n"
    return msg


async def get_today_new_users():
    users_count = 0
    active_users = 0
    inactive_users = 0
    groups_count = 0
    active_groups = 0
    inactive_groups = 0

    async for message in app.iter_history(USERS_DATABASE_CHANNEL_ID):
        if time() - message.date >= 86400:
            break
        try:
            if message.text.startswith("ID: "):
                users_count += 1
                if message.text.endswith("False"):
                    inactive_users += 1
                else:
                    active_users += 1
            elif message.text.startswith("GROUP ID: "):
                groups_count += 1
                if message.text.endswith("False"):
                    inactive_groups += 1
                else:
                    active_groups += 1
        except Exception as e:
            print(e)
    msg = f"Updates for last 24 hours:\n" \
          f"Active: {active_users + active_groups} ({active_users}👤 {active_groups}👥)\n" \
          f"Inactive: {inactive_users + inactive_groups} ({inactive_users}👤 {inactive_groups}👥)\n" \
          f"Total: {users_count + groups_count} ({users_count}👤 {groups_count}👥)\n" \
          f"👤 - users\n👥 - group chats(Work in Progress)\n"
    return msg


@bot.on_message(
    filters.command(commands=["today_new_users", "send_ad", "all_users_count"]) & filters.chat(chats=ADMINS_IDS))
async def handle_admins_messages(client, message):
    if message.text.lower() == "/all_users_count":
        stats = await get_all_users_count()
        await message.reply_text(stats)
    elif message.text.lower() == "/today_new_users":
        stats = await get_today_new_users()
        await message.reply_text(stats)


@bot.on_message(filters.command(commands=["start", "help"]))
async def welcome(client, message):
    await save_user_in_db(message.from_user)
    if message.text.lower() == "/start":
        await message.reply_text(f'Hello {message.from_user.first_name}!'
                                 f' I can find any music you want\nJust send me the search query')
    else:
        await message.reply_text("Send me a search query, or mention me in any chat you want,"
                                 " in the following form: @salvatoremuzbot Artist name - Song title")


@bot.on_callback_query()
async def answer(client, callback_query):
    try:
        if callback_query.data == "PREV_PAGE":
            try:
                if pages_dict[callback_query.message.chat.id] - 1 <= 0:
                    await callback_query.answer("⛔ No way back")
                    return
                else:
                    pages_dict[callback_query.message.chat.id] -= 1
            except Exception as e:
                print(e)
                pages_dict[callback_query.message.chat.id] = 1
            audios = await find_audio(callback_query.message.text, YT_MUSIC_DATABASE_CHANNEL_ID,
                                      page=pages_dict[callback_query.message.chat.id])
            await callback_query.message.edit_reply_markup(audios_markup(audios,
                                                                         pages_dict[callback_query.message.chat.id]))
        elif callback_query.data == "NEXT_PAGE":
            try:
                if len(callback_query.message.reply_markup.inline_keyboard) != ELEMENTS_PER_PAGE + 1:
                    await callback_query.answer("⛔ No way further")
                    return
                else:
                    pages_dict[callback_query.message.chat.id] += 1
            except Exception as e:
                print(e)
                pages_dict[callback_query.message.chat.id] = 1
            audios = await find_audio(callback_query.message.text, YT_MUSIC_DATABASE_CHANNEL_ID,
                                      page=pages_dict[callback_query.message.chat.id])
            if len(audios) == 0:
                pages_dict[callback_query.message.chat.id] -= 1
                await callback_query.answer("⛔ No way further")
            else:
                await callback_query.message.edit_reply_markup(audios_markup(audios,
                                                                             pages_dict[
                                                                                 callback_query.message.chat.id]))
        elif callback_query.data == "PAGES":
            await callback_query.answer()
        elif callback_query.data.isdigit():
            msg = await forward_audio(int(callback_query.data), KEK_MUSIC_DATABASE_CHANNEL_ID,
                                      YT_MUSIC_DATABASE_CHANNEL_ID)
            final_msg = await client.forward_messages(
                chat_id=callback_query.message.chat.id,
                from_chat_id=KEK_MUSIC_DATABASE_CHANNEL_ID,
                message_ids=msg.message_id,
                as_copy=True,
            )
            await client.edit_message_caption(final_msg.chat.id, final_msg.message_id,
                                              "[𝑺𝒂𝒍𝒗𝒂𝒕𝒐𝒓𝒆𝑴𝒖𝒛](https://t.me/salvatoremuzbot)🥀")
            await callback_query.answer()
        else:
            await callback_query.answer("⛔ Something went wrong")
    except Exception as e:
        print(e)
        await callback_query.answer("⛔ Something went wrong")


@bot.on_message(filters.text & ~filters.channel)
async def echo(client, message):
    search_message = await client.send_message(message.chat.id, "Searching...")
    try:
        audios = await find_audio(message.text, YT_MUSIC_DATABASE_CHANNEL_ID)
        if len(audios) == 0:
            raise EmptyResponse
        pages_dict[message.chat.id] = 1
        await message.reply_text(message.text, reply_markup=audios_markup(audios, pages_dict[message.chat.id]))
    except EmptyResponse:
        await message.reply_text("Please send valid query")
    except Exception as e:
        print("Something went wrong:", e)
        await message.reply_text("Something went wrong, please try again later")
    await search_message.delete()
    # await bot.delete_messages(message.chat.id, search_message.message_id)


def audios_markup(audios, curr_page):
    keyboard = []
    for audio in audios:
        elem_title = f"{audio.audio.title} - {audio.audio.performer}"
        try:
            time = str(datetime.timedelta(seconds=audio.audio.duration))
            if time.startswith("0:"):
                elem_title += f" | {time[2:]}"
            else:
                elem_title += f" | {time}"
        except Exception as e:
            print(e)
        keyboard.append([InlineKeyboardButton(text=elem_title, callback_data=str(audio.message_id))])

    if len(audios) == ELEMENTS_PER_PAGE:
        controls = []
        if curr_page != 1:
            controls.append(InlineKeyboardButton(text="<<", callback_data="PREV_PAGE"))
        controls += [InlineKeyboardButton(text=f"{curr_page}", callback_data="PAGES"),
                     InlineKeyboardButton(text=">>", callback_data="NEXT_PAGE"), ]
        keyboard.append(controls)
    elif len(audios) != ELEMENTS_PER_PAGE and curr_page != 1:
        controls = [InlineKeyboardButton(text="<<", callback_data="PREV_PAGE"),
                    InlineKeyboardButton(text=f"{curr_page}", callback_data="PAGES")]
        keyboard.append(controls)

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup


if __name__ == '__main__':
    app.start()
    bot.run()
    app.stop()
