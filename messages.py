#! /usr/bin/env python3

"""
Helpers for parsing "WhatsApp Chat with x.txt" files
"""

import datetime


def android_timestamp(formatted_ts: str) -> int:
    """
    get unix timestamp for message
    """
    return int(datetime.datetime.strptime(formatted_ts, "%m/%d/%y, %H:%M").strftime("%s")) * 1000
