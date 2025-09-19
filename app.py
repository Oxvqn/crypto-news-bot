from flask import Flask, render_template, request
import feedparser
import openai
import os
import requests
import tweepy

app = Flask(__name__)

# Environment variables
openai.api_key = os.environ.get("OPENAI_API_KEY")
twitter_bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")

# Coins to filter
coins = ["XRP", "BTC", "ETH", "MC"]

# Twitter client
twitter_client = tweepy.Client(bearer_token=twitter_bearer_token)

# Binance-style summarization function
def summarize_news_binance_style(text):
    prompt = f"""
    Rewrite the following crypto news in a Binance-style format:
    - Use engaging and concise sentences.
    - Include emojis for excitement, warnings, or trends.
    - Highlight coin symbols like $XRP, $BTC, $ETH.
    - Make it easy to read and copy-paste.

    Original News:
    {text}

    Output:
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        rewritten_news = response['choices'][0]['message']['content'].strip()
        return rewritten_news
    except Exception as e:
        print(f"Error summarizing news: {e}")
        return text  # fallback

# Fetch RSS news
def fetch_rss_news():
    urls = [
        "https://cointelegraph.com/rss",  # example RSS feed
        "https://www.coindesk.com/arc/outboundfeeds/rss/"
    ]
    news_items = []
    for url in urls:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            summary = summarize_news_binance_style(entry.get("summary", entry.get("title", "")))
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "summary": summary,
                "source": feed.feed.title,
                "date": entry.get("published", ""),
                "image": entry.get("media_content", [{}])[0].get("url", "")
            })
    return news_items

# Fetch Twitter/X news (optional)
def fetch_twitter_news():
    usernames = ["Cointelegraph", "CoinDesk"]
    news_items = []
    for user in usernames:
        tweets = twitter_client.get_users_tweets(id=twitter_client.get_user(username=user).data.id, max_results=5)
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
    return news_items

@app.route("/", methods=["GET"])
def index():
    selected_coin = request.args.get("coin", "")
    rss_news = fetch_rss_news()
    twitter_news = fetch_twitter_news()
    news = rss_news + twitter_news

    if selected_coin:
        news = [n for n in news if selected_coin in n["title"] or selected_coin in n["summary"]]

    return render_template("index.html", news=news, coins=coins, selected_coin=selected_coin)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
