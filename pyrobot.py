from time import time

import config as conf  # custom configurations
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import datetime
import asyncio

api_id = conf.API_ID
api_hash = conf.API_HASH

pages_dict = {}

app = Client("music_session", api_id, api_hash, phone_number=conf.PHONE_NUMBER)
bot = Client("bot_session", api_id, api_hash, bot_token=conf.BOT_TOKEN)


class EmptyResponse(Exception):
    pass


async def find_audio(query, chat_id, page=1):
    page = page - 1
    # async with app:
    messages = []
    async for message in app.search_messages(chat_id, query=query, limit=conf.ELEMENTS_PER_PAGE,
                                             offset=page * conf.ELEMENTS_PER_PAGE):
        messages.append(message)
    return messages


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
    async for message in app.search_messages(conf.USERS_DATABASE_CHANNEL_ID, query=f"{user.id}",
                                             limit=999):
        if message.message_id != 25 and message.text.startswith(f"ID: {user.id}"):
            users_data.append(message)
    msg = f"ID: {user.id}\nIs bot?: {user.is_bot}\nFirst name: {user.first_name}" \
          f"\nLast name: {user.last_name}\nUsername: @{user.username}\nIs active: True"
    if len(users_data) == 0:
        await bot.send_message(conf.USERS_DATABASE_CHANNEL_ID, msg)
    elif len(users_data) == 1:
        try:
            await users_data[0].edit_text(msg)

        except Exception as e:
            print(e)
            pass
    else:
        for single_user_data in users_data:
            await single_user_data.delete()
        await bot.send_message(conf.USERS_DATABASE_CHANNEL_ID, msg)


@bot.on_message(filters.new_chat_members & filters.left_chat_member)
async def handle_groups(client, message):
    pass


async def get_all_users_count():
    users_count = 0
    active_users = 0
    inactive_users = 0
    groups_count = 0
    active_groups = 0
    inactive_groups = 0

    async for message in app.iter_history(conf.USERS_DATABASE_CHANNEL_ID):
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

    async for message in app.iter_history(conf.USERS_DATABASE_CHANNEL_ID):
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
          f"👤 - users\n👥 - group chats\n"
    return msg


@bot.on_message(
    filters.command(commands=["today_new_users", "send_ad", "all_users_count"]) & filters.chat(chats=conf.ADMINS_IDS))
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
                                 " in the following form: @kekmusic_bot Artist name - Song title")


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
            audios = await find_audio(callback_query.message.text, conf.YT_MUSIC_DATABASE_CHANNEL_ID,
                                      page=pages_dict[callback_query.message.chat.id])
            await callback_query.message.edit_reply_markup(audios_markup(audios,
                                                                         pages_dict[callback_query.message.chat.id]))
        elif callback_query.data == "NEXT_PAGE":
            try:
                if len(callback_query.message.reply_markup.inline_keyboard) != conf.ELEMENTS_PER_PAGE + 1:
                    await callback_query.answer("⛔ No way further")
                    return
                else:
                    pages_dict[callback_query.message.chat.id] += 1
            except Exception as e:
                print(e)
                pages_dict[callback_query.message.chat.id] = 1
            audios = await find_audio(callback_query.message.text, conf.YT_MUSIC_DATABASE_CHANNEL_ID,
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
            msg = await forward_audio(int(callback_query.data), conf.KEK_MUSIC_DATABASE_CHANNEL_ID,
                                      conf.YT_MUSIC_DATABASE_CHANNEL_ID)
            final_msg = await client.forward_messages(
                chat_id=callback_query.message.chat.id,
                from_chat_id=conf.KEK_MUSIC_DATABASE_CHANNEL_ID,
                message_ids=msg.message_id,
                as_copy=True,
            )
            await client.edit_message_caption(final_msg.chat.id, final_msg.message_id, "[KeK Music](t.me/kekmusic_bot)")
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
        audios = await find_audio(message.text, conf.YT_MUSIC_DATABASE_CHANNEL_ID)
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

    if len(audios) == conf.ELEMENTS_PER_PAGE:
        controls = []
        if curr_page != 1:
            controls.append(InlineKeyboardButton(text="<<", callback_data="PREV_PAGE"))
        controls += [InlineKeyboardButton(text=f"{curr_page}", callback_data="PAGES"),
                     InlineKeyboardButton(text=">>", callback_data="NEXT_PAGE"), ]
        keyboard.append(controls)
    elif len(audios) != conf.ELEMENTS_PER_PAGE and curr_page != 1:
        controls = [InlineKeyboardButton(text="<<", callback_data="PREV_PAGE"),
                    InlineKeyboardButton(text=f"{curr_page}", callback_data="PAGES")]
        keyboard.append(controls)

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup


if __name__ == '__main__':
    app.start()
    bot.run()
    app.stop()
