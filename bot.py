import discord
from discord.ext import commands
from discord import app_commands
import json
import asyncio
import datetime
import pytz
from Schedule import create_race_schedule, convert_to_est

# Create a subclass of `discord.Client` or `commands.Bot` to create your bot
intents = discord.Intents.default()
intents.message_content = True  # Enable message content for bot interaction
class Client(commands.Bot):
    async def on_ready(self):
        print(f'logged on as {self.user}')
        try:
            guild=discord.Object(id=GuildID) #Change to fit whatever your server id is for faster connections
            synced= await self.tree.sync(guild=guild)
            print(f'Synced {len(synced)} commands to guild {guild.id}')
        except Exception as e:
            print(f'Error syncing commands: {e}')
client = Client(command_prefix ="!",intents=intents)

# Time to check every minute (60 seconds) to send notifications
CHECK_INTERVAL = 60


fmt = '%d-%m-%Y %H:%M %Z%z'

# File path to your schedule data
FILE_PATH = 'Race schedule.xlsx'  # Replace with the actual path to your file
USER_TIMEZONE_FILE = 'user_timezones.json'  # File to store user timezones
# Channel ID of the target Discord channel
CHANNEL_ID_ANNOUNCEMENTS = 123456789012345678  # Replace with your actual Discord channel ID
CHANNEL_ID_SPAM=1
GUILD_ID=discord.Object(id=GuildID) #replace with server id 
def load_user_timezones():
    try:
        with open(USER_TIMEZONE_FILE, 'r') as f:
            # Try loading the JSON content
            data = json.load(f)
            # If the data is empty, return an empty dictionary
            if not data:
                return {}
            return data
    except FileNotFoundError:
        # If the file doesn't exist, return an empty dictionary
        return {}
    except json.JSONDecodeError:
        # If there's an issue decoding the JSON, log the error and return an empty dictionary
        print(f"Error decoding {USER_TIMEZONE_FILE}. Returning empty dictionary.")
        return {}
    
def save_user_timezones(timezones):
    with open(USER_TIMEZONE_FILE, 'w') as f:
        json.dump(timezones, f)




# Helper function to get the time difference from current time to event
def time_to_event(event_time):
    # Get the current time in EST
    now = datetime.datetime.now(pytz.timezone('US/Eastern'))

    # Calculate the time difference between the event and current time
    time_diff = event_time - now
    return time_diff

# Function to send race event notifications
async def send_race_notifications(channel):
    race_schedule = create_race_schedule(FILE_PATH)

    # Iterate over each GP in the schedule
    for gp in race_schedule:
        for event in gp.event:
            # Convert to datetime object in EST
            event_time_est = convert_to_est(event.datetime)  # This is now a datetime object

            # Get the time difference
            time_diff = time_to_event(event_time_est)

            # Time before the event to send a notification
            if time_diff.total_seconds() <= 900 and time_diff.total_seconds() > 0:  # 15 minutes before
                if event.event_type.lower() in ['race', 'sprint']:
                    await channel.send(f"@Race alerts **Reminder**: The {event.event_type} for {gp.name} at {gp.circuit} is starting in 15 minutes!")
                else:
                    await channel.send(f"@All alerts  **Reminder**: The {event.event_type} for {gp.name} at {gp.circuit} is starting in 15 minutes!")
            
            # If pre-show is true, send separate pre-show notification
            if event.pre_show:
                pre_show_time = time_to_event(event_time_est)
                if pre_show_time.total_seconds() <= 1800 and pre_show_time.total_seconds() > 0:  # 30 minutes before qualifying or 1 hour for race
                    if event.event_type.lower() in ['qualifying', 'race', 'sprint']:
                        pre_show_message = f"@All alerts  **Pre-show reminder**: The {event.event_type} for {gp.name} at {gp.circuit} will begin in 30 minutes!" if event.event_type.lower() == 'qualifying' else \
                                           f"@Race alerts **Pre-show reminder**: The {event.event_type} for {gp.name} at {gp.circuit} will begin in 1 hour!"
                        await channel.send(pre_show_message)

            # Send message when the event is about to start
            if time_diff.total_seconds() <= 0 and time_diff.total_seconds() > -60:  # Event time is now
                if event.event_type.lower() in ['race', 'sprint']:
                    await channel.send(f"@Race alerts **Now starting**: The {event.event_type} for {gp.name} at {gp.circuit} has just begun!")
                else:
                    await channel.send(f"@All alerts  **Now starting**: The {event.event_type} for {gp.name} at {gp.circuit} has just begun!")

# Discord bot event loop that runs every minute
async def scheduled_event_loop():
    await client.wait_until_ready()  # Wait until the bot is logged in
    channel = client.get_channel(CHANNEL_ID_ANNOUNCEMENTS)  # Get the target channel

    while not client.is_closed():
        await send_race_notifications(channel)  # Check and send race notifications
        await asyncio.sleep(CHECK_INTERVAL)  # Wait for 1 minute before checking again

def get_next_race():
    race_schedule = create_race_schedule(FILE_PATH)
    now = datetime.datetime.now(pytz.timezone('US/Eastern'))

    # Find the next event in the future
    next_race = None
    for gp in race_schedule:
        for event in gp.event:
            event_time_est = convert_to_est(event.datetime)  # Get the event time in EST

            if event_time_est > now:
                if not next_race or event_time_est < convert_to_est(next_race.datetime):
                    next_race = event
                    next_gp = gp
    return next_gp, next_race

@client.tree.command(name='settz',description="",guild=GUILD_ID)
async def set_timezone(interaction:discord.Interaction, timezone: str):

    try:
        pytz.timezone(timezone)  # Check if the timezone is valid
    except pytz.UnknownTimeZoneError:
        await interaction.response.send_message(f"Invalid timezone: {timezone}. Please use a valid timezone, like 'US/Eastern'.")
        return

    # Load current timezones and update for the user
    user_timezones = load_user_timezones()
    user_timezones[str(interaction.user._user.id)] = timezone
    save_user_timezones(user_timezones)

    await interaction.response.send_message(f"Timezone for {interaction.user._user.name} set to {timezone}.")




# Command to get the next race
@client.tree.command(name='nextrace',description="",guild=GUILD_ID)
async def next_race(interaction: discord.Interaction):
    next_gp, next_race = get_next_race()

    if not next_race:
        await interaction.response.send_message("No upcoming races found.")
        return

    # User's timezone (for this example, we assume it's Eastern Time)
    user_timezones=load_user_timezones()
    user_timezone=pytz.timezone(user_timezones.get(str(interaction.user._user.id),'US/Eastern'))

    next_race.datetime=datetime.datetime.fromisoformat(next_race.datetime).replace(tzinfo=pytz.UTC)
    race_time_in_user_timezone = next_race.datetime.astimezone(user_timezone)

    # Embed the message
    embed = discord.Embed(
        title=f"Next Race: {next_gp.name}",
        description=f"**Country**: {next_gp.country}\n**Circuit**: {next_gp.circuit}\n**Time**: {race_time_in_user_timezone.strftime(fmt)}",
        color=discord.Color.blue()
    )
    
    # Use the country flag emoji as thumbnail
    embed.set_thumbnail(url=next_gp.flag)  # You can replace the URL with a proper one

    # Send the embed to the channel
    await interaction.response.send_message(embed=embed)

# Event when the bot is ready
@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    try:    
        guild=discord.Object(id=GuildID)
        synced= await client.tree.sync(guild=guild)
        print(f'Synced {len(synced)} commands to guild {guild.id}')
    except Exception as e:
        print(f'Error syncing commands: {e}')
# Start the scheduled event loop
    client.loop.create_task(scheduled_event_loop())


TOKEN = 'your_token_here'  # Replace with your bot's token
client.run(TOKEN)
