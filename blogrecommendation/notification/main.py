import json
import logging
import os
import pymongo
import pika
from dotenv import load_dotenv
from pika.compat import url_unquote
import smtplib


load_dotenv()

AMQP_HOST = os.getenv("AMQP_HOST")
QUEUE = os.getenv("NOTIFICATION_QUEUE")
DLQ_NAME = os.getenv("DLQ_NOTIFICATION")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

mongo_server = os.environ["EVENT_LOG_DB_URL"]
mongo_client = pymongo.MongoClient(f"mongodb://{mongo_server}/",
                                   username=os.environ['MONGO_USER'],
                                   password=os.environ['MONGO_PASS'])
subscriber_db = mongo_client[os.environ['SUBSCRIBERS_DB']]

def process_notification(ch, method, properties, body):
    try:
        message = json.loads(body.decode())
        event = message["body"]["event"]

        col = subscriber_db['subscribers']

        if event == "SubscribeNotifications":
            user_id = message["body"]["user"]["id"]
            user_email = message["body"]["user"]["email"]
            author_id = message["body"]["author_id"]

            col.update_one(
                { "id": user_id },
                {
                    "$set": { "email": user_email },
                    "$addToSet": { "subscribed_to": author_id }
                },
                upsert=True
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)

        elif event == "UnsubscribeNotifications":
            user_id = message["body"]["user"]["id"]
            author_id = message["body"]["author_id"]

            col.update_one({ "id": user_id },{"$pull": { "subscribed_to": author_id }})
            ch.basic_ack(delivery_tag=method.delivery_tag)

        elif event == "RecommendationReady":
            blog_post_uri = message["body"]["post"]["uri"]
            author_id = message["body"]["post"]["author"]["id"]
            author_name = message["body"]["post"]["author"]["username"]
            author_email = message["body"]["post"]["author"]["email"]

            subs = col.find({
                "email": { "$ne": author_email },
                "subscribed_to": author_id
            })

            mailtrap_user = os.getenv("MAILTRAP_USER")
            mailtrap_pass = os.getenv("MAILTRAP_PASS")

            sender = "Blog <blog@blog.net>"

            with smtplib.SMTP("sandbox.smtp.mailtrap.io", 2525) as server:
                server.starttls()
                server.login(mailtrap_user, mailtrap_pass)

                for receiver_doc in subs:
                    receiver_email = receiver_doc['email']

                    notification_message = f"""\
Subject: New Post
To: {receiver_email}
From: {sender}

Hi! There is a new post by {author_name} at {blog_post_uri} that is worth reading."""

                    server.sendmail(sender, receiver_email, notification_message)
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
    channel.basic_consume(queue=QUEUE, on_message_callback=process_notification)

    print("[*] Waiting for blog post creation events. To exit press CTRL+C")
    channel.start_consuming()