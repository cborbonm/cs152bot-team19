# bot.py
import discord
from discord.ext import commands
import os
import json
import logging
import re
import requests
from report import Report
from reports.report_utils import store_report, load_report
from reports.review_utils import store_review, load_review
from gpt import GPTClassification, ask_gpt
from mod_review import ModReview
from typing import Dict
import pdb

_HISTORY_TTLS = {
    GPTClassification.MAYBE_SEXTORTION: 5,
    GPTClassification.YES_SEXTORTION: 20
}

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

# There should be a file called 'report_number.json' inside the same folder as this file
report_number_path = "report_number.json"
if not os.path.isfile(report_number_path):
    print(f"{report_number_path} not found!")
    report_num = 1
    review_num = 1
else:
    with open(report_number_path) as f:
        # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
        obj: Dict = json.load(f)
        report_num = obj.get("report_num", 1)
        review_num = obj.get("review_num", 1)

class ModBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=".", intents=intents)
        self.group_num = None
        self.mod_channels = {}  # Map from guild to the mod channel id for that guild
        self.processes = {}  # Map from user IDs to the state of their report / review
        self.flagged_users = {}
        self.next_report_num = report_num
        self.next_review_num = review_num

    async def cleanup(self):
        print("\nCleaning up!")
        with open(report_number_path, "w") as f:
            # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
            json.dump({"report_num": self.next_report_num, "review_num": self.next_review_num}, f)
        return
    
    async def close(self):
        await self.cleanup()
        await super().close()

    async def on_ready(self):
        print(f"{self.user.name} has connected to Discord! It has these guilds:")
        for guild in self.guilds:
            print(f" - {guild.name}")
        print(f"The next report number is {self.next_report_num}.")
        print(f"The next review number is {self.next_review_num}.")
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

        if author_id not in self.processes:
            # Handle a help message
            if message.content == Report.HELP_KEYWORD:
                reply = f"Use the `{Report.START_KEYWORD}` command to begin the reporting process.\n"
                reply += "Use the `cancel` command to cancel the report process.\n"
                if author_id in mods.values():
                    reply += f"Use the `{ModReview.START_KEYWORD}` command to begin the moderator review process.\n"
                reply += "If you are a mod and haven't registered yourself, please add your ID to `mods.json` the repo.\n"
                reply += f"Your user ID is: {message.author.id} \n"
                await message.channel.send(reply)
                return

            # Only respond to messages if they're part of a reporting flow
            if not (
                message.content.startswith(Report.START_KEYWORD)
                or message.content.startswith(ModReview.START_KEYWORD)
            ):
                return

            # We don't currently have an active report for this user, add one
            if message.content.startswith(Report.START_KEYWORD):
                self.processes[author_id] = Report(self.next_report_num, self, author_id)
                self.next_report_num += 1
            elif message.content.startswith(ModReview.START_KEYWORD):
                self.processes[author_id] = ModReview(self.next_review_num, self, author_id, self.mod_channels)
                self.next_review_num += 1
            else:
                await message.channel.send(
                    "Sorry, something went wrong starting your report. Please try again."
                )
                return

        # Let the report class handle this message; forward all the messages it returns to uss
        responses = await self.processes[author_id].handle_message(message)
        for r in responses:
            await message.channel.send(r)

        # If the report is complete or cancelled, remove it from our map
        if self.processes[author_id].report_complete():
            process = self.processes.pop(author_id)
            if not process.is_review:
                report_message = f"---- New report! Number: {str(process.report_num)} ----\n"
                await self.mod_channels[process.guild_id].send(report_message)
                await store_report(process)
                print(f"Stored report {process.report_num}")
            else:
                review_message = f"---- New moderator review complete! Number: {str(process.review_num)} ----\n"
                await self.mod_channels[process.guild_id].send(review_message)
                await process.send_followup()
                await store_review(process)
                print(f"Stored mod review {process.review_num}")

    async def handle_channel_message(self, message):
        # Only handle messages sent in the "group-#" channel
        if not message.channel.name == f"group-{self.group_num}":
            return
        
        # Forward the message to the mod channel
        flag, eval_message = self.eval_text(message)
        if flag:
            mod_channel = self.mod_channels[message.guild.id]
            await mod_channel.send(
                f'Forwarded message:\n{message.author.display_name}: "{message.content}"'
            )
            await mod_channel.send(eval_message)

    def eval_text(self, message):
        """'
        TODO: Once you know how you want to evaluate messages in your channel,
        insert your code here! This will primarily be used in Milestone 3.
        """
        # Get user history
        flag = False
        history = GPTClassification.NO_HISTORY
        ttl = 0
        author_id = message.author.id
        if author_id in self.flagged_users:
            hist, ttl = self.flagged_users[author_id]
            ttl -= 1
            if ttl > 0:
                history = hist
                self.flagged_users[author_id] = hist, ttl
            else:
                del self.flagged_users[author_id]
            
        # Ask GPT if it thinks the message is sextortion
        gpt_answer = ask_gpt(message.content, history)

        # If sextortion, flag the message
        if gpt_answer != GPTClassification.NOT_SEXTORTION:
            flag = True
            gpt_answer_hist = GPTClassification.convert_to_hist(gpt_answer)
            if GPTClassification.hist_leq(history, gpt_answer_hist):
                self.flagged_users[author_id] = gpt_answer_hist, _HISTORY_TTLS[gpt_answer]
            logging.warning(f"Flag: '{gpt_answer}' Message: '{message.content}'")
        return flag, self.code_format(gpt_answer, history, ttl)

    def code_format(self,  gpt_flag: str, history:str = GPTClassification.NO_HISTORY, ttl:int = 0):
        """'
        TODO: Once you know how you want to show that a message has been
        evaluated, insert your code here for formatting the string to be
        shown in the mod channel.
        """
        return f"History: '{history}' TTL: {ttl}\nGPT Eval: {gpt_flag}"


client = ModBot()
client.run(discord_token)
