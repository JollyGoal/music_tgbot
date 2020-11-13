import config as conf  # custom configurations
from pyrogram import Client
import asyncio

api_id = conf.API_ID
api_hash = conf.API_HASH


# app = Client("music_session", api_id, api_hash, phone_number=conf.PHONE_NUMBER)

class UserClass:
    app = Client("music_session", api_id, api_hash, phone_number=conf.PHONE_NUMBER)

    async def find_audio(self, query, page=1):
        page = page - 1
        print('start')
        async with self.app:
            messages = []
            async for message in self.app.search_messages(conf.YT_MUSIC_DATABASE_CHANNEL_ID, query=query,
                                                          limit=conf.ELEMENTS_PER_PAGE,
                                                          offset=page * conf.ELEMENTS_PER_PAGE):
                messages.append(message)
        print('ff')
        return messages


if __name__ == '__main__':
    user_class = UserClass()
    user_class.app.run(user_class.find_audio(query="Lion"))
