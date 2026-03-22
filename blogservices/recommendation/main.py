import json
import logging
import os

import nltk
import pika
import requests
from dotenv import load_dotenv
from nltk.sentiment import SentimentIntensityAnalyzer
from pika.compat import url_unquote

nltk.download("vader_lexicon")

analyzer = SentimentIntensityAnalyzer()
load_dotenv()

AMQP_HOST = os.getenv("AMQP_HOST")
QUEUE = os.getenv("RECOMMENDATION_QUEUE")
DLQ_NAME = os.getenv("DLQ_RECOMMENDATION")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def text_has_positive_sentiment(text):
    scores = analyzer.polarity_scores(text)
    sentiment = (
        1 if scores["pos"] > 0 else 0
    )
    return sentiment == 1

debug = False

def moderate_blog_post(ch, method, properties, body):
    try:
        message = json.loads(body.decode())
        blog_post_id = message["body"]["post"]["id"]
        blog_post_uri = message["body"]["post"]["uri"]
        author_id = message["body"]["post"]["author"]["id"]
        author_username = message["body"]["post"]["author"]["username"]
        author_email = message["body"]["post"]["author"]["email"]
        correlation_id = message["correlationId"]
        logger.info(f"Post {blog_post_uri}, author_email: {author_email}, author_id: {author_id}, correlation_id: {correlation_id}")
        response = requests.get(
            os.environ["BLOG_API_URL"] + blog_post_uri
        )
        if debug:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        if response.status_code != 200:
            logger.error(
                "Failed to get post information from API",
                response.text,
                "status code:",
                response.status_code,
            )
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        else:
            blog_text = response.json()["text"]
            positive_sentiment = text_has_positive_sentiment(blog_text)
            logger.info("Text has positive statement [bool] : %s" % positive_sentiment)

            if positive_sentiment:
                ch.basic_publish(
                    exchange=os.environ["EVENT_EXCHANGE"],
                    routing_key=os.environ["ROUTING_KEY_NOTIFICATION"],
                    body=json.dumps(
                        {
                             'correlationId': correlation_id,
                            'body': {
                                 'event': 'RecommendationReady',
                                 'post': {
                                     'id': blog_post_id,
                                     'uri': blog_post_uri,
                                     'author': {
                                         'id': author_id,
                                         'username': author_username,
                                         'email': author_email
                                     }
                                 },
                                 'moderation': {
                                     'sentiment': {
                                         'positive': positive_sentiment
                                     },
                                     'recommend': positive_sentiment == True
                                 }
                            }
                        }
                    )
                )
            ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.exception(e)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

if __name__ == "__main__":
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.environ["AMQP_HOST"],
            credentials=pika.credentials.PlainCredentials(
                url_unquote(os.environ["AMQP_USER"]),
                url_unquote(os.environ["AMQP_PASS"]),
            ),
        )
    )
    channel = connection.channel()
    channel.basic_consume(queue=QUEUE, on_message_callback=moderate_blog_post)

    print("[*] Waiting for blog post creation events. To exit press CTRL+C")
    channel.start_consuming()