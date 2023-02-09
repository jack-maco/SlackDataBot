import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

#Bot user OAuth token (stored in local env var)
slack_token = os.environ.get('SLACK_BOT_TOKEN')

client = WebClient(token=slack_token)

try:
    #posting a message in #slackdatadev channel                     WORKS
#    response=client.chat_postMessage(
#        channel="slackdatadev", text="Bot's first message"
#    )
    #sending a message to a particular user                         WORKS         
#    response = client.chat_postEphemeral(
#        channel="slackdatadev", 
#        text="Hello Oscar",
#        user="U026SEU4W8H"
#    )
    #Get basic info of the channel where out Bot has access
#    response = client.conversations_info(
#        channel="C04NJCDBWH2"
#    )
#    print(response)
    #Get a list of conversations
#    response = client.conversations_list()
#    print(response['channels'])

    response = client.conversations_history(
        channel="C04NJCDBWH2"
    )
    for x in (response['messages']):
        print(f'\n{x}')

except SlackApiError as e:
#    assert e.response["error"]
    print(e)