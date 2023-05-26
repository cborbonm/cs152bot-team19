import discord
import pickle
import pathlib
import re

from typing import Optional, Union

from report import Report

here = pathlib.Path(__file__).parent.resolve()
storage = here / "storage"


def _report_filename(report_num: int) -> str:
    return f"report_{report_num}.pickle"


async def load_report(report_num: int, client: discord.Client) -> Optional[Report]:
    report_loc = storage / _report_filename(report_num)
    if not report_loc.exists():
        return None
    
    with report_loc.open("rb") as f:
        report: Report = pickle.load(f)
        report.client = client

        # Parse out the three ID strings from the message link
        m = re.search("/(\d+)/(\d+)/(\d+)", report.message_link)
        if not m:
            return None
        guild = report.client.get_guild(int(m.group(1)))
        if not guild:
            return None
        channel = guild.get_channel(int(m.group(2)))
        if not channel:
            report.message = None
        else:
            try:
                report.message = await channel.fetch_message(int(m.group(3)))
            except discord.errors.NotFound:
                report.message = None

        # Get author channel
        report.author_channel = await client.fetch_channel(report.author_channel_id)
        return report

async def store_report(report: Report):
    report.client = None
    report.author_channel = None
    report.message = None
    report.mod_channels = None

    report_num = report.report_num
    report_loc = storage / _report_filename(report_num)
    with report_loc.open("wb") as f:
        pickle.dump(report, f)
