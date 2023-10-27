import logging
import json
import yaml
import requests
import env_config as config
import re
from redishelper import RedisHelper
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Load the RedisHelper class
redis_helper = RedisHelper()

COMMANDS = {
    "start": "Show available order types and order submission templates",
    "help": "Show this help message",
    "login": "Login to the exchange",
    "submit": "Submit an order"
}

# Load order formats from the YAML file
with open('order_formats.yaml', 'r') as f:
    order_formats = yaml.safe_load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [        
        [
            InlineKeyboardButton("LIMIT", callback_data='LIMIT'),
            InlineKeyboardButton("MARKET", callback_data='MARKET'),
        ],
        [
            InlineKeyboardButton("STOP_LIMIT", callback_data='STOP_LIMIT'),
            InlineKeyboardButton("STOP_MARKET", callback_data='STOP_MARKET'),
        ],
        [
            InlineKeyboardButton("CANCEL_ORDER", callback_data='CANCEL_ORDER')         
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please choose an order type:", reply_markup=reply_markup)

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Assuming you pass the credentials like: /login <exchange> <username> <password>
    args = update.message.text.split()[1:]
    if len(args) != 2:
        await context.bot.send_message(chat_id=chat_id, text="Usage: /login <exchange> <username> <password>")
        return
    try:
        username, password = args
        response = requests.post("http://localhost:8000/auth/token/", data={"username": username, "password": password})

        if response.status_code == 200:
            token = response.json().get("access_token")
            await redis_helper.set_token(token)
            await context.bot.send_message(chat_id=chat_id, text="Logged in successfully!")
        else:
            await context.bot.send_message(chat_id=chat_id, text="Login failed. Please check your credentials.")
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"Login failed. {e}")

async def submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_json = update.message.text
    command_args = re.sub(r'^/submit\s*', '', user_json, flags=re.MULTILINE)
    chat_id = update.effective_chat.id

    try:
        parsed_json = json.loads(command_args)
    except json.JSONDecodeError:
        await context.bot.send_message(chat_id=chat_id, text="Invalid JSON format.")
        return

    token = await redis_helper.get_token()
    if not token:        
        await context.bot.send_message(chat_id=chat_id, text="Please log in first.")
        return
    
    # Decide the endpoint
    endpoint = "http://localhost:8000/order/place_order/"
    if parsed_json.get("type") in ["STOP_LOSS", "TAKE_PROFIT"]:
        endpoint = "http://localhost:8000/position/tpsl_order/"
    
    # Send the request to the FastAPI app
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(endpoint, json=parsed_json, headers=headers)

    await context.bot.send_message(chat_id=chat_id, text=f"Response from server: {response.text}")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = "Available commands:\n"
    for command, description in COMMANDS.items():
        help_text += f"/{command} - {description}\n"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    order_type = query.data

    # Generate the JSON template based on the selected order type
    template = order_formats.get(order_type, {})

    await query.answer()
    await query.edit_message_text( text=f"Selected order type: {order_type}\n\nJSON template:\n<pre>{json.dumps(template, indent=2)}</pre>", parse_mode='HTML')

if __name__ == '__main__':
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    help_handler = CommandHandler('help', help)
    start_handler = CommandHandler('start', start)
    login_handler = CommandHandler('login', login)
    submit_handler = CommandHandler('submit', submit)
    button_handler = CallbackQueryHandler(button)
    
    application.add_handler(help_handler)
    application.add_handler(start_handler)
    application.add_handler(login_handler)
    application.add_handler(submit_handler)
    application.add_handler(button_handler)
    

    application.run_polling()
