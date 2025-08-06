import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import asyncio
import time
import re
from pokemon_data import ORIGINAL_POKEMON

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Game state
active_games = {}

# Grid display configuration
GRID_SECTIONS = 4  # Number of messages to split the grid into

secret_role = "Gamer"

@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}")
    print(f"Bot is connected to {len(bot.guilds)} servers")
    print("Commands registered:", [command.name for command in bot.commands])

@bot.event
async def on_member_join(member):
    await member.send(f"Welcome to the server {member.name}")

@bot.event
async def on_message(message):
    # First check to avoid processing the bot's own messages
    if message.author == bot.user:
        return

    # Important: Process commands first to make sure they work correctly
    # This needs to happen before other message processing
    await bot.process_commands(message)
    
    try:
        # Check if message is part of an active game
        channel_id = message.channel.id
        if channel_id in active_games and active_games[channel_id]["is_running"]:
            # Skip command messages for game processing
            if message.content.startswith(bot.command_prefix):
                return
                
            game_data = active_games[channel_id]
            
            # Clean and check the message
            guess = clean_pokemon_name(message.content)
            if not guess:  # Skip empty guesses
                return
                
            print(f"Received guess: '{guess}' from {message.author.name}")
            
            # Check if this is a valid remaining pokemon
            match_found = False
            for pos, name in list(game_data["remaining_pokemon"].items()):
                if clean_pokemon_name(name) == guess:
                    # Found a match!
                    match_found = True
                    print(f"Match found! {guess} = {name}")
                    game_data["guessed"][pos] = name
                    del game_data["remaining_pokemon"][pos]
                    
                    # Update the display immediately
                    time_left = game_data["end_time"] - time.time()
                    time_str = format_time(time_left)
                    total_guessed = len(game_data["guessed"])
                    
                    # Update header with new count and time
                    header = generate_grid_header(total_guessed, time_str)
                    await game_data["header_message"].edit(content=f"```\n{header}\n```")
                    
                    # Determine which section of the grid needs to be updated
                    pokemon_per_section = (151 + GRID_SECTIONS - 1) // GRID_SECTIONS
                    section_index = (pos - 1) // pokemon_per_section
                    
                    # Only update the section that changed
                    if section_index < len(game_data["grid_messages"]):
                        grid_sections = generate_grid_sections(game_data["guessed"])
                        try:
                            await game_data["grid_messages"][section_index].edit(
                                content=f"```\n{grid_sections[section_index]}\n```"
                            )
                        except discord.HTTPException as e:
                            print(f"Error updating grid section {section_index+1}: {str(e)}")
                            simplified = f"Grid segment - Contains guessed Pokémon"
                            await game_data["grid_messages"][section_index].edit(
                                content=f"```\n{simplified}\n```"
                            )
                    
                    # Delete the message to keep chat clean
                    try:
                        await message.delete()
                    except Exception as e:
                        print(f"Could not delete message: {str(e)}")
                    
                    # Check if all Pokemon have been guessed
                    if len(game_data["guessed"]) == 151:
                        await message.channel.send("Congratulations! You've named all 151 original Pokémon!")
                        await end_game(message.channel)
                    
                    # We found a match, no need to check other Pokemon
                    break
            
            # If no match was found and it's not an empty guess
            if not match_found and guess:
                print(f"Incorrect guess: '{guess}' from {message.author.name}")
                try:
                    # React with an X emoji
                    await message.add_reaction('❌')
                    
                    # Wait 1 second before deleting
                    await asyncio.sleep(1)
                    
                    # Delete the incorrect message
                    await message.delete()
                except Exception as e:
                    print(f"Error handling incorrect guess: {str(e)}")
        
        if "shit" in message.content.lower():
            await message.delete()
            await message.channel.send(f"{message.author.mention} - dont use that word!")
    except Exception as e:
        print(f"Error in on_message: {type(e).__name__}: {str(e)}")

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")

@bot.command()
async def assign(ctx):
    role = discord.utils.get(ctx.guild.roles, name=secret_role)
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f"{ctx.author.mention} is now assigned to {secret_role}")
    else:
        await ctx.send("Role doesn't exist")

@bot.command()
async def remove(ctx):
    role = discord.utils.get(ctx.guild.roles, name=secret_role)
    if role:
        await ctx.author.remove_roles(role)
        await ctx.send(f"{ctx.author.mention} has had the {secret_role} removed")
    else:
        await ctx.send("Role doesn't exist")

@bot.command()
async def dm(ctx, *, msg):
    await ctx.author.send(f"You said {msg}")

@bot.command()
async def reply(ctx):
    await ctx.reply("This is a reply to your message!")
    
@bot.command()
async def test(ctx):
    """Test command to verify the bot is working properly"""
    try:
        print(f"Test command invoked by {ctx.author.name}")
        await ctx.send("Bot is working! This is a test message.")
        print("Test message sent successfully")
    except Exception as e:
        print(f"Error in test command: {type(e).__name__}: {str(e)}")

@bot.command()
async def poll(ctx, *, question):
    embed = discord.Embed(title="New Poll", description=question)
    poll_message = await ctx.send(embed=embed)
    await poll_message.add_reaction("👍")
    await poll_message.add_reaction("👎")

@bot.command()
@commands.has_role(secret_role)
async def secret(ctx):
    await ctx.send("Welcome to the club!")

# Helper function to clean text
def clean_pokemon_name(name):
    # Only log this for messages with less than 50 characters to avoid console spam
    if len(name) < 50:
        cleaned = re.sub(r'[^a-zA-Z]', '', name).lower()
        print(f"Cleaned name: '{name}' -> '{cleaned}'")
        return cleaned
    else:
        # For longer content (like the grid itself), don't log
        return re.sub(r'[^a-zA-Z]', '', name).lower()

# Generate the game grid header (count and time)
def generate_grid_header(total_guessed, time_remaining_str):
    return f"{total_guessed}/151  |  {time_remaining_str}\n{'='*50}"

# Generate the game grid, split into sections
def generate_grid_sections(guessed_pokemon, sections=GRID_SECTIONS):
    # Calculate how many Pokémon to include per section
    pokemon_per_section = (151 + sections - 1) // sections  # Ceiling division
    grid_sections = []
    
    # Generate each section of the grid
    for section in range(sections):
        grid_lines = []
        start_pos = section * pokemon_per_section + 1
        end_pos = min((section + 1) * pokemon_per_section, 151)
        
        # Create a grid with 5 columns for this section
        items_in_section = end_pos - start_pos + 1
        rows_in_section = (items_in_section + 4) // 5  # Ceiling division for 5 columns
        
        for row in range(rows_in_section):
            line_items = []
            for col in range(5):
                pos = start_pos + row + col * rows_in_section
                if pos <= end_pos:
                    if pos in guessed_pokemon:
                        # Shorter format for guessed Pokémon
                        pokemon_name = guessed_pokemon[pos]
                        # Truncate long names to keep the grid compact
                        if len(pokemon_name) > 9:
                            pokemon_name = pokemon_name[:9]
                        line_items.append(f"{pos:3d}.{pokemon_name}")
                    else:
                        line_items.append(f"{pos:3d}.")
            
            # Pad each item to make columns align
            padded_items = [item.ljust(14) for item in line_items]
            grid_line = "".join(padded_items)
            
            # Only add non-empty lines
            if grid_line.strip():
                grid_lines.append(grid_line)
        
        grid_sections.append("\n".join(grid_lines))
    
    return grid_sections

# Generate the game grid (legacy method for compatibility)
def generate_grid(guessed_pokemon, time_remaining_str, total_guessed):
    header = generate_grid_header(total_guessed, time_remaining_str)
    sections = generate_grid_sections(guessed_pokemon)
    
    # Combine all sections into one grid for backward compatibility
    result = header + "\n" + "\n".join(sections)
    
    # Ensure the result is within Discord's message limit
    if len(result) > 1900:  # Leave some buffer for the code block markers
        return "Grid too large for display. Please use the multi-message grid format."
    
    return result

# Generate the final grid header
def generate_final_grid_header(total_guessed):
    return f"{total_guessed}/151  |  Time's up!\n{'='*50}"

# Generate the final grid sections with missed Pokemon
def generate_final_grid_sections(guessed_pokemon, missed_pokemon, sections=GRID_SECTIONS):
    # Calculate how many Pokémon to include per section
    pokemon_per_section = (151 + sections - 1) // sections  # Ceiling division
    grid_sections = []
    
    # Generate each section of the grid
    for section in range(sections):
        grid_lines = []
        start_pos = section * pokemon_per_section + 1
        end_pos = min((section + 1) * pokemon_per_section, 151)
        
        # Create a grid with 5 columns for this section
        items_in_section = end_pos - start_pos + 1
        rows_in_section = (items_in_section + 4) // 5  # Ceiling division for 5 columns
        
        for row in range(rows_in_section):
            line_items = []
            for col in range(5):
                pos = start_pos + row + col * rows_in_section
                if pos <= end_pos:
                    if pos in guessed_pokemon:
                        # Truncate long names to keep the grid compact
                        pokemon_name = guessed_pokemon[pos]
                        if len(pokemon_name) > 9:
                            pokemon_name = pokemon_name[:9]
                        line_items.append(f"{pos:3d}.{pokemon_name}")
                    else:
                        # For missed Pokémon, mark with a star (*) and show the name
                        pokemon_name = missed_pokemon[pos]
                        if len(pokemon_name) > 9:
                            pokemon_name = pokemon_name[:9]
                        line_items.append(f"*{pos:2d}.{pokemon_name}")
            
            # Pad each item to make columns align
            padded_items = [item.ljust(14) for item in line_items]
            grid_line = "".join(padded_items)
            
            # Only add non-empty lines
            if grid_line.strip():
                grid_lines.append(grid_line)
        
        grid_sections.append("\n".join(grid_lines))
    
    return grid_sections

# Display the final grid with missed Pokemon (legacy method for compatibility)
def generate_final_grid(guessed_pokemon, missed_pokemon):
    header = generate_final_grid_header(len(guessed_pokemon))
    sections = generate_final_grid_sections(guessed_pokemon, missed_pokemon)
    
    # Combine all sections into one grid for backward compatibility
    result = header + "\n" + "\n".join(sections)
    
    # If the result is still too long, show a summary instead
    if len(result) > 1900:
        found_count = len(guessed_pokemon)
        missed_count = 151 - found_count
        summary = [
            f"{found_count}/151  |  Time's up!",
            f"="*50,
            f"You found {found_count} Pokémon and missed {missed_count}.",
            f"Note: Missed Pokémon are marked with a star (*)",
            f"Examples: {', '.join(['*' + str(list(missed_pokemon.keys())[i]) + '. ' + list(missed_pokemon.values())[i] for i in range(min(5, missed_count))])}"
        ]
        return "\n".join(summary)
    
    return result

# Format time remaining
def format_time(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

@bot.command()
async def play(ctx):
    try:
        print(f"Play command invoked by {ctx.author.name} in channel {ctx.channel.name}")
        channel = ctx.channel
        
        # Check if there's already a game running in this channel
        if channel.id in active_games:
            await ctx.send("A game is already in progress in this channel!")
            return
            
        # Initialize game state
        game_data = {
            "guessed": {},  # Position -> Pokemon name mapping
            "remaining_pokemon": {i+1: name for i, name in enumerate(ORIGINAL_POKEMON)},
            "header_message": None,  # For the count and timer
            "grid_messages": [],  # List to hold grid section messages
            "is_running": True,
            "start_time": time.time(),
            "end_time": time.time() + 15 * 60,  # 15 minutes
        }
        active_games[channel.id] = game_data
        
        print("Sending initial messages...")
        
        # First message: header with count and time
        header = generate_grid_header(0, "15:00")
        game_data["header_message"] = await ctx.send(f"```\n{header}\n```")
        print(f"Header message sent with ID: {game_data['header_message'].id}")
        
        # Send each grid section as a separate message
        grid_sections = generate_grid_sections({})  # Empty grid to start
        
        for i, section in enumerate(grid_sections):
            try:
                msg = await ctx.send(f"```\n{section}\n```")
                game_data["grid_messages"].append(msg)
                print(f"Grid section {i+1} sent with ID: {msg.id}")
            except discord.HTTPException as e:
                print(f"Error sending grid section {i+1}: {str(e)}")
                # If there's an error, try sending a simplified version
                simplified = f"Grid segment - No Pokémon guessed yet"
                msg = await ctx.send(f"```\n{simplified}\n```")
                game_data["grid_messages"].append(msg)
        
        # Start the game loop
        print("Starting game loop...")
        game_task = asyncio.create_task(game_loop(channel))
        
        # Store the task so it doesn't get garbage collected
        game_data["task"] = game_task
        
        await ctx.send("Pokémon Quiz Game has started! You have 15 minutes to name all 151 original Pokémon!")
        print("Play command completed successfully")
    except Exception as e:
        print(f"Error in play command: {type(e).__name__}: {str(e)}")
        await ctx.send(f"An error occurred while starting the game: {type(e).__name__}")
        if channel.id in active_games:
            del active_games[channel.id]

async def game_loop(channel):
    try:
        print(f"Game loop started for channel: {channel.name}")
        
        # Get game data
        if channel.id not in active_games:
            print(f"Error: No active game found for channel {channel.id}")
            return
            
        game_data = active_games[channel.id]
        
        while game_data["is_running"]:
            try:
                # Check if time is up
                current_time = time.time()
                if current_time >= game_data["end_time"]:
                    print("Time's up, ending game...")
                    await end_game(channel)
                    break
                    
                # Update timer
                time_left = game_data["end_time"] - current_time
                time_str = format_time(time_left)
                
                # Total guessed count
                total_guessed = len(game_data["guessed"])
                
                print(f"Updating grid... ({total_guessed}/151 guessed)")
                
                # Update the header message with current count and time
                header = generate_grid_header(total_guessed, time_str)
                await game_data["header_message"].edit(content=f"```\n{header}\n```")
                
                # Update each grid section message
                grid_sections = generate_grid_sections(game_data["guessed"])
                for i, section in enumerate(grid_sections):
                    if i < len(game_data["grid_messages"]):
                        try:
                            await game_data["grid_messages"][i].edit(content=f"```\n{section}\n```")
                        except discord.HTTPException as e:
                            print(f"Error updating grid section {i+1}: {str(e)}")
                            # If there's an error, try updating with a simplified version
                            simplified = f"Grid segment - Too large to display"
                            await game_data["grid_messages"][i].edit(content=f"```\n{simplified}\n```")
                
                # Wait before updating again
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Error in game loop iteration: {type(e).__name__}: {str(e)}")
                await channel.send(f"An error occurred during the game: {type(e).__name__}")
                break
        
        print("Game loop ended normally")
    except Exception as e:
        print(f"Fatal error in game loop: {type(e).__name__}: {str(e)}")
        try:
            await channel.send("A fatal error occurred. The game has been terminated.")
            if channel.id in active_games:
                del active_games[channel.id]
        except:
            print("Could not send error message to channel")
        return

async def end_game(channel):
    try:
        print(f"Ending game for channel: {channel.name}")
        
        if channel.id not in active_games:
            print(f"Error: No active game found for channel {channel.id}")
            return
            
        game_data = active_games[channel.id]
        game_data["is_running"] = False
        
        total_guessed = len(game_data["guessed"])
        
        # Update the header message with final count
        header = generate_final_grid_header(total_guessed)
        await game_data["header_message"].edit(content=f"```\n{header}\n```")
        
        # Update each grid section with answers for missed Pokémon
        final_grid_sections = generate_final_grid_sections(game_data["guessed"], game_data["remaining_pokemon"])
        
        for i, section in enumerate(final_grid_sections):
            if i < len(game_data["grid_messages"]):
                try:
                    await game_data["grid_messages"][i].edit(content=f"```\n{section}\n```")
                except discord.HTTPException as e:
                    print(f"Error updating final grid section {i+1}: {str(e)}")
                    # If there's an error, try updating with a simplified version
                    simplified = f"Grid segment - Too large to display"
                    await game_data["grid_messages"][i].edit(content=f"```\n{simplified}\n```")
        
        await channel.send(f"Time's up! You guessed {total_guessed}/151 Pokémon!")
        
        # Clean up game data
        print("Cleaning up game data...")
        del active_games[channel.id]
        print("Game ended successfully")
    except Exception as e:
        print(f"Error in end_game: {type(e).__name__}: {str(e)}")
        await channel.send("An error occurred while ending the game.")
        
        # Make sure to clean up even if there's an error
        if channel.id in active_games:
            del active_games[channel.id]

@secret.error
async def secret_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("You do not have permission to do that!")

# Custom error handler for all commands
@bot.event
async def on_command_error(ctx, error):
    print(f"Command error in {ctx.command}: {type(error).__name__}: {str(error)}")
    if isinstance(error, commands.CommandNotFound):
        return
    await ctx.send(f"Error: {type(error).__name__}")

# Log important startup info
print(f"Starting bot with token: {'*' * (len(token) - 4) + token[-4:] if token else 'None'}")
if not token:
    print("WARNING: No Discord token found! Make sure you have a .env file with DISCORD_TOKEN")

# Run the bot
try:
    bot.run(token, log_handler=handler, log_level=logging.DEBUG)
except Exception as e:
    print(f"Failed to start bot: {type(e).__name__}: {str(e)}")