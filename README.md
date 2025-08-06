# Discord Pokémon Quiz Bot

A Discord bot that lets users play a game to name all 151 original Pokémon within a 15-minute time limit. 

My friends and I on Discord were watching one of us play the single player version of this game online (https://www.sporcle.com/games/g/pokemon). Being we wanted to play it together, I made this game in 30 minutes for my friends at 2AM because I'm unfortunately unemployed and have all the time in the world. Being it was late, I figured I didn't have the time to develop a frontend or deploy it. Being the nature of the game was text based, I decided to simply utilize Discord's API to play the game in chat by creating a bot for it.

This was made using a highly detailed and meticulusly structured prompt then debugged by vibe coding.

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