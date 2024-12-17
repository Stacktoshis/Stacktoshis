import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler

# Logging Setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Game Data (In-Memory Storage)
game_data = {
    "players": {},  # Stores player data: {player_id: {"username": str, "money": int, "position": int, "in_jail": bool}}
    "turn_order": [],  # List of player IDs in turn order
    "current_turn": 0,  # Index of the current player's turn
    "properties": {},  # Stores property data: {position: {"name": str, "price": int, "rent": int, "owner": str}}
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
            # Add more properties as needed...
        },
        "game_started": False,
    }
    await update.message.reply_text("Welcome to Monopoly! Use /join to join the game (max 4 players).")

async def join(update: Update, context: CallbackContext):
    """Join the game."""
    global game_data
    player_id = update.message.from_user.id
    username = update.message.from_user.username

    if game_data["game_started"]:
        await update.message.reply_text("The game has already started. Wait for the next game.")
        return

    if player_id in game_data["players"]:
        await update.message.reply_text("You have already joined the game.")
        return

    if len(game_data["players"]) >= MAX_PLAYERS:
        await update.message.reply_text("The game already has 4 players. Please wait for the next game.")
        return

    # Add the player to the game
    game_data["players"][player_id] = {"username": username, "money": STARTING_MONEY, "position": 0, "in_jail": False}
    await update.message.reply_text(f"{username} has joined the game!")

    if len(game_data["players"]) == MAX_PLAYERS:
        await start_game(update)

async def start_game(update: Update):
    """Start the game and decide turn order."""
    global game_data
    game_data["game_started"] = True

    # Roll dice to decide turn order
    rolls = {player_id: random.randint(1, DICE_SIDES) for player_id in game_data["players"]}
    game_data["turn_order"] = sorted(rolls.keys(), key=lambda pid: rolls[pid], reverse=True)

    turn_order_usernames = [game_data["players"][pid]["username"] for pid in game_data["turn_order"]]
    await update.message.reply_text(f"The turn order is: {', '.join(turn_order_usernames)}. Let’s start the game!")

    await take_turn(update)

async def roll(update: Update, context: CallbackContext):
    """Roll dice and move."""
    global game_data
    if not game_data["game_started"]:
        await update.message.reply_text("The game hasn't started yet. Use /join to join the game.")
        return

    player_id = game_data["turn_order"][game_data["current_turn"]]
    player = game_data["players"][player_id]

    dice_1 = random.randint(1, DICE_SIDES)
    dice_2 = random.randint(1, DICE_SIDES)
    total_roll = dice_1 + dice_2

    # Move the player
    player["position"] = (player["position"] + total_roll) % BOARD_SIZE

    await update.message.reply_text(
        f"{player['username']} rolled {dice_1} and {dice_2} (total: {total_roll}). "
        f"You landed on space {player['position']}."
    )

    # Handle landing actions
    await handle_space(update, player, player["position"])

    # Move to the next turn
    game_data["current_turn"] = (game_data["current_turn"] + 1) % len(game_data["turn_order"])
    await take_turn(update)

async def handle_space(update: Update, player, position):
    """Handle the action for the space the player landed on."""
    global game_data
    property = game_data["properties"].get(position)

    if property and property["owner"] == "Banker":
        await prompt_buy_property(update, player, property)
    elif property and property["owner"] != player["username"]:
        await pay_rent(update, player, property)

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
        f"The property '{property['name']}' is available for ${property['price']}. Do you want to buy it?",
        reply_markup=reply_markup,
    )

async def handle_buy(update: Update, context: CallbackContext):
    """Handle buying a property."""
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
                    await query.edit_message_text(f"You bought '{property_name}' for ${property['price']}!")
                else:
                    await query.edit_message_text("You don't have enough money to buy this property.")
                break

async def take_turn(update: Update):
    """Notify the next player of their turn."""
    global game_data
    player_id = game_data["turn_order"][game_data["current_turn"]]
    player = game_data["players"][player_id]
    await update.message.reply_text(f"It's {player['username']}'s turn. Use /roll to roll the dice.")

# Main Function
def main():
    application = Application.builder().token("BOT_TOKEN").build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("join", join))
    application.add_handler(CommandHandler("roll", roll))
    application.add_handler(CallbackQueryHandler(handle_buy, pattern="^buy_.*"))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()

                

  
