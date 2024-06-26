from flask import Flask, request, Response 
from slack_sdk import WebClient
from slackeventsapi import SlackEventAdapter
from slack_sdk.errors import SlackApiError
import sys, os
import requests

app = Flask(__name__)
to_run = True
# Set up Slack API client
slack_token = "xoxb-773919780944-6545227300720-mTgMldXEyDqgieEMPTN75tPf"
slack_signing_secret = '89686c150358a5bd66fdd4030011b884'
client = WebClient(token=slack_token)
slack_events_adapter = SlackEventAdapter(slack_signing_secret, "/slack/events", app)

# Stops the 
@app.route('/stop', methods=['POST'])
def stop_server():
    print("Received stop request. Stopping server...")
    global to_run
    to_run = False
    return "Sever stopped!"


@app.route('/start', methods=['POST'])
def start_server():
    print("Received start request. Starting server...")
    global to_run
    to_run = True
    return "Server started!"


@app.route('/book', methods=['POST'])
def receive_message():
    if to_run:
        send_to_group_channel(request.json['url'])


def send_to_group_channel(data):
    client.chat_postMessage(
        channel="#ticketmaster-notifications",
        text=f"З'явилась нові квитки!" + f"\n*url:* {data}",
        parse="mrkdwn"
    )

if __name__ == '__main__':
    app.run(debug=True, port=4040)
