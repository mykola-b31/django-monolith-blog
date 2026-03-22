import os
import pika
from pika.compat import url_unquote
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=os.environ['AMQP_HOST'],
        credentials=pika.credentials.PlainCredentials(
            url_unquote(os.environ['AMQP_USER']),
            url_unquote(os.environ['AMQP_PASS'])
        )
    )
)
channel = connection.channel()

EXCHANGE = os.environ['EVENT_EXCHANGE']
DLQ_EXCHANGE = os.environ['DLQ_EVENT_EXCHANGE']
channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
channel.exchange_declare(exchange=DLQ_EXCHANGE, exchange_type="direct", durable=True)

channel.queue_declare(queue=os.environ['EVENT_QUEUE'], durable=True)
channel.queue_declare(queue=os.environ['DLQ_RECOMMENDATION'], durable=True)
channel.queue_declare(queue=os.environ['DLQ_NOTIFICATION'], durable=True)
channel.queue_declare(
    queue=os.environ['RECOMMENDATION_QUEUE'],
    durable=True,
    arguments={
        'x-dead-letter-exchange': DLQ_EXCHANGE,
        "x-dead-letter-routing-key": os.environ['DLQ_RECOMMENDATION'],
    }
)
channel.queue_declare(
    queue=os.environ['NOTIFICATION_QUEUE'],
    durable=True,
    arguments={
        'x-dead-letter-exchange': DLQ_EXCHANGE,
        "x-dead-letter-routing-key": os.environ['DLQ_NOTIFICATION']
    }
)

channel.queue_bind(
    queue=os.environ['EVENT_QUEUE'],
    exchange=EXCHANGE,
    routing_key=os.environ['ROUTING_KEY_EVENT']
)
channel.queue_bind(
    queue=os.environ['RECOMMENDATION_QUEUE'],
    exchange=EXCHANGE,
    routing_key=os.environ['ROUTING_KEY_RECOMMENDATION']
)
channel.queue_bind(
    queue=os.environ['NOTIFICATION_QUEUE'],
    exchange=EXCHANGE,
    routing_key=os.environ['ROUTING_KEY_NOTIFICATION']
)
channel.queue_bind(queue=os.environ['DLQ_RECOMMENDATION'], exchange=DLQ_EXCHANGE)
channel.queue_bind(queue=os.environ['DLQ_NOTIFICATION'], exchange=DLQ_EXCHANGE)