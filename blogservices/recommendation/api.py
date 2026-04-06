import os
from dotenv import load_dotenv
import logging
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager

from moderation import moderate_blog_post
from db import get_recommendations
import aiormq
import asyncio
from auth import get_current_user
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.DEBUG)

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()

    rabbit = f"amqp://{os.environ['AMQP_USER']}:{os.environ['AMQP_PASS']}@{os.environ['AMQP_HOST']}/"

    for i in range(10):
        try:
            connection = await aiormq.connect(rabbit)
            logger.info("Connected to RabbitMQ")
            break
        except (ConnectionRefusedError, aiormq.exceptions.AMQPConnectionError) as e:
            logger.info(f"Failed to connect to RabbitMQ, attempt {i+1}/10")
            await asyncio.sleep(3)
    else:
        raise Exception("Failed to connect to RabbitMQ")

    channel = await connection.channel()
    await channel.basic_qos(prefetch_count=1)
    await channel.basic_consume(os.environ['RECOMMENDATION_QUEUE'], moderate_blog_post)

    yield

    await channel.close()
    await connection.close()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
async def api_get_recommendations(user_id: int = Depends(get_current_user)):
    recommendations = get_recommendations(user_id)
    return recommendations

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)