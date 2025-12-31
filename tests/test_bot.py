import asyncio
from telegram import Update, User, Message, Chat
from telegram.ext import Application, ContextTypes
import os
from BINSearchCCGbot import walletbalance_handler, premium_handler

async def test_bot():
    app = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()
    user = User(id=7444150670, first_name="Test", is_bot=False)
    chat = Chat(id=7444150670, type="private")
    message = Message(message_id=1, date=None, chat=chat, from_user=user)
    context = ContextTypes.DEFAULT_TYPE().context

    test_cases = [
        {"cmd": "walletbalance", "args": ["eth", "0x742d35cc6634c0532925a3b844bc454e4438f44e"], "desc": "Valid ETH"},
        {"cmd": "walletbalance", "args": ["btc", "1MDUoxL1bGvMxhuoDYx6i11ePytECAk9QK"], "desc": "Valid BTC"},
        {"cmd": "walletbalance", "args": ["xyz", "invalid"], "desc": "Invalid chain"},
        {"cmd": "walletbalance", "args": [], "desc": "Missing args"},
        {"cmd": "premium", "args": [], "desc": "Premium prompt"}
    ]

    for case in test_cases:
        print(f"Testing: {case['desc']}")
        update = Update(update_id=1, message=message)
        context.args = case['args']
        if case['cmd'] == "walletbalance":
            await walletbalance_handler(update, context)
        elif case['cmd'] == "premium":
            await premium_handler(update, context)
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(test_bot())
