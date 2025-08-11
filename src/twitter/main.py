# Having issue with this. Can't get bookrmars programmatically.

import os
import tweepy
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()

client = tweepy.Client(
    consumer_key=os.getenv('TWITTER_CONSUMER_KEY'),
    consumer_secret=os.getenv('TWITTER_CONSUMER_SECRET'),
    access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
    access_token_secret=os.getenv('TWITTER_SECRET_TOKEN')
)
# getting this error
# An error occurred: Access Token must be provided for OAuth 2.0 Authorization Code Flow with PKCE

# client = tweepy.Client(bearer_token=os.getenv('TWITTER_BEARER_TOKEN'))
# getting this error
# An error occurred: 403 Forbidden
# Authenticating with OAuth 2.0 Application-Only is forbidden for this endpoint.  Supported authentication types are [OAuth 1.0a User Context, OAuth 2.0 User Context].

def get_recent_bookmarks(days=7):
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    recent_bookmarks = []
    pagination_token = None

    try:
        while True:
            # Fetch bookmarks with tweet fields including created_at
            response = client.get_bookmarks(
                max_results=2,
                pagination_token=pagination_token,
                tweet_fields=['created_at', 'author_id', 'public_metrics', 'context_annotations'],
                expansions=['author_id'],
                user_fields=['username', 'name', 'verified']
            )

            if not response.data:
                break

            # Filter bookmarks by date
            for tweet in response.data:
                tweet_date = tweet.created_at
                if tweet_date >= cutoff_date:
                    recent_bookmarks.append(tweet)
                else:
                    # Since bookmarks are returned in reverse chronological order,
                    # we can stop when we hit an older tweet
                    return recent_bookmarks

            # Check if there are more pages
            if 'next_token' in response.meta:
                pagination_token = response.meta['next_token']
            else:
                break

    except tweepy.TooManyRequests:
        print("Rate limit exceeded. Please wait before making more requests.")
    except tweepy.Unauthorized:
        print("Unauthorized. Check your authentication credentials.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return recent_bookmarks

recent_bookmarks = get_recent_bookmarks(days=7)
