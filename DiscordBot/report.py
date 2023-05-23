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
    AWAITING_REASON_TYPE = auto()
    AWAITING_ANYTHING_ELSE = auto()

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

    HARASS_SENS_INFO_KEYWORD = "l"
    HARASS_BULLYING_KEYWORD = "b"
    HARASS_HATE_SPEECH_KEYWORD = "h"

    DANG_INFO_SUICIDE_KEYWORD = "s"
    DANG_INFO_THREAT_KEYWORD = "t"

    MIS_INFO_FRAUD_KEYWORD = "f"
    MIS_INFO_IMPER_KEYWORD = "i"
    MIS_INFO_SPAM_KEYWORD = "s"

    EXPL_CONT_CHILD_KEYWORD = "c"
    EXPL_CONT_PORN_KEYWORD = "p"


    def __init__(self, client):
        self.state = State.REPORT_START
        self.client = client
        self.message = None
        self.help_message = ""
        self.who = None
        self.account = None
        self.reason = None
        self.reason_type = None
        self.anything_else = None
    
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
            reply += f"Say `{self.CANCEL_KEYWORD}` at any time to cancel the report."
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
                return ["Thank you! ", self.get_report_reason_prompt()]
            
            if message.content.startswith(self.SOMEONE_ELSE_KEYWORD):
                self.who = self.SOMEONE_ELSE_KEYWORD
                self.help_message = self.get_report_reason_prompt()
                self.state = State.AWAITING_WHAT_REASON
                return ["Thank you! ", self.get_report_reason_prompt()]
            
            return ["I'm sorry, I didn't understand that response. Please try again or say `cancel` to cancel."]

        if self.state == State.AWAITING_WHAT_REASON:
            if message.content == self.HELP_KEYWORD:
                return [self.get_help_message()]
            
            if message.content == self.HARASSMENT_KEYWORD:
                self.reason = self.HARASSMENT_KEYWORD
                self.help_message = self.get_harassment_type_prompt()
                self.state = State.AWAITING_REASON_TYPE
                return ["Thank you! You have selected `Harassment`. ", 
                        self.get_harassment_type_prompt()]
            
            if message.content == self.DANGEROUS_INFO_KEYWORD:
                self.reason = self.DANGEROUS_INFO_KEYWORD
                self.help_message = self.get_dang_info_type_prompt()
                self.state = State.AWAITING_REASON_TYPE
                return ["Thank you! You have selected `Dangerous Information`. ", 
                        self.get_dang_info_type_prompt()]
            
            if message.content == self.MISLEADING_INFO_KEYWORD:
                self.reason = self.MISLEADING_INFO_KEYWORD
                self.help_message = self.get_mis_info_type_prompt()
                self.state = State.AWAITING_REASON_TYPE
                return ["Thank you! You have selected `Misleading Information`. ", 
                        self.get_mis_info_type_prompt()]
            
            if message.content == self.EXPLICIT_KEYWORD:
                self.reason = self.EXPLICIT_KEYWORD
                self.help_message = self.get_expl_cont_type_prompt()
                self.state = State.AWAITING_REASON_TYPE
                return ["Thank you! You have selected `Explicit Content`. ", 
                        self.get_expl_cont_type_prompt()]
            
            if message.content == self.OTHER_KEYWORD:
                self.reason = self.OTHER_KEYWORD
                self.help_message = "Please explain the reason for your report."
                self.state = State.AWAITING_REASON_TYPE
                return ["Thank you! You have selected `Dangerous Information`. ", 
                        self.help_message]

            return ["I'm sorry, I didn't understand that response. Please try again or say `cancel` to cancel."]

        if self.state == State.AWAITING_REASON_TYPE:
            if message.content == self.HELP_KEYWORD:
                return [self.get_help_message()]
            
            self.reason_type = message.content
            self.help_message = "Please respond with anything else you would like to add to the report."
            self.state = State.AWAITING_ANYTHING_ELSE
            return ["Thank you! ", self.help_message]
        
        if self.state == State.AWAITING_ANYTHING_ELSE:
            if message.content == self.HELP_KEYWORD:
                return [self.get_help_message()]

            self.anything_else = message.content
            self.help_message = None
            self.state = State.REPORT_COMPLETE
            return ["Thank you! Your report has been recorded and will be processed by our moderation team soon."]

        return []

    def get_help_message(self):
        return self.help_message + f"You may say `{self.CANCEL_KEYWORD}` at any time to cancel this report.\n"

    def get_report_reason_prompt(self):
        prompt = "Please enter the reason for your report.\n"
        prompt += f"1. For harassment, type `{self.HARASSMENT_KEYWORD}`.\n"
        prompt += f"2. For dangerous information, type `{self.DANGEROUS_INFO_KEYWORD}`.\n"
        prompt += f"3. For misleading information, type `{self.MISLEADING_INFO_KEYWORD}`.\n"
        prompt += f"4. For explicit content, type `{self.EXPLICIT_KEYWORD}`.\n"
        prompt += f"5. For other reasons, type `{self.OTHER_KEYWORD}`.\n"
        return prompt

    def get_harassment_type_prompt(self):
        prompt = "Please select the type of harassment.\n"
        prompt += f"1. For leaking sensitive information, type `{self.HARASS_SENS_INFO_KEYWORD}`.\n"
        prompt += f"2. For bullying, type `{self.HARASS_BULLYING_KEYWORD}`.\n"
        prompt += f"3. For hate speech, type `{self.HARASS_HATE_SPEECH_KEYWORD}`.\n"
        return prompt

    def get_dang_info_type_prompt(self):
        prompt = "Please select the type of dangerous information.\n"
        prompt += f"1. For suicide/self-harm content, type `{self.DANG_INFO_SUICIDE_KEYWORD}`.\n"
        prompt += f"2. For threats of violence, type `{self.DANG_INFO_THREAT_KEYWORD}`.\n"
        return prompt

    def get_mis_info_type_prompt(self):
        prompt = "Please select the type of misleading information.\n"
        prompt += f"1. For fraud, type `{self.MIS_INFO_FRAUD_KEYWORD}`.\n"
        prompt += f"2. For impersonation, type `{self.MIS_INFO_IMPER_KEYWORD}`.\n"
        prompt += f"3. For spam, type `{self.MIS_INFO_SPAM_KEYWORD}`.\n"
        return prompt

    def get_expl_cont_type_prompt(self):
        prompt = "Please select the type of explicit content.\n"
        prompt += f"1. For child abuse or harassment, type `{self.EXPL_CONT_CHILD_KEYWORD}`.\n"
        prompt += f"2. For pornography, type `{self.EXPL_CONT_PORN_KEYWORD}`.\n"
        return prompt

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE or self.state == State.REPORT_CANCELLED
    


    

