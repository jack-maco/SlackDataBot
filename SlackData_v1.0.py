from __future__ import print_function
import os
import re
import csv
from datetime import datetime
import time

from flask import Flask, request

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from slack_bolt import App, Say
from slack_bolt.adapter.flask import SlackRequestHandler

app = Flask(__name__)

conversation_history = []

if (os.path.isfile('Dump/dump.csv')):
    with open('Dump/dump.csv', 'a', newline='') as file:
        print("File Exists")
else:
    with open('Dump/dump.csv', 'w+', newline='') as file:
        print("File Created")

#Creating client to talk with slack
client = WebClient(token=os.environ.get("SLACK_DATA_TOKEN"))

#DECLARING BOLT APP and passing auth tokens
bolt_app = App(token=os.environ.get("SLACK_DATA_TOKEN"),
signing_secret=os.environ.get("SLACK_SIGNING_SECRET"))

#======================== RESPONDERS ========================
#responds if message contains hello slackdata with hello @[user]
@bolt_app.message("hello slackdata")
def hello(payload: dict, say: Say):
    user = payload.get("user")
    say(f"Hi <@{user}>")

#responds to /help
@bolt_app.command("/help")
def help(say, ack):
    ack()
    text = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdown",
                    "text": "This is a slash command"
                }
            }
        ]
    }
    say(text=text)

#responds to request for channel
@bolt_app.message("slackdata all analytics")
def analytics(message, payload: dict, say: Say):
    user = payload.get("user")
    regChannel = re.findall('#(.*)\|', message['text'])
    channel = regChannel[0]
    message_log = history_count(channel, payload.get("ts"))
    print(f'User:<@{user}> \n Channel:<#{channel}>')
    say(f"<@{user}>, there were {message_log[channel][0]} messages and {message_log[channel][1]} thread replies in <#{channel}> in the last 24 hours.")
    say(f"<@{user}>, there were {message_log[channel][2]} messages and {message_log[channel][3]} thread replies in <#{channel}> in the last 7 days.")
    say(f"<@{user}>, there were {message_log[channel][4]} messages and {message_log[channel][5]} thread replies in <#{channel}> in the last 30 days.")

@bolt_app.message("slackdata day analytics")
def analytics(message, payload: dict, say: Say):
    user = payload.get("user")
    regChannel = re.findall('#(.*)\|', message['text'])
    channel = regChannel[0]
    message_log = history_count(channel, payload.get("ts"))
    print(f'User:<@{user}> \n Channel:<#{channel}>')
    say(f"<@{user}>, there were {message_log[channel][0]} messages and {message_log[channel][1]} thread replies in <#{channel}> in the last 24 hours.")

@bolt_app.message("slackdata week analytics")
def analytics(message, payload: dict, say: Say):
    user = payload.get("user")
    regChannel = re.findall('#(.*)\|', message['text'])
    channel = regChannel[0]
    message_log = history_count(channel, payload.get("ts"))
    print(f'User:<@{user}> \n Channel:<#{channel}>')
    say(f"<@{user}>, there were {message_log[channel][2]} messages and {message_log[channel][3]} thread replies in <#{channel}> in the last 7 days.")

@bolt_app.message("slackdata month analytics")
def analytics(message, payload: dict, say: Say):
    user = payload.get("user")
    regChannel = re.findall('#(.*)\|', message['text'])
    channel = regChannel[0]
    message_log = history_count(channel, payload.get("ts"))
    print(f'User:<@{user}> \n Channel:<#{channel}>')
    say(f"<@{user}>, there were {message_log[channel][4]} messages and {message_log[channel][5]} thread replies in <#{channel}> in the last 30 days.")

#close and output message_log dict for local testing
@bolt_app.message("slackdata testing output")
def testingOut(message, payload: dict, say: Say):
    user = payload.get("user")
    print(payload)
    regChannel = re.findall('#(.*)\|', message['text'])
    channel = regChannel[0]
    message_log = history_count(channel, payload.get("ts"))
    with open ('message_log.txt', 'w+') as file:
        for i in message_log:
            file.writelines(f'{i}        {str(message_log[i])}\n')
    say(f'Logs printed')

@bolt_app.message("slackdata userinfo")
def userInfo(payload: dict, say: Say):
    userid = payload.get("user")
    print(f'\n\n{userid}\n\n')
    result = client.users_info(user=userid)
    say(str(result))
    result = client.conversations_info(channel = (payload.get("channel")))
    say(str(result))

#======================== LISTENERS ========================
#logs all messages
@bolt_app.event("message")
def record_message_event(body, logger):
    #try for standard message logging
    try:
        corp_domains = ["homeinsteadinc.com", "joinhonor.com", "honorcare.com"]
        logger.info("body")
        workflow = False
        channel =  client.conversations_info(channel = (body["event"]["channel"]))
        user = client.users_info(user = (body["event"]["user"]))
        domainregex = re.compile(r".*@(\S+)")
        domain = domainregex.search(user['user']['profile']['email'])
        if (domain.group(1) in corp_domains):
            member = "Internal"
        else:
            member = "External"
        if (body["event"].get("thread_ts", 0) != 0):
            thread = True
        else:
            thread = False
        current_channels = []
        with open("Dump/dump.csv", "r+") as file:
            reader = csv.reader(file, delimiter=',')
            for row in reader:
                current_channels.append(row[0])
        if channel["channel"].get("name") not in current_channels:
            history(body["event"]["channel"], body["event"].get("ts", 0))
        entry = [channel["channel"].get("name"), user['user']['real_name'], user['user']['profile']['email'], member, (str(datetime.fromtimestamp(int((float(body["event"]["ts"]))//1)))), thread, workflow]
        if (os.path.isfile('Dump/dump.csv')):
            with open('Dump/dump.csv', 'a', newline='') as file:
                writer = csv.writer(file, delimiter=',')
                writer.writerow(entry)
        else:
            with open('Dump/dump.csv', 'w+', newline='') as file:
                writer = csv.writer(file, delimiter=',')

                writer.writerow(entry)
    #except for workflow detection
    except Exception as e:
        j = body["event"]
        try:
            subtype = j.get('subtype', 0)
        except:
            subtype = 0
        if subtype == 'bot_message':
                channel =  client.conversations_info(channel = (body["event"]["channel"]))
                workflow = True
                user_regex = re.compile(r".*<@(\S+)>")
                user = user_regex.search(j['text'])
                user = user.group(1)
                user_info = client.users_info(user = str(user))
                domainregex = re.compile(r".*@(\S+)")
                domain = domainregex.search(user_info['user']['profile']['email'])
                if (domain.group(1) in corp_domains):
                    member = "Internal"
                else:
                    member = "External"
                timestamp = str(datetime.fromtimestamp(int((float(j["event_ts"]))//1)))
                thread = False
                entry = [channel["channel"].get("name"), user_info['user']['real_name'], user_info['user']['profile']['email'], member, timestamp, thread, workflow]
                if (os.path.isfile('Dump/dump.csv')):
                    with open('Dump/dump.csv', 'a', newline='') as file:
                        writer = csv.writer(file, delimiter=',')
                        writer.writerow(entry)
                else:
                    with open('Dump/dump.csv', 'w+', newline='') as file:
                        writer = csv.writer(file, delimiter=',')
                        writer.writerow(entry)
        else:
            print("busted")
            print(e)
            print(body)

    #-----------------------------------------------------------------------------------------------------------------------------------------------
    #                                  IMPLEMENT CHECK FOR WEEK ON MESSAGE TO PUSH TO GOOGLE SHEETS
    #-----------------------------------------------------------------------------------------------------------------------------------------------
    #CHRON JOB FOR DATA PUSH AND CLEANUP

#======================== ANALYTICS ========================
def history(channel, current):
    corp_domains = ["homeinsteadinc.com", "joinhonor.com", "honorcare.com"]
    channel_info = client.conversations_info(channel = channel)
    channel_history = client.conversations_history(channel = channel)
    with open('history.txt', 'w+') as file:
        writer = csv.writer(file, delimiter=',')
        for i in channel_history:
            writer.writerow(i)
    try:
        file = open("Dump/dump.csv", 'a')
        print("\nFile exists, appending history...\n")
    except:
        file = open("Dump/dump.csv", 'w+')
        print("\nFile created, appending history...\n")
    writer = csv.writer(file, delimiter=',')
    for i in channel_history:
        for j in i["messages"]:
            first = next(iter(j))
            #print(f'\n{j}\n')
            if (first == "client_msg_id"):
                workflow = False
                user_info = client.users_info(user = (j["user"]))
                print(j['user'])
                domainregex = re.compile(r".*@(\S+)")
                domain = domainregex.search(user_info['user']['profile']['email'])
                if (domain.group(1) in corp_domains):
                    member = "Internal"
                else:
                    member = "External"
                timestamp = str(datetime.fromtimestamp(int((float(j["ts"]))//1)))
                print(j.get("thread_ts", 0))
                print(j.get("ts", 0))
                print()
                if j.get("reply_count", 0) != 0:
                    replies = client.conversations_replies(channel = channel, ts = j.get("ts"))
                    print(replies)
                    for k in replies["messages"]:
                        #compare ts with parent ts to determine thread, then write and do everything, then break so the rest doesnt run
                        if (k.get("ts") != j.get("ts")):
                            thread = True
                            workflow = False
                            user_info = client.users_info(user = (j["user"]))
                            print(j['user'])
                            domainregex = re.compile(r".*@(\S+)")
                            domain = domainregex.search(user_info['user']['profile']['email'])
                            if (domain.group(1) in corp_domains):
                                member = "Internal"
                            else:
                                member = "External"
                            timestamp = str(datetime.fromtimestamp(int((float(j["ts"]))//1)))
                            entry = [channel_info["channel"].get("name"), user_info['user']['real_name'], user_info['user']['profile']['email'], member, timestamp, thread, workflow]
                            writer.writerow(entry)
                        else:
                            thread = False
                    break
                else:
                    thread = False
                entry = [channel_info["channel"].get("name"), user_info['user']['real_name'], user_info['user']['profile']['email'], member, timestamp, thread, workflow]
                writer.writerow(entry)
            try:
               subtype = j.get('subtype', 0)
            except:
               subtype = 0
            if subtype == 'bot_message':
                workflow = True
                user_regex = re.compile(r".*<@(\S+)>")
                user = user_regex.search(j['text'])
                user = user.group(1)
                user_info = client.users_info(user = str(user))
                domainregex = re.compile(r".*@(\S+)")
                domain = domainregex.search(user_info['user']['profile']['email'])
                if (domain.group(1) in corp_domains):
                    member = "Internal"
                else:
                    member = "External"
                thread = False
                entry = [channel_info["channel"].get("name"), user_info['user']['real_name'], user_info['user']['profile']['email'], member, timestamp, thread, workflow]
                writer.writerow(entry)
            else:
                print("\nother type of message")
    print("\n\n COMPLETE! \n\n")

def history_count(channel, current):
    message_log = {}
    print(channel, current)
    message_log [channel] = [0, 0, 0, 0, 0, 0]
    message_count = 0
    thread_count = 0
    for i in client.conversations_history(channel=channel):
        for x in range(len(i['messages'])):
            thread = i['messages'][x].get('thread_ts', 0)
            if i['messages'][x].get('client_msg_id', 0) != 0:
                if abs(float(current) - float(i["messages"][x].get('ts', 0))) <= 86400:
                    message_log[channel][0] += 1
                if abs(float(current) - float(i["messages"][x].get('ts', 0))) <= 604800:
                    message_log[channel][2] += 1
                if abs(float(current) - float(i["messages"][x].get('ts', 0))) <= 2592000:
                    message_log[channel][4] += 1
            if thread != 0:
                if abs(float(current) - float(i["messages"][x].get('ts', 0))) <= 86400:
                    message_log[channel][1] += i["messages"][x]["reply_count"]
                if abs(float(current) - float(i["messages"][x].get('ts', 0))) <= 604800:
                    message_log[channel][3] += i["messages"][x]["reply_count"]
                if abs(float(current) - float(i["messages"][x].get('ts', 0))) <= 2592000:
                    message_log[channel][5] += i["messages"][x]["reply_count"]
    return message_log

#======================== ROUTING ========================
handler = SlackRequestHandler(bolt_app)

@app.route("/slackdata/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)