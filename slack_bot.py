import slack
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter


# cuts out the white space of a word by splitting it using Regular Expressions
def prepForModeration(word):
    split_word = re.split("\d*|\W*", word)
    new_word = "".join(split_word)
    final_word = new_word.lower()
    return final_word

#checks for any of the words in the array and returns something that isn't -1 if it finds it
def containsNaughtyWord(word):
    new_word = prepForModeration(word)
    naughtyWords = ["shit", "fuck", "nigger", "faggot", "fuk", "fuc" ]
    for swear_word in naughtyWords:
        result = new_word.find(swear_word)
        if result != -1:
            return result

# Logs into Slack as an admin to delete messages
def deleteMessage(channel_id, time_stamp):
    admin_client = slack.WebClient(token=os.environ['ADMIN_TOKEN'])
    admin_client.chat_delete(channel=channel_id, ts=time_stamp)

# Searches a message string for the USER ID of the user mentioned
def findUserID(string):
    index = string.find("@")
    user_id = string[index+1:index+11]
    return user_id


env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter( os.environ['SIGNING_SECRET'],'/slack/events',app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']

message_counts = {}

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
            user_id = event.get('user')
            print(user_id)
            if containsNaughtyWord(text) != None:
                ts = event.get('ts')
                client.chat_postMessage(channel='#bot-logs', text="Bad message detected")
                deleteMessage(channel_id, ts)
            else:
                if user_id in message_counts:
                    message_counts[user_id] += 1
                else: 
                    message_counts[user_id] = 1

@app.route('/message-count', methods=['POST'])
def message_count():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')
    message_count = message_counts.get(user_id, 0)

    client.chat_postMessage(channel=channel_id, text=f"Message: {message_count}")
    return Response(), 200

if __name__ == "__main__":
    app.run(debug=True)

