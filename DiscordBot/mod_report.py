from enum import Enum, auto
import discord
import re

class State(Enum):
    MOD_REPORT_START = auto()
    AWAITING_FLAG = auto()
    REVIEWING_REPORT = auto()
    IMMEDIATE_DANGER = auto()
    FINALIZE_OUTCOME = auto()
    REPORT_COMPLETE = auto()
    REPORT_CANCELLED = auto()



class ModReport:
    START_KEYWORD = "modreport"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"

    AUTO_FLAGGING_KEYWORD = "af"

    YES_KEYWORD = "yes"
    NO_KEYWORD = "no"

    def __init__(self, report_num, client, author_id):
        self.report_num = report_num
        self.author_id = author_id
        self.state = State.MOD_REPORT_START
        self.client = client
        self.helpMessage = None
        self.message = None
        self.source = None
        self.reason = None
        self.credibility = None

    def __str__(self) -> str:
        s = "--------------------------------------------------\n"
        s += f"Report Number: {self.report_num}\n"
        report_status = "In Progress"
        if self.state == State.REPORT_COMPLETE:
            report_status = "Complete"
        if self.state == State.REPORT_CANCELLED:
            report_status = "Cancelled"
        s += f"Report Status: {report_status}\n"
        s += f"Author ID: {self.author_id}\n"
        s += "--------------------------------------------------\n"
        return s
    
    async def handle_message(self, message):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''
        if self.state == State.MOD_REPORT_START:
            reply = "Please review this report.\n"
            if self.source == self.AUTO_FLAGGING_KEYWORD:
                self.helpMessage = f"Can you tell who is the victim and attacker in this report? Please say `{self.YES_KEYWORD}` or `{self.NO_KEYWORD}`."
                self.state = State.AWAITING_FLAG
                return [reply, self.helpMessage]
            self.state = State.REVIEWING_REPORT
            return [reply]

        if self.state == State.AWAITING_FLAG:
            if message.content.startswith(self.NO_KEYWORD):
                return ["Please contact a specialized team"]
            self.state = State.REVIEWING_REPORT
        
        if self.state == State.REVIEWING_REPORT:
            return [f"Is this a credible report? Please say  `{self.YES_KEYWORD}` or `{self.NO_KEYWORD}`."]
        
        if self.state == State.REVIEWING_REPORT:
            if message.content.startswith(self.YES_KEYWORD):
                self.credibility = True
                self.state = State.IMMEDIATE_DANGER
                return [f"Is the user in any immediate danger? Please say `{self.YES_KEYWORD}` or `{self.NO_KEYWORD}`."]
            else:
                self.credibility = False
                self.state = State.FINALIZE_OUTCOME

        if self.state == State.IMMEDIATE_DANGER:
            self.state = State.FINALIZE_OUTCOME
            if message.content.startswith(self.YES_KEYWORD):
                return ["Please contact a specialized team to make a final outcome on this report."]
            else:
                return ["Contact the relevant stakeholders and give the attacker a warning/education."]
        
        if self.state == State.FINALIZE_OUTCOME:
            if self.credibility == False:
                return ["No action necessary."]
            else:
                return ["Decide on necessary actions."]

        return []

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE
    


    

