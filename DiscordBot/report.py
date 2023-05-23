from enum import Enum, auto
import discord
import re

class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE = auto()
    MESSAGE_IDENTIFIED = auto()
    
    AWAITING_WHO_REPORT = auto()
    MYSELF = auto()
    SOMEONE_ELSE = auto()
    
    AWAITING_HAVE_DISCORD = auto()
    AWAITING_WHAT_USERNAME = auto()
    
    AWAITING_WHAT_REASON = auto()

    REPORT_COMPLETE = auto()
    REPORT_CANCELLED = auto()

class Report:
    START_KEYWORD = "report"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"

    MYSELF_KEYWORD = "myself"
    SOMEONE_ELSE_KEYWORD = "someone else"

    YES_KEYWORD = "yes"
    NO_KEYWORD = "no"

    HARASSMENT_KEYWORD = "h"
    DANGEROUS_INFO_KEYWORD = "d"
    MISLEADING_INFO_KEYWORD = "m"
    EXPLICIT_KEYWORD = "e"
    OTHER_KEYWORD = "o"

    def __init__(self, client):
        self.state = State.REPORT_START
        self.client = client
        self.message = None
        self.help_message = ""
        self.who = None
        self.account = None
        self.reason = None
    
    async def handle_message(self, message):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''

        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REPORT_CANCELLED
            return ["Report cancelled."]
        
        if self.state == State.REPORT_START:
            reply =  "Thank you for starting the reporting process. "
            reply += f"Say `{self.HELP_KEYWORD}` at any time for more information.\n\n"
            reply += "Please copy paste the link to the message you want to report.\n"
            reply += "You can obtain this link by right-clicking the message and clicking `Copy Message Link`."
            self.state = State.AWAITING_MESSAGE
            return [reply]
        
        if self.state == State.AWAITING_MESSAGE:
            # Parse out the three ID strings from the message link
            m = re.search('/(\d+)/(\d+)/(\d+)', message.content)
            if not m:
                return ["I'm sorry, I couldn't read that link. Please try again or say `cancel` to cancel."]
            guild = self.client.get_guild(int(m.group(1)))
            if not guild:
                return ["I cannot accept reports of messages from guilds that I'm not in. Please have the guild owner add me to the guild and try again."]
            channel = guild.get_channel(int(m.group(2)))
            if not channel:
                return ["It seems this channel was deleted or never existed. Please try again or say `cancel` to cancel."]
            try:
                self.message = await channel.fetch_message(int(m.group(3)))
            except discord.errors.NotFound:
                return ["It seems this message was deleted or never existed. Please try again or say `cancel` to cancel."]

            # Here we've found the message - it's up to you to decide what to do next!
            self.state = State.MESSAGE_IDENTIFIED
            return ["I found this message:", "```" + self.message.author.name + ": " + self.message.content + "```", \
                    f"Does it look correct? Please respond with `{self.YES_KEYWORD}` or `{self.NO_KEYWORD}`."]
        
        if self.state == State.MESSAGE_IDENTIFIED:
            if message.content.startswith(self.HELP_KEYWORD):
                return ["Does the identified message look correct? ",
                        f"Please respond with `{self.YES_KEYWORD}` or `{self.NO_KEYWORD}`."]
            
            reply = "Thank you! Who is this report regarding?\n"
            self.help_message = f"1. If this report involves you directly, please say `{self.MYSELF_KEYWORD}`.\n"
            self.help_message += f"2. If this report does not involve you directly, please say `{self.SOMEONE_ELSE_KEYWORD}`.\n"
            
            self.state = State.AWAITING_WHO_REPORT
            return [reply, self.help_message]

        if self.state == State.AWAITING_WHO_REPORT:
            if message.content.startswith(self.HELP_KEYWORD):
                return [self.get_help_message()]
            
            if message.content.startswith(self.MYSELF_KEYWORD):
                self.who = self.MYSELF_KEYWORD
                self.help_message = self.get_report_reason_prompt()
                self.state = State.AWAITING_WHAT_REASON
                return [self.get_report_reason_prompt()]
            
            if message.content.startswith(self.SOMEONE_ELSE_KEYWORD):
                self.who = self.SOMEONE_ELSE_KEYWORD
                self.help_message = self.get_report_reason_prompt()
                self.state = State.AWAITING_WHAT_REASON
                return [self.get_report_reason_prompt()]
            
            return ["I'm sorry, I didn't understand that response. Please try again or say `cancel` to cancel."]

        return []

    def get_help_message(self):
        return self.help_message + f"You may say `{self.CANCEL_KEYWORD}` at any time to cancel this report.\n"

    def get_report_reason_prompt(self):
        prompt = "Please enter the reason for your report.\n"
        prompt += f"1. For harassment, say `{self.HARASSMENT_KEYWORD}`.\n"
        prompt += f"2. For dangerous information, say `{self.DANGEROUS_INFO_KEYWORD}`.\n"
        prompt += f"3. For misleading information, say `{self.MISLEADING_INFO_KEYWORD}`.\n"
        prompt += f"4. For explicit content, say `{self.EXPLICIT_KEYWORD}`.\n"
        prompt += f"5. For other reasons, say `{self.OTHER_KEYWORD}`.\n"
        return prompt

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE or self.state == State.REPORT_CANCELLED
    


    

