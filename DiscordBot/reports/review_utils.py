import discord
import pickle
import pathlib
import re

from typing import Optional, Union

from report import Report
from mod_review import ModReview
from reports.report_utils import load_report

here = pathlib.Path(__file__).parent.resolve()
storage = here / "storage"


def _review_filename(review_num: int) -> str:
    return f"review_{review_num}.pickle"


async def load_review(review_num: int, client: discord.Client) -> Optional[ModReview]:
    review_loc = storage / _review_filename(review_num)
    if not review_loc.exists():
        return None
    
    with review_loc.open("rb") as f:
        review: ModReview = pickle.load(f)
        review.client = client
        try:
            review.mod_channels = client.mod_channels
        except:
            review.mod_channels = None
        review.report = await load_report(review.report_num, client)

        return review

async def store_review(review: ModReview):
    review.client = None
    review.mod_channels = None
    review.report = None

    review_num = review.report_num
    review_loc = storage / _review_filename(review_num)
    with review_loc.open("wb") as f:
        pickle.dump(review, f)
