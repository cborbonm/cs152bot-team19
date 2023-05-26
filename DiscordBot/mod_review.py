from enum import Enum, auto
import discord
import logging
import re
from reports.report_utils import load_report, store_report


class State(Enum):
    MOD_REPORT_START = auto()

    AWAITING_REPORT_NUMBER = auto()
    AWAITING_FLAG = auto()

    REVIEWING_REPORT = auto()
    AWAITING_CREDIBLE = auto()

    AWAITING_IMMEDIATE_DANGER = auto()
    FINALIZE_OUTCOME = auto()
    AWAITING_DECISION = auto()

    REPORT_COMPLETE = auto()
    REPORT_CANCELLED = auto()
    MOD_REPORT_COMPLETE = auto()


class ModReview:
    START_KEYWORD = "review"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"

    AUTO_FLAGGING_KEYWORD = "af"
    USER_REPORT_KEYWORD = "user"

    NO_ACTION_KEYWORD = "no action"
    REMOVE_POST_KEYWORD = "remove post"
    BAN_OFFENDER_KEYWORD = "offender ban"
    ENGAGE_LAW_KEYWORD = "law enforcement"
    BOTH_ACTIONS_KEYWORD = "max penalty"

    YES_KEYWORD = "yes"
    NO_KEYWORD = "no"

    def __init__(self, review_num, client, mod_id, mod_channels):
        self.is_review = True
        self.review_num = review_num
        self.mod_channels = mod_channels
        self.client = client

        self.report_num = None
        self.report = None

        self.guild_id = None
        self.mod_id = mod_id
        
        self.state = State.MOD_REPORT_START
        self.help_message = ""
        self.reason = None
        self.credibility = None
        
        self.outcome = []
        self.followups = []
        self.victim_resources = None

    def __str__(self) -> str:
        s = "--------------------------------------------------\n"
        s += f"Mod Review Number: {self.review_num}\n"
        report_status = "In Progress"
        if self.state == State.REPORT_COMPLETE:
            report_status = "Complete"
        if self.state == State.REPORT_CANCELLED:
            report_status = "Cancelled"
        s += f"Review Status: {report_status}\n"
        s += f"Mod ID: {self.mod_id}\n"
        s += f"Report Number: {self.report_num if self.report_num else '`Awaiting`'}\n"
        s += "--------------------------------------------------\n"
        return s

    async def handle_message(self, message):
        """
        This function makes up the meat of the moderator reporting flow. It defines how we transition between states and what
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord.
        """

        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REPORT_CANCELLED
            return ["Report cancelled."]

        if message.content == self.HELP_KEYWORD:
            return self.get_help_messages()

        if self.state == State.MOD_REPORT_START:
            self.help_message = "Please enter the report number you wish to review.\n"
            self.state = State.AWAITING_REPORT_NUMBER
            return [self.help_message]

        if self.state == State.AWAITING_REPORT_NUMBER:
            self.report = await load_report(int(message.content), self.client)
            if not self.report:
                reply = "Error loading report. Please try again.\n"
                return [reply, self.help_message]
            self.guild_id = self.report.guild_id
            reply = "Please review this report.\n"
            if self.report.source == self.AUTO_FLAGGING_KEYWORD:
                self.help_message = f"Can you tell who is the victim and offender in this report? Please say `{self.YES_KEYWORD}` or `{self.NO_KEYWORD}`."
                self.state = State.AWAITING_FLAG
                return [reply, str(self.report), self.help_message]
            self.state = State.AWAITING_CREDIBLE
            self.help_message = f"Is this a credible report? Please say  `{self.YES_KEYWORD}` or `{self.NO_KEYWORD}`."
            return [reply, str(self.report), self.help_message]

        if self.state == State.AWAITING_FLAG:
            self.state = State.AWAITING_CREDIBLE
            self.help_message = f"Is this a credible report? Please say  `{self.YES_KEYWORD}` or `{self.NO_KEYWORD}`."
            if message.content.startswith(self.NO_KEYWORD):
                self.help_message = (
                    "Please contact a specialized team.\n" + self.help_message
                )
            return [reply, str(self.report), self.help_message]

        if self.state == State.AWAITING_CREDIBLE:
            if message.content.startswith(self.YES_KEYWORD):
                self.credibility = True
                self.state = State.AWAITING_IMMEDIATE_DANGER
                self.help_message = f"Is the user in any immediate danger? Please say `{self.YES_KEYWORD}` or `{self.NO_KEYWORD}`."
                return [self.help_message]
            else:
                self.credibility = False
                self.help_message = "No action necessary."
                self.state = State.MOD_REPORT_COMPLETE
                await self.no_action_outcome()
                await self.send_followup()
                return [self.help_message]

        if self.state == State.AWAITING_IMMEDIATE_DANGER:
            self.state = State.AWAITING_DECISION
            self.help_message = self.get_decision_prompt()
            if message.content.startswith(self.YES_KEYWORD):
                mod_notif = "Detected Immediate Danger!\n" + str(self.report)
                await self.mod_channels[self.report.message.guild.id].send(mod_notif)
                return [
                    "Please contact a specialized team to make a final outcome on this report.",
                    self.help_message,
                ]
            else:
                self.victim_resources = "*Resources for the victim*"
                return [self.help_message]

        # if self.state == State.FINALIZE_OUTCOME:
        #     self.state = State.MOD_REPORT_COMPLETE
        #     if self.credibility == False:
        #         return ["No action necessary."]
        #     else:
        #         return ["Based on the contents of the reports what steps should be taken?\n" +
        #                 "The following options include\n" +
        #                 "1. No action\n"+
        #                 "2. Attacker account temporary suspension/permanent ban \n" +
        #                 "3. Contact law enforcement. \n" +
        #                 f"For option 1 say: `{self.NO_ACTION_KEYWORD}`\n" +
        #                 f"For option 2 say: `{self.BAN_ATTACKER_KEYWORD}`\n" +
        #                 f"For option 3 say: `{self.ENGAGE_LAW_KEYWORD}`\n" +
        #                 f"For both option 2 and 3 say: `{self.BOTH_ACTIONS_KEYWORD}`\n"
        #                 ]

        if self.state == State.AWAITING_DECISION:
            self.state = State.MOD_REPORT_COMPLETE
            reply = []
            if message.content.startswith(self.NO_ACTION_KEYWORD):
                await self.no_action_outcome()
                reply = [
                    "The user who submitted report will be notified that no action will be taken."
                ]
            elif message.content.startswith(self.REMOVE_POST_KEYWORD):
                await self.remove_post_outcome()
                reply = ["The victim will be notified of the actions taken."]
            elif message.content.startswith(self.BAN_OFFENDER_KEYWORD):
                await self.ban_offender_outcome()
                reply = ["The victim will be notified of the actions taken."]
            elif message.content.startswith(self.ENGAGE_LAW_KEYWORD):
                await self.engage_law_outcome()
                reply = ["Law enforcement will be contacted."]
            elif message.content.startswith(self.BOTH_ACTIONS_KEYWORD):
                await self.ban_offender_outcome()
                await self.engage_law_outcome()
                reply = ["Law enforcement will be contacted."]

            # await self.send_followup()
            return reply
        return []

    async def no_action_outcome(self):
        reporter_update = f"Update regarding report number {self.report.report_num}.\n"
        reporter_update += "-No action will be taken."
        self.outcome.append(self.NO_ACTION_KEYWORD)
        self.followups.append(reporter_update)
        # await self.report.author_channel.send(reporter_update)

    async def remove_post_outcome(self):
        reporter_update = f"Update regarding report number {self.report.report_num}.\n"
        reporter_update += "-The post will be removed."
        self.outcome.append(self.REMOVE_POST_KEYWORD)
        self.followups.append(reporter_update)
        # await self.report.author_channel.send(reporter_update)
        await self.mod_channels[self.report.message.guild.id].send(
            f"--Remove message: {self.report.message_link}--"
        )

    async def ban_offender_outcome(self):
        reporter_update = f"Update regarding report number {self.report.report_num}.\n"
        reporter_update += "-The offending account will be suspended."
        self.outcome.append(self.BAN_OFFENDER_KEYWORD)
        self.followups.append(reporter_update)
        # await self.report.author_channel.send(reporter_update)
        await self.mod_channels[self.report.message.guild.id].send(
            f"--Ban offender from message: {self.report.message_link}--"
        )

    async def engage_law_outcome(self):
        reporter_update = f"Update regarding report number {self.report.report_num}.\n"
        reporter_update += "-Law enforcement will be engaged."
        self.outcome.append(self.ENGAGE_LAW_KEYWORD)
        self.followups.append(reporter_update)
        # await self.report.author_channel.send(reporter_update)
        await self.mod_channels[self.report.message.guild.id].send(
            f"--Please engage law enforcement!-- \n {self.report}"
        )

    async def send_followup(self):
        for msg in self.followups:
            await self.report.author_channel.send(msg)
        if self.victim_resources:
            await self.report.author_channel.send(self.victim_resources)

    def get_help_messages(self):
        return [
            "Here's a summary of your report so far: \n" + str(self),
            self.help_message
            + f"You may say `{self.CANCEL_KEYWORD}` at any time to cancel this report.\n",
        ]

    def get_decision_prompt(self):
        return (
            "Based on the contents of the reports what steps should be taken?\n"
            + "The options include: \n"
            + "1. No action\n"
            + "2. Remove post\n"
            + "3. Offending account temporary suspension/permanent ban \n"
            + "4. Contact law enforcement. \n"
            + f"For option 1 say: `{self.NO_ACTION_KEYWORD}`\n"
            + f"For option 2 say: `{self.REMOVE_POST_KEYWORD}`\n"
            + f"For option 2 say: `{self.BAN_OFFENDER_KEYWORD}`\n"
            + f"For option 3 say: `{self.ENGAGE_LAW_KEYWORD}`\n"
            + f"For both option 2 and 3 say: `{self.BOTH_ACTIONS_KEYWORD}`\n"
        )

    def report_complete(self):
        return self.state == State.MOD_REPORT_COMPLETE
