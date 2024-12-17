import os
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
)

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Game Data (In-Memory Storage)
game_data = {
    "players": {},  # Stores player data
    "turn_order": [],  # List of player IDs in turn order
    "current_turn": 0,  # Index of the current player's turn
    "properties": {},  # Stores property data
    "game_started": False,  # Flag to track if the game has started
}

STARTING_MONEY = 1500
MAX_PLAYERS = 4
BOARD_SIZE = 40
DICE_SIDES = 6


# Command Handlers
async def start(update: Update, context: CallbackContext):
    """Start a new game."""
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
    await update.message.reply_text(
        "🎲 Welcome to *Stacktoshis*! 🎲\nUse /join to join the game (max 4 players).",
        parse_mode="Markdown",
    )


async def join(update: Update, context: CallbackContext):
    """Allow players to join the game."""
    global game_data
    player_id = update.message.from_user.id
    username = update.message.from_user.username or f"Player_{player_id}"

    if game_data["game_started"]:
        await update.message.reply_text("🚫 The game has already started. Wait for the next round.")
        return

    if player_id in game_data["players"]:
        await update.message.reply_text("✅ You have already joined the game.")
        return

    if len(game_data["players"]) >= MAX_PLAYERS:
        await update.message.reply_text("🚫 The game is full. Please wait for the next game.")
        return

    # Add player to the game
    game_data["players"][player_id] = {
        "username": username,
        "money": STARTING_MONEY,
        "position": 0,
        "in_jail": False,
    }
    await update.message.reply_text(f"🎉 {username} has joined the game!")

    if len(game_data["players"]) == MAX_PLAYERS:
        await start_game(update)


async def start_game(update: Update):
    """Start the game and determine turn order."""
    global game_data
    game_data["game_started"] = True

    # Roll dice to decide the turn order
    rolls = {player_id: random.randint(1, DICE_SIDES) for player_id in game_data["players"]}
    game_data["turn_order"] = sorted(rolls.keys(), key=lambda pid: rolls[pid], reverse=True)

    turn_order_usernames = [game_data["players"][pid]["username"] for pid in game_data["turn_order"]]
    await update.message.reply_text(
        f"🎲 Turn order has been decided: {', '.join(turn_order_usernames)}.\nLet's start the game!"
    )

    await take_turn(update)


async def roll(update: Update, context: CallbackContext):
    """Roll dice and move the player."""
    global game_data
    if not game_data["game_started"]:
        await update.message.reply_text("🚫 The game hasn't started yet. Use /join to join.")
        return

    player_id = game_data["turn_order"][game_data["current_turn"]]
    player = game_data["players"][player_id]

    # Roll the dice
    dice_1 = random.randint(1, DICE_SIDES)
    dice_2 = random.randint(1, DICE_SIDES)
    total_roll = dice_1 + dice_2

    # Update player position
    player["position"] = (player["position"] + total_roll) % BOARD_SIZE
    await update.message.reply_text(
        f"🎲 {player['username']} rolled {dice_1} and {dice_2} (Total: {total_roll}).\n"
        f"You landed on space {player['position']}."
    )

    # Handle landing actions
    await handle_space(update, player, player["position"])

    # Move to the next turn
    game_data["current_turn"] = (game_data["current_turn"] + 1) % len(game_data["turn_order"])
    await take_turn(update)


async def handle_space(update: Update, player, position):
    """Handle actions based on the player's landing position."""
    global game_data
    property = game_data["properties"].get(position)

    if property and property["owner"] == "Banker":
        await prompt_buy_property(update, player, property)
    elif property and property["owner"] != player["username"]:
        await update.message.reply_text(f"🏠 This space is owned by {property['owner']}. Pay rent!")


async def prompt_buy_property(update: Update, player, property):
    """Prompt the player to buy a property."""
    keyboard = [
        [
            InlineKeyboardButton("Buy", callback_data=f"buy_{property['name']}"),
            InlineKeyboardButton("Skip", callback_data="skip"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"💰 '{property['name']}' is available for ${property['price']}. Do you want to buy it?",
        reply_markup=reply_markup,
    )


async def handle_buy(update: Update, context: CallbackContext):
    """Handle the buy property callback."""
    query = update.callback_query
    await query.answer()

    data = query.data
    global game_data

    if "buy" in data:
        player_id = game_data["turn_order"][game_data["current_turn"]]
        player = game_data["players"][player_id]
        property_name = data.split("_")[1]

        for position, property in game_data["properties"].items():
            if property["name"] == property_name and property["owner"] == "Banker":
                if player["money"] >= property["price"]:
                    player["money"] -= property["price"]
                    property["owner"] = player["username"]
                    await query.edit_message_text(f"🎉 You bought '{property_name}' for ${property['price']}!")
                else:
                    await query.edit_message_text("🚫 You don't have enough money to buy this property.")
                break


async def take_turn(update: Update):
    """Announce the next player's turn."""
    global game_data
    player_id = game_data["turn_order"][game_data["current_turn"]]
    player = game_data["players"][player_id]
    await update.message.reply_text(f"🔔 It's {player['username']}'s turn! Use /roll to roll the dice.")

# Main Function
def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("Error: BOT_TOKEN environment variable is not set!")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("join", join))
    application.add_handler(CommandHandler("roll", roll))
    application.add_handler(CallbackQueryHandler(handle_buy, pattern="^buy_.*"))

    # Run the bot
    logger.info("Starting Stacktoshis bot...")
    application.run_polling()

if __name__ == "__main__":
    main()


                

  
