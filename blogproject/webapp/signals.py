from django.db.models.signals import post_save
from django.dispatch import receiver
from webapp.models import BlogPost
import logging
from .events import PostProducer

logger = logging.getLogger("django")

@receiver([post_save], sender=BlogPost, dispatch_uid="BlogPostSignal")
def on_post_created(sender, instance, **kwargs):
    created = kwargs.get("created")

    if created:
        logger.info(f"Post {instance.id} created. Sending event to RabbitMQ")
        try:
            post_producer = PostProducer()
            post_uri = '/api/posts/' + str(instance.id)
            post_producer.send_event(instance.author, instance.id, post_uri)
            post_producer.close()
        except Exception as e:
            logger.error("Failed to produce event on post creation. Error: %s" % e)