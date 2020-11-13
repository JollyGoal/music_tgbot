import config as conf  # custom configurations
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import datetime
import os
import math

api_id = conf.API_ID
api_hash = conf.API_HASH

pages_dict = {}

app = Client("music_session", api_id, api_hash, phone_number=conf.PHONE_NUMBER)
bot = Client("bot_session", api_id, api_hash, bot_token=conf.BOT_TOKEN)


class EmptyResponse(Exception):
    pass


async def find_audio(query, chat_id, page=1):
    page = page - 1
    async with app:
        messages = []
        async for message in app.search_messages(chat_id, query=query, limit=conf.ELEMENTS_PER_PAGE,
                                                 offset=page * conf.ELEMENTS_PER_PAGE):
            messages.append(message)
    return messages


async def forward_audio(message_ids, chat_id, from_chat_id):
    async with app:
        msg = await app.forward_messages(
            chat_id=chat_id,
            from_chat_id=from_chat_id,
            message_ids=message_ids,
            as_copy=False,
        )
    return msg


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
            await callback_query.message.edit_reply_markup(audios_markup(audios,
                                                                         pages_dict[callback_query.message.chat.id]))
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


@bot.on_message(filters.text & filters.private)
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
    bot.run()
