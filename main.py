import logging
import random
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler

# Logging Setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Game Data (In-Memory Storage)
game_data = {
    "players": {},
    "turn_order": [],
    "current_turn": 0,
    "properties": {
        1: {"name": "Mediterranean Avenue", "price": 60, "rent": 2, "owner": "Banker"},
        3: {"name": "Baltic Avenue", "price": 60, "rent": 4, "owner": "Banker"},
    },
    "game_started": False,
}

STARTING_MONEY = 1500
MAX_PLAYERS = 4
BOARD_SIZE = 40
DICE_SIDES = 6

# Command Handlers
async def start(update: Update, context: CallbackContext):
    global game_data
    game_data = {
        "players": {},
        "turn_order": [],
        "current_turn": 0,
        "properties": {
            1: {"name": "Mediterranean Avenue", "price": 60, "rent": 2, "owner": "Banker"},
            3: {"name": "Baltic Avenue", "price": 60, "rent": 4, "owner": "Banker"},
        },
        "game_started": False,
    }
    await update.message.reply_text("Welcome to Stacktoshis! Use /join to join the game (max 4 players).")

# Other game logic functions...

# Main Function
def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("join", join))
    application.add_handler(CommandHandler("roll", roll))
    application.add_handler(CallbackQueryHandler(handle_buy, pattern="^buy_.*"))

    # Polling method (for simplicity during testing):
    application.run_polling()

if __name__ == "__main__":
    main()


                

  
