from flask import Flask, render_template, request
import feedparser
import requests
import tweepy
import openai
import datetime

# ================= CONFIG =================
openai.api_key = "YOUR_OPENAI_API_KEY"
TWITTER_BEARER_TOKEN = "YOUR_TWITTER_BEARER_TOKEN"

# Twitter client
client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)

RSS_FEEDS = {
    "CoinTelegraph": "https://cointelegraph.com/rss",
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/"
}

COINS = ["XR", "BTC", "ETH"]
# ==========================================

app = Flask(__name__)

# ---------- Helper Functions ----------
def summarize_text(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"Summarize this in 2 sentences:\n{text}"}],
            max_tokens=60
        )
        summary = response['choices'][0]['message']['content'].strip()
        return summary
    except:
        return text[:200] + "..."

def fetch_rss_news():
    news_list = []
    for source, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            image = entry.get("media_content", [{"url": ""}])[0]["url"]
            summary = summarize_text(entry.summary)
            date = entry.get("published", str(datetime.datetime.now()))
            news_list.append({
                "title": entry.title,
                "source": source,
                "date": date,
                "summary": summary,
                "link": entry.link,
                "image": image
            })
    return news_list

def fetch_twitter_news():
    news_list = []
    accounts = ["Cointelegraph", "CoinDesk"]
    for account in accounts:
        try:
            user = client.get_user(username=account)
            tweets = client.get_users_tweets(id=user.data.id, max_results=5, tweet_fields=["created_at"])
            for tweet in tweets.data:
                summary = summarize_text(tweet.text)
                news_list.append({
                    "title": tweet.text[:50]+"...",
                    "source": f"Twitter - {account}",
                    "date": tweet.created_at,
                    "summary": summary,
                    "link": f"https://twitter.com/{account}/status/{tweet.id}",
                    "image": ""
                })
        except:
            continue
    return news_list

# ---------- Routes ----------
@app.route('/')
def index():
    coin_filter = request.args.get('coin', None)
    rss_news = fetch_rss_news()
    twitter_news = fetch_twitter_news()
    news = rss_news + twitter_news

    # Filter by coin
    if coin_filter:
        news = [n for n in news if coin_filter.upper() in n["title"].upper()]

    news.sort(key=lambda x: x["date"], reverse=True)

    return render_template('index.html', news=news, coins=COINS, selected_coin=coin_filter)

# ---------- Run App ----------
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use Render's assigned port
    app.run(host="0.0.0.0", port=port, debug=True)

