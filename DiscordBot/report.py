from enum import Enum, auto
import discord
import re


class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE = auto()
    MESSAGE_IDENTIFIED = auto()

    AWAITING_WHO_REPORT = auto()

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

    HARASSMENT_KEYWORD = "harass"
    DANGEROUS_INFO_KEYWORD = "dangerous"
    MISLEADING_INFO_KEYWORD = "mislead"
    EXPLICIT_KEYWORD = "explicit"
    OTHER_KEYWORD = "other"

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

    TYPE_MAP = {
        HARASS_SENS_INFO_KEYWORD: "Leaking Sensitive Information",
        HARASS_BULLYING_KEYWORD: "Bullying",
        HARASS_HATE_SPEECH_KEYWORD: "Hate Speech",
        DANG_INFO_SUICIDE_KEYWORD: "Suicide/Self-Harm",
        DANG_INFO_THREAT_KEYWORD: "Threats",
        MIS_INFO_FRAUD_KEYWORD: "Fraud",
        MIS_INFO_IMPER_KEYWORD: "Impersonation",
        MIS_INFO_SPAM_KEYWORD: "Spam",
        EXPL_CONT_CHILD_KEYWORD: "Child Abuse",
        EXPL_CONT_PORN_KEYWORD: "Pornography"
    }

    def __init__(self, client, author_id):
        self.state = State.REPORT_START
        self.client = client
        self.author_id = author_id
        self.message = None
        self.message_text = "```N/A```"
        self.help_message = ""
        self.who = None
        self.have_disc = None
        self.other_username = None
        self.reason = None
        self.reason_type = None
        self.anything_else = None

    def __str__(self):
        s = "--------------------------------------------------\n"
        report_status = "In Progress"
        if self.state == State.REPORT_COMPLETE:
            report_status = "Complete"
        if self.state == State.REPORT_CANCELLED:
            report_status = "Cancelled"
        s += f"Report Status: {report_status}\n"
        s += f"Author ID: {self.author_id}\n"
        s += "--------------------------------------------------\n"
        m = self.message_text if self.message else "`Awaiting`"
        s += f"Message: {m}\n"
        s += f"Person Involved: `{self.who if self.who else 'Awaiting'}`\n"
        s += f"Other Username: `{self.other_username if self.other_username else 'N/A'}`\n"
        s += "--------------------------------------------------\n"
        s += f"Reason For Report: `{self.reason if self.reason else 'Awaiting'}`\n"
        s += f"Type: `{self.TYPE_MAP[self.reason_type] if self.reason_type else 'Awaiting'}`\n"
        s += f"Additional Comments: `{self.anything_else if self.anything_else else 'N/A'}`\n"
        s += "--------------------------------------------------\n"

        return s

    async def handle_message(self, message):
        """
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord.
        """

        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REPORT_CANCELLED
            return ["Report cancelled."]

        if message.content == self.HELP_KEYWORD:
            return self.get_help_messages()

        if self.state == State.REPORT_START:
            reply = "Thank you for starting the reporting process.\n"
            reply += f"Say `{self.CANCEL_KEYWORD}` at any time to cancel the report.\n"
            reply += f"Say `{self.HELP_KEYWORD}` at any time for more information.\n\n"
            self.help_message = (
                "Please copy paste the link to the message you want to report.\n" +
                "You can obtain this link by right-clicking the message and clicking `Copy Message Link`."
            )
            self.state = State.AWAITING_MESSAGE
            return [reply, self.help_message]

        if self.state == State.AWAITING_MESSAGE:
            # Parse out the three ID strings from the message link
            m = re.search("/(\d+)/(\d+)/(\d+)", message.content)
            if not m:
                return [
                    "I'm sorry, I couldn't read that link. Please try again or say `cancel` to cancel."
                ]
            guild = self.client.get_guild(int(m.group(1)))
            if not guild:
                return [
                    "I cannot accept reports of messages from guilds that I'm not in. Please have the guild owner add me to the guild and try again."
                ]
            channel = guild.get_channel(int(m.group(2)))
            if not channel:
                return [
                    "It seems this channel was deleted or never existed. Please try again or say `cancel` to cancel."
                ]
            try:
                self.message = await channel.fetch_message(int(m.group(3)))
            except discord.errors.NotFound:
                return [
                    "It seems this message was deleted or never existed. Please try again or say `cancel` to cancel."
                ]

            # Here we've found the message - it's up to you to decide what to do next!
            self.state = State.MESSAGE_IDENTIFIED
            message_content = self.message.content.replace('```', '``')
            self.message_text = (
                f"```{self.message.author.display_name}: {message_content}```"
            )
            self.help_message = f"I found this message: {self.message_text}\n"
            self.help_message += f"Does it look correct? Please respond with `{self.YES_KEYWORD}` or `{self.NO_KEYWORD}`. "
            return ["Thank you! ", self.help_message]

        if self.state == State.MESSAGE_IDENTIFIED:
            if message.content == self.NO_KEYWORD:
                reply = "I see. Please try again.\n"
                self.help_message = (
                    "Please copy paste the link to the message you want to report.\n" +
                    "You can obtain this link by right-clicking the message and clicking `Copy Message Link`."
                )
                self.state = State.AWAITING_MESSAGE
                return [reply, self.help_message]
            reply = "Thank you! Who is this report regarding?\n"
            self.help_message = f"1. If this report involves you directly, please say `{self.MYSELF_KEYWORD}`.\n"
            self.help_message += f"2. If this report does not involve you directly, please say `{self.SOMEONE_ELSE_KEYWORD}`.\n"
            self.state = State.AWAITING_WHO_REPORT
            return [reply, self.help_message]

        if self.state == State.AWAITING_WHO_REPORT:
            if message.content.startswith(self.MYSELF_KEYWORD):
                self.who = self.MYSELF_KEYWORD
                self.help_message = self.get_report_reason_prompt()
                self.state = State.AWAITING_WHAT_REASON
                return ["Thank you! ", self.get_report_reason_prompt()]
            if message.content.startswith(self.SOMEONE_ELSE_KEYWORD):
                self.who = self.SOMEONE_ELSE_KEYWORD
                self.help_message = (
                    f"Please respond with `{self.YES_KEYWORD}`/`{self.NO_KEYWORD}`."
                )
                self.state = State.AWAITING_HAVE_DISCORD
                return [
                    "Thank you! Does this person have a discord account? ",
                    self.help_message,
                ]
            return [
                "I'm sorry, I didn't understand that response. Please try again or say `cancel` to cancel."
            ]

        if self.state == State.AWAITING_HAVE_DISCORD:
            if message.content.startswith(self.YES_KEYWORD):
                self.have_disc = True
                self.help_message = "What is their username?"
                self.state = State.AWAITING_WHAT_USERNAME
                return ["Thank you! ", self.help_message]
            if message.content.startswith(self.NO_KEYWORD):
                self.have_disc = False
                self.help_message = self.get_report_reason_prompt()
                self.state = State.AWAITING_WHAT_REASON
                return ["Thank you! ", self.get_report_reason_prompt()]

        if self.state == State.AWAITING_WHAT_USERNAME:
            self.other_username = message.content
            self.help_message = self.get_report_reason_prompt()
            self.state = State.AWAITING_WHAT_REASON
            return ["Thank you! ", self.get_report_reason_prompt()]

        if self.state == State.AWAITING_WHAT_REASON:
            if message.content == self.HARASSMENT_KEYWORD:
                self.reason = "Harassment"
                self.help_message = self.get_harassment_type_prompt()
                self.state = State.AWAITING_REASON_TYPE
                return [
                    "Thank you! You have selected `Harassment`. ",
                    self.get_harassment_type_prompt(),
                ]
            if message.content == self.DANGEROUS_INFO_KEYWORD:
                self.reason = "Dangerous Information"
                self.help_message = self.get_dang_info_type_prompt()
                self.state = State.AWAITING_REASON_TYPE
                return [
                    "Thank you! You have selected `Dangerous Information`. ",
                    self.get_dang_info_type_prompt(),
                ]
            if message.content == self.MISLEADING_INFO_KEYWORD:
                self.reason = "Misleading Information"
                self.help_message = self.get_mis_info_type_prompt()
                self.state = State.AWAITING_REASON_TYPE
                return [
                    "Thank you! You have selected `Misleading Information`. ",
                    self.get_mis_info_type_prompt(),
                ]
            if message.content == self.EXPLICIT_KEYWORD:
                self.reason = "Explicit Content"
                self.help_message = self.get_expl_cont_type_prompt()
                self.state = State.AWAITING_REASON_TYPE
                return [
                    "Thank you! You have selected `Explicit Content`. ",
                    self.get_expl_cont_type_prompt(),
                ]
            if message.content == self.OTHER_KEYWORD:
                self.reason = "Other"
                self.help_message = "Please explain the reason for your report."
                self.state = State.AWAITING_REASON_TYPE
                return [
                    "Thank you! You have selected `Dangerous Information`. ",
                    self.help_message,
                ]
            return [
                "I'm sorry, I didn't understand that response. Please try again or say `cancel` to cancel."
            ]

        if self.state == State.AWAITING_REASON_TYPE:
            self.reason_type = message.content
            self.help_message = (
                "Please respond with anything else you would like to add to the report."
            )
            self.state = State.AWAITING_ANYTHING_ELSE
            return ["Thank you! ", self.help_message]

        if self.state == State.AWAITING_ANYTHING_ELSE:
            self.anything_else = message.content
            self.help_message = None
            self.state = State.REPORT_COMPLETE
            return [
                "Thank you! Your report has been recorded and will be processed " +
                "by our moderation team as soon as possible.",
                "Here is a summary of your report:\n" +
                str(self)
            ]

        return []

    def get_help_messages(self):
        return [
            "Here's a summary of your report so far: \n" + str(self),
            self.help_message
            + f"You may say `{self.CANCEL_KEYWORD}` at any time to cancel this report.\n",
        ]

    def get_report_reason_prompt(self):
        prompt = "Please enter the reason for your report.\n"
        prompt += f"1. For harassment, type `{self.HARASSMENT_KEYWORD}`.\n"
        prompt += (
            f"2. For dangerous information, type `{self.DANGEROUS_INFO_KEYWORD}`.\n"
        )
        prompt += (
            f"3. For misleading information, type `{self.MISLEADING_INFO_KEYWORD}`.\n"
        )
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
        prompt += (
            f"2. For threats of violence, type `{self.DANG_INFO_THREAT_KEYWORD}`.\n"
        )
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
        return (
            self.state == State.REPORT_COMPLETE or self.state == State.REPORT_CANCELLED
        )
