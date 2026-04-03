import json
import logging
import time

import pymongo
import os
import pika
from pika.compat import url_unquote
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)

mongo_server = os.environ['EVENT_LOG_DB_URL']
mongo_client = pymongo.MongoClient(f"mongodb://{mongo_server}/",
                                   username=os.environ['MONGO_USER'],
                                   password=os.environ['MONGO_PASS'])
events_db = mongo_client[os.environ['EVENT_LOG_DB']]

def event_store(ch, method, properties, body):
    message = json.loads(body.decode())
    event_type = message.get("body", {}).get("event", "UNKNOWN_EVENT")
    logger.info(f"[x] Event is received by EVENT LOGGING: {event_type}")
    col = events_db['events']
    col.insert_one(message)
    ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == '__main__':
    connection = None
    for i in range(10):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=os.environ['AMQP_HOST'],
                    credentials=pika.credentials.PlainCredentials(
                        url_unquote(os.environ['AMQP_USER']),
                        url_unquote(os.environ['AMQP_PASS'])
                    ),
                )
            )
            logger.info("Connected to RabbitMQ")
            break
        except pika.exceptions.AMQPConnectionError:
            logger.info(f"Failed to connect to RabbitMQ, attempt {i + 1}/10")
            time.sleep(3)
    else:
        raise Exception("Failed to connect to RabbitMQ after 10 attempts")

    channel = connection.channel()

    channel.basic_consume(queue=os.environ['EVENT_QUEUE'], on_message_callback=event_store)
    logger.info('[*] EventLogging service started. To exit press CTRL+C')
    channel.start_consuming()