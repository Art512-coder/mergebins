from flask import Flask, request
import redis
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT', 18055))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Redis connection
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_timeout=5
    )
    redis_client.ping()
except redis.RedisError as e:
    logger.error(f"Redis connection failed: {e}")
    redis_client = None

app = Flask(__name__)

@app.route('/ipn', methods=['POST'])
def ipn_callback():
    try:
        data = request.json
        if data.get('payment_status') == 'finished':
            order_id = data.get('order_id')
            user_id = order_id.split('_')[1]
            if order_id.startswith('premium_'):
                if redis_client:
                    redis_client.setex(f"premium:{user_id}", 2592000, "active")
                logger.info(f"Premium activated for user {user_id}")
            elif order_id.startswith('check_'):
                if redis_client:
                    redis_client.setex(f"check:{user_id}:{order_id}", 3600, "paid")
                logger.info(f"Per-check payment confirmed for user {user_id}")
        return '', 200
    except Exception as e:
        logger.error(f"IPN error: {e}")
        return '', 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
