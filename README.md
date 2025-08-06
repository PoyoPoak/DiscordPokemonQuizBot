# Discord Pokémon Quiz Bot

A Discord bot that lets users play a game to name all 151 original Pokémon within a 15-minute time limit.

## Features

- Start a game with the command `!play`
- Users have 15 minutes to guess all 151 original Pokémon
- Real-time updating grid shows progress
- Messages with correct guesses are automatically deleted to keep chat clean
- Answer key displayed at the end of the game

## Setup

1. Clone this repository
2. Create a `.env` file with your Discord bot token:
   ```
   DISCORD_TOKEN=your_token_here
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the bot:
   ```
   python main.py
   ```

## Commands

- `!play` - Start a new Pokémon guessing game in the current channel
- `!hello` - Get a greeting from the bot
- `!assign` - Assign yourself to the "Gamer" role
- `!remove` - Remove yourself from the "Gamer" role
- `!dm [message]` - Have the bot DM you a message
- `!reply` - Get a reply to your message
- `!poll [question]` - Create a poll with a question

## How to Play

1. Type `!play` in a text channel to start the game
2. Type the names of the original 151 Pokémon in the chat
3. The bot will update the grid with correct guesses
4. Try to name all Pokémon within the 15-minute time limit