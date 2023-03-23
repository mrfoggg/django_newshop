import asyncio
import random

from django_telethon_session.sessions import DjangoSession
from telethon import TelegramClient
from telethon.tl import functions, types

#
# sessions = DjangoSession()
# client = TelegramClient('session', api_id, api_hash).start()
#
#
# def get_tg_username(phone):
#     async def main():
#         asyncio.get_event_loop()
#         result = await client(functions.contacts.ImportContactsRequest(
#             contacts=[types.InputPhoneContact(
#                 client_id=random.randrange(-2 ** 63, 2 ** 63),
#                 phone=phone,
#                 first_name='Somee Name',
#                 last_name=''
#             )]
#         ))
#         return result.users[0].username
#
#     with client:
#         return client.loop.run_until_complete(main())
