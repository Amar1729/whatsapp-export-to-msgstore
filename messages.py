#! /usr/bin/env python3

"""
Helpers for parsing "WhatsApp Chat with x.txt" files
"""

import datetime
import re
from enum import Enum
from pathlib import Path


class MsgType(Enum):
    SYSTEM = 1
    TEXT = 2
    MEDIA = 3
    CALL = 4


def android_timestamp(formatted_ts: str) -> int:
    """
    get unix timestamp for message
    """
    return int(datetime.datetime.strptime(formatted_ts, "%m/%d/%y, %H:%M").strftime("%s")) * 1000


def parse_media(fname: Path) -> bytes:
    """
    Return raw bytes of a media file.
    """
    with open(fname, "rb") as f:
        content = f.read()

    blob_str = "".join([
        f"{hex(b)[2:]:>02}"
        for b in content
    ])

    return blob_str.encode()


class TxtMessage:
    def __init__(self, timestamp: int, content: str, chat_dir: Path):
        self.timestamp = timestamp

        if ": " in content:
            part_msg = content.index(": ")
            self.contact_name = content[:part_msg]
            text = content[part_msg + 2:]
        else:
            self.contact_name = ""
            text = content

        # SYSTEM
        if re.match(r"Your security code with (.*) changed. Tap to learn more.", text):
            self.type = MsgType.SYSTEM
            self.content = text

        # CALL
        elif re.match(r"^Missed video call$", text):
            self.type = MsgType.CALL
            self.content = ""

        # MEDIA
        elif msg_file := re.match(r"(.*) \(file attached\)(.*)$", text, flags=re.DOTALL | re.MULTILINE):
            m_file = msg_file.group(1)
            caption = msg_file.group(2).strip()

            if Path(chat_dir, m_file).exists():
                self.blob = parse_media(Path(chat_dir, m_file))
            else:
                self.blob = b""

            self.type = MsgType.MEDIA
            self.content = m_file
            self.caption = caption

        # MEDIA (chat was exported without including media)
        elif re.match(r"<Media omitted>$", text):
            self.type = MsgType.MEDIA
            self.blob = b""
            self.content = ""
            self.caption = ""

        # TEXT
        else:
            self.type = MsgType.TEXT
            self.content = text

    def __str__(self) -> str:
        fts = datetime.datetime.fromtimestamp(self.timestamp // 1000)
        our_header = f"({self.type}) {fts.strftime('%m/%d/%y %H:%M')} - "

        if self.type == MsgType.MEDIA:
            return our_header + f"{self.content} - {len(self.blob)} ({self.caption})"
        elif self.type == MsgType.SYSTEM:
            return our_header + f"{self.content}"
        else:
            return our_header + f"{self.contact_name}: {self.content}"


def is_msg(text: str) -> tuple[bool, tuple[int, str]]:
    r = re.match(r"(\d{1,2}/\d{1,2}/\d{1,2}, \d{1,2}:\d\d) - (.*)", text)

    if r:
        formatted_ts = r.group(1)
        timestamp = android_timestamp(formatted_ts)
        content = r.group(2)

        return (True, (timestamp, content))

    else:
        return (False, (0, ""))


class ChatParser:
    def __init__(self, chat_path: Path):
        self.lines = open(chat_path, "r").read().splitlines()
        self.chat_path = chat_path

    def __iter__(self):
        return self

    def __next__(self):
        while self.lines:
            check_msg, (timestamp, content) = is_msg(self.lines.pop(0))
            full_content = [content]

            while self.lines and not is_msg(self.lines[0])[0]:
                full_content.append(self.lines.pop(0))

            return TxtMessage(timestamp, "\n".join(full_content), self.chat_path.parent)

        raise StopIteration
