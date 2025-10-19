import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from slackeventsapi import SlackEventAdapter

def containsNaughtyWord(word):
    naughtyWords = ["shit", "fuck", "nigger", "faggot", "fuk", "fuc" ]
    for swear_word in naughtyWords:
        result = word.find(swear_word)
        if result != -1:
            return result

def deleteMessage(channel_id, time_stamp):
    admin_client = slack.WebClient(token=os.environ['ADMIN_TOKEN'])
    admin_client.chat_delete(channel=channel_id, ts=time_stamp)

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter( os.environ['SIGNING_SECRET'],'/slack/events',app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']

@slack_event_adapter.on('message')
def message(payload):
    event = payload.get('event', {})
    channel_id = event.get('channel')
    subtype = event.get('subtype')
    if channel_id != 'C09M7V67NEA':
        if subtype == "message_deleted":
            deleted_message = event.get('previous_message')
            text = deleted_message.get('text')
            user_id = deleted_message.get('user')
            client.chat_postMessage(channel='#bot-logs', text=("Message Deleted: " + text +"\n"+user_id))
        else:
            text = event.get('text')
            if containsNaughtyWord(text) != None:
                ts = event.get('ts')
                client.chat_postMessage(channel='#bot-logs', text="Bad message detected")
                deleteMessage(channel_id, ts)


if __name__ == "__main__":
    app.run(debug=True)

