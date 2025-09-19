from flask import Flask, render_template, request
import feedparser
import os
import tweepy
from openai import OpenAI
import random
import datetime

app = Flask(__name__)

# Environment variables
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
twitter_bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")

# Coins to filter
coins = ["XRP", "BTC", "ETH", "MC"]

# Twitter client
twitter_client = tweepy.Client(bearer_token=twitter_bearer_token)

# Binance-style summarization function using GPT-3.5
def summarize_news_binance_style(text):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    prompt = f"""
Rewrite the following crypto news to **look exactly like a Binance news post**:
- Short, punchy sentences.
- Include emojis for excitement, warnings, and trends.
- Highlight coins using symbols like $XRP, $BTC, $ETH.
- Easy to read and copy-paste-friendly.
- Make it slightly different each time.
- Keep it concise, max 2-3 lines if possible.

Original News:
{text}

Timestamp: {timestamp}

Output:
"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.85,
            max_tokens=150
        )
        rewritten_news = response.choices[0].message.content.strip()
        return rewritten_news
    except Exception as e:
        print(f"Error summarizing news: {e}")
        return text  # fallback

# Fetch RSS news
def fetch_rss_news():
    urls = [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/"
    ]
    news_items = []
    for url in urls:
        feed = feedparser.parse(url)
        for entry in feed.entries[:15]:
            summary = summarize_news_binance_style(entry.get("summary", entry.get("title", "")))
            image = ""
            media_content = entry.get("media_content")
            if media_content and len(media_content) > 0:
                image = media_content[0].get("url", "")
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "summary": summary,
                "source": feed.feed.title,
                "date": entry.get("published", ""),
                "image": image
            })
    return news_items

# Fetch Twitter/X news safely
def fetch_twitter_news():
    usernames = ["Cointelegraph", "CoinDesk"]
    news_items = []
    for user in usernames:
        try:
            user_id = twitter_client.get_user(username=user).data.id
            tweets = twitter_client.get_users_tweets(id=user_id, max_results=5)
            if tweets.data:
                for tweet in tweets.data:
                    summary = summarize_news_binance_style(tweet.text)
                    news_items.append({
                        "title": tweet.text[:50]+"...",
                        "link": f"https://twitter.com/{user}/status/{tweet.id}",
                        "summary": summary,
                        "source": f"Twitter/{user}",
                        "date": tweet.created_at if hasattr(tweet,'created_at') else "",
                        "image": ""
                    })
        except tweepy.TooManyRequests:
            print(f"Rate limit reached for {user}, skipping.")
        except Exception as e:
            print(f"Error fetching tweets for {user}: {e}")
    return news_items

@app.route("/", methods=["GET"])
def index():
    selected_coin = request.args.get("coin", "")
    rss_news = fetch_rss_news()
    twitter_news = fetch_twitter_news()

    # Combine and shuffle news for dynamic display
    all_news = rss_news + twitter_news
    random.shuffle(all_news)

    # Filter by coin if selected
    if selected_coin:
        all_news = [n for n in all_news if selected_coin in n["title"] or selected_coin in n["summary"]]

    # Limit displayed news items
    all_news = all_news[:10]

    return render_template("index.html", news=all_news, coins=coins, selected_coin=selected_coin)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
