#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.
from __future__ import print_function
import logging
import re
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import datetime
import pytz
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


creds = None
# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

hoy_d = datetime.datetime.now().date()
hoy = hoy_d.strftime("%Y-%m-%d")
ayer = (hoy_d - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
manana = (hoy_d + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

async def leToca(dia):
    try:
        service = build('calendar', 'v3', credentials=creds)

        calendarId = "4ae69e1030d277ffe0ad6a14c42bc4cf6d1fc4522ec707a122b3e31d4d239822@group.calendar.google.com"
        
        mexico_city_tz = pytz.timezone('America/Mexico_City')
        dia_d = datetime.datetime.strptime(dia, "%Y-%m-%d").date()
        dia_a_medianoche = mexico_city_tz.localize(datetime.datetime.combine(dia_d, datetime.time(0, 0))).isoformat()

        print(dia_d)

        events_result = service.events().list(calendarId=calendarId, timeMin=dia_a_medianoche,
                                              maxResults=1, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
            return

        for event in events:
            return event['summary']

    except HttpError as error:
        print('An error occurred: %s' % error)

# Handle messages according to RegEx
async def handleMessages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    user = update.effective_user
    text = update.effective_message.text
    reply = "error"
    
    if re.match("@BandaQuixoteBot ", text):

        if re.match(".*toca.*hoy.*|.*hoy.*toca.*", text):
            toca = await leToca(hoy)
            reply = rf"Hoy le toca publicar a {toca}"
        elif re.match(".*tocaba.*ayer.*|.*toca.*ayer.*", text):
            toca = await leToca(ayer)
            reply = rf"Ayer le tocaba publicar a {toca}"
        elif re.match(".*toca.*mañana.*|.*tocará.*mañana.*", text):
            toca = await leToca(manana)
            reply = rf"Mañana le toca publicar a {toca}"
        else:
            toca = await leToca("2023-08-23")
            reply = rf"Aun soy un bot bebé... no tengo idea de lo que me dices "+ u"\U0001F625"
 
        await update.effective_message.reply_html(reply)

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.effective_message.reply_html(
        rf"Hola {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.effective_message.reply_text("Help!")

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(open('telegram_token.txt').readlines()[0]).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handleMessages))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()