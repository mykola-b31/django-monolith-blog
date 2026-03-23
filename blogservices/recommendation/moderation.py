import logging
import json
from statistics import correlation

import requests
import os
from nltk import download
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import Counter

from db import create_recommendation
import aiormq

from recommendation.main import analyzer

download('vader_lexicon')
download('punkt')
download('stopwords')
download('punkt_tab')

logger = logging.getLogger("RECOMMENDATION_SERVICE.MODERATION")
logging.basicConfig(level=logging.INFO)

analyzer = SentimentIntensityAnalyzer()

def text_has_positive_sentiment(text):
    scores = analyzer.polarity_scores(text)
    sentiment = 1 if scores['pos'] > 0 else 0
    return sentiment == 1

def text_top_5_tags(text):
    stop_words = set(stopwords.words('english'))
    tokens = word_tokenize(str.lower(text))
    filtered_tokens = [word for word in tokens if word not in stop_words and word.isalpha()]
    word_freq = Counter(filtered_tokens)

    return [word for word, freq in word_freq.most_common(5)]

async def moderate_blog_post(message: aiormq.abc.DeliveredMessage):
    try:
        body = json.loads(message.body.decode())
        blog_post_uri = body["body"]["post"]["uri"]
        blog_post_id = body['body']['post']['id']
        correlation_id = body['correlationId']
        author_id = body['body']['post']['author']['id']

        response = requests.get(os.environ['BLOG_API_URL'] + blog_post_uri)
        if response.status_code != 200:
            logger.error("Failed to get post information from API", response.text, "status code:", response.status_code)

            await message.channel.basic_nack(
                message.delivery.delivery_tag,
                requeue=False
            )
        else:
            blog_text = response.json()['text']

            logger.info("Processing new message: %s" % correlation_id)

            positive_sentiment = text_has_positive_sentiment(blog_text)
            logger.info("Message processed: %s" % correlation_id)
            logger.info("Text has positive statement [bool]: %s" % positive_sentiment)

            await message.channel.basic_ack(
                message.delivery.delivery_tag
            )

            if positive_sentiment:
                create_recommendation({
                    "author": author_id,
                    "post_id": blog_post_id,
                    "tags": text_top_5_tags(blog_text)
                })

                await message.channel.basic_publish(
                    exchange=os.environ['EVENT_EXCHANGE'],
                    routing_key=['ROUTING_KEY_NOTIFICATION'],
                    body=json.dumps({
                        'correlationId': correlation_id,
                        'body': {
                            'event': 'BLOG_POST_MODERATED',
                            'post': {
                                'id': blog_post_id,
                                'author': {
                                    'id': author_id
                                },
                                'uri': blog_post_uri
                            },
                            'moderation': {
                                'sentiment': {
                                    'positive': positive_sentiment
                                },
                                'recommend': positive_sentiment == True
                            }
                        }
                    }).encode('utf-8'),
                    properties=aiormq.spec.Basic.Properties(
                        delivery_mode=1
                    )
                )
    except Exception as e:
        logger.exception(e)
        await message.channel.basic_nack(
            message.delivery.delivery_tag,
            requeue=False
        )