import feedparser
import time

def fetch_all_feeds(feed_urls):
    """
    Fetches news items from a list of RSS URLs.
    Returns a combined list of news dictionaries:
    { 'title': ..., 'link': ..., 'published': ..., 'summary': ..., 'source': ... }
    """
    all_news = []
    
    for url in feed_urls:
        try:
            feed = feedparser.parse(url)
            source_title = feed.feed.get('title', 'Unknown Source')
            
            # Limit to latest 5 entries per feed to avoid token overflow
            for entry in feed.entries[:5]:
                # Basic filtering or limit could go here
                news_item = {
                    'title': entry.get('title', 'No Title'),
                    'link': entry.get('link', '#'),
                    'published': entry.get('published', entry.get('updated', '')),
                    'summary': entry.get('summary', ''),
                    'source': source_title
                }
                all_news.append(news_item)
        except Exception as e:
            print(f"Error parsing feed {url}: {e}")
            continue
            
    return all_news
