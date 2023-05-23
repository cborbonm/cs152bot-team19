# bot.py
import discord
from discord.ext import commands
import os
import json
import logging
import re
import requests
from report import Report
from mod_report import ModReport
import pdb

# Set up logging to the console
logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)

# There should be a file called 'tokens.json' inside the same folder as this file
token_path = "tokens.json"
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
    tokens = json.load(f)
    discord_token = tokens["discord"]

# There should be a file called 'mods.json' inside the same folder as this file
mods_path = "mods.json"
if not os.path.isfile(mods_path):
    print(f"{mods_path} not found!")
else:
    with open(mods_path) as f:
        # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
        mods = json.load(f)


class ModBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=".", intents=intents)
        self.group_num = None
        self.mod_channels = {}  # Map from guild to the mod channel id for that guild
        self.reports = {}  # Map from user IDs to the state of their report

    async def on_ready(self):
        print(f"{self.user.name} has connected to Discord! It is these guilds:")
        for guild in self.guilds:
            print(f" - {guild.name}")
        print("Press Ctrl-C to quit.")

        # Parse the group number out of the bot's name
        match = re.search("[gG]roup (\d+) [bB]ot", self.user.name)
        if match:
            self.group_num = match.group(1)
        else:
            raise Exception(
                'Group number not found in bot\'s name. Name format should be "Group # Bot".'
            )

        # Find the mod channel in each guild that this bot should report to
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == f"group-{self.group_num}-mod":
                    self.mod_channels[guild.id] = channel

    async def on_message(self, message):
        """
        This function is called whenever a message is sent in a channel that the bot can see (including DMs).
        Currently the bot is configured to only handle messages that are sent over DMs or in your group's "group-#" channel.
        """
        # Ignore messages from the bot
        if message.author.id == self.user.id:
            return

        # Check if this message was sent in a server ("guild") or if it's a DM
        if message.guild:
            await self.handle_channel_message(message)
        else:
            await self.handle_dm(message)

    async def handle_dm(self, message):
        responses = []
        author_id = message.author.id

        if author_id not in self.reports:
            # Handle a help message
            if message.content == Report.HELP_KEYWORD:
                reply = "Use the `report` command to begin the reporting process.\n"
                reply += "Use the `cancel` command to cancel the report process.\n"
                if author_id in mods.values():
                    reply += "Use the `modreport` command to begin the moderator reporting process.\n"
                reply += "If you are a mod and haven't registered yourself, please add your ID to the repo.\n"
                reply += f"Your user ID is: {message.author.id} \n"
                await message.channel.send(reply)
                return

            # Only respond to messages if they're part of a reporting flow
            if not (
                message.content.startswith(Report.START_KEYWORD)
                or message.content.startswith(ModReport.START_KEYWORD)
            ):
                return

            # We don't currently have an active report for this user, add one
            if message.content.startswith(Report.START_KEYWORD):
                self.reports[author_id] = Report(self, author_id)
            elif message.content.startswith(ModReport.START_KEYWORD):
                self.reports[author_id] = ModReport(self, author_id)
            else:
                await message.channel.send(
                    "Sorry, something went wrong starting your report. Please try again."
                )
                return

        # Let the report class handle this message; forward all the messages it returns to uss
        responses = await self.reports[author_id].handle_message(message)
        for r in responses:
            await message.channel.send(r)

        # If the report is complete or cancelled, remove it from our map
        if self.reports[author_id].report_complete():
            report = self.reports.pop(author_id)
            report_message = "---- New report! ----\n" + str(report)
            await self.mod_channels[report.message.guild.id].send(report_message)

    async def handle_channel_message(self, message):
        # Only handle messages sent in the "group-#" channel
        if not message.channel.name == f"group-{self.group_num}":
            return

        # Forward the message to the mod channel
        mod_channel = self.mod_channels[message.guild.id]
        await mod_channel.send(
            f'Forwarded message:\n{message.author.display_name}: "{message.content}"'
        )
        scores = self.eval_text(message.content)
        await mod_channel.send(self.code_format(scores))

    def eval_text(self, message):
        """'
        TODO: Once you know how you want to evaluate messages in your channel,
        insert your code here! This will primarily be used in Milestone 3.
        """
        return message

    def code_format(self, text):
        """'
        TODO: Once you know how you want to show that a message has been
        evaluated, insert your code here for formatting the string to be
        shown in the mod channel.
        """
        return "Evaluated: '" + text + "'"


client = ModBot()
client.run(discord_token)
