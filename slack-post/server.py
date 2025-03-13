from flask import Flask, request, jsonify
from slack_sdk import WebClient
import os
import json

app = Flask(__name__)

# Load Slack token from JSON file
json_file = os.path.join(os.getcwd(), "slack_token.json")
try:
    slack_token = json.load(open(json_file)).get("token")
    if not slack_token:
        raise ValueError("Token not found.")
    print("Slack token loaded.")
except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
    print(f"Error loading token: {e}")
    slack_token = None

# Initialize Slack client
client = WebClient(token=slack_token) if slack_token else None


@app.route('/book', methods=['POST'])
def receive_message():
    """Handles incoming requests and sends notifications to Slack."""
    data = request.json.get("url")
    if not data:
        return jsonify({"error": "Missing URL"}), 400

    if send_to_group_channel(data):
        return jsonify({"message": "Notification sent"}), 200
    return jsonify({"error": "Failed to send message"}), 500


def send_to_group_channel(url):
    """Sends a message to the Slack channel."""
    if not client:
        print("Slack client not initialized.")
        return False
    try:
        client.chat_postMessage(
            channel="#ticketmaster-notifications",
            text=f"З'явились нові квитки!\n*URL:* {url}",
            parse="mrkdwn"
        )
        return True
    except Exception as e:
        print(f"Error sending message: {e}")
        return False


if __name__ == '__main__':
    app.run(debug=True, port=4040)
