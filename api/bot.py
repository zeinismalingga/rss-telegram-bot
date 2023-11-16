import requests
import json
import feedparser
import ssl
from flask import Flask, jsonify
from pymongo import MongoClient

if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

bot_token = '1062055797:AAEmRgWMc9zPFPLogiQ1pXS2qmV44E8Ath0'
rss_feed_urls = ['https://www.upwork.com/ab/feed/topics/rss?securityToken=d563174036881b0d3a3472af4b66fe610888ee090c48b0fe655700ddfc441eda4e398733d264804b71627d8d4a48eba8cdda988da5470eb73c8424cd5815dbec&userUid=1310828478425313280&orgUid=1310828478429507585&topic=6314726',
                 'https://www.upwork.com/ab/feed/topics/rss?securityToken=d563174036881b0d3a3472af4b66fe610888ee090c48b0fe655700ddfc441eda4e398733d264804b71627d8d4a48eba8cdda988da5470eb73c8424cd5815dbec&userUid=1310828478425313280&orgUid=1310828478429507585&topic=6705447']
chat_id = '1066141419'

# Connect to MongoDB
client = MongoClient(
    "mongodb+srv://admin:rcqjCOEwOG7SAgzf@rss-upwork.qfjtuk7.mongodb.net/?retryWrites=true&w=majority")

# Specify the database and collection
db = client['rss-upwork']
collection = db['rss']


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    })
    headers = {
        'Content-Type': 'application/json'
    }
    telegram_response = requests.request(
        "POST", url, headers=headers, data=payload)
    return telegram_response


app = Flask(__name__)


@app.route('/bot')
def run_bot():
    for rss_feed_url in rss_feed_urls:
        feed = feedparser.parse(rss_feed_url)
        if feed.entries:
            latest_entry = feed.entries[0]
            title = latest_entry.title
            link = latest_entry.link
            description = latest_entry.description

            # Check if the latest entry is different from the stored one
            stored_info = collection.find_one({'rss_feed_url': rss_feed_url})
            if stored_info and stored_info.get('title') == title:
                continue

            # Remove html tags from description
            description = description.replace(
                '<br />', '\n').replace('<br /><br />', '\n')

            message = f"<b>Title</b>: {title}\n<b>Description</b>: {description}\n\n<b>Link</b>: {link}"
            telegram_response = send_telegram_message(message)
            print(telegram_response.text)

            # Update or insert the stored information for this RSS feed
            collection.update_one(
                {'rss_feed_url': rss_feed_url},
                {'$set': {'title': title}},
                upsert=True
            )

    return jsonify({'status': 'success', 'message': 'Bot script executed successfully.'})


if __name__ == '__main__':
    # Run the Flask app on http://127.0.0.1:5000/
    app.run()
