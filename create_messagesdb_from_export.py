#! /usr/bin/env python3

"""
WhatsApp messages.db files have three important tables:

1. jid
2. chat
3. messages
"""

import argparse
import re
import sqlite3
from pathlib import Path
from typing import NamedTuple, Optional

from messages import (
    android_timestamp,
)


OUT_DB = "messages.db"


class Message(NamedTuple):
    id: int
    key_remote_jid: str
    key_from_me: Optional[int]
    key_id: str
    status: Optional[int]
    needs_push: Optional[int]
    data: Optional[str]
    timestamp: Optional[int]
    media_url: Optional[str]
    media_mime_type: Optional[str]
    media_wa_type: Optional[str]
    media_size: Optional[int]
    media_name: Optional[str]
    media_caption: Optional[str]
    media_hash: Optional[str]
    media_duration: Optional[int]
    origin: Optional[int]
    latitude: Optional[float]
    longitude: Optional[float]
    thumb_image: Optional[str]
    remote_resource: Optional[str]
    received_timestamp: Optional[int]
    send_timestamp: Optional[int]
    receipt_server_timestamp: Optional[int]
    receipt_device_timestamp: Optional[int]
    read_device_timestamp: Optional[int]
    played_device_timestamp: Optional[int]
    raw_data: Optional[bytes]
    recipient_count: Optional[int]
    participant_hash: Optional[str]
    starred: Optional[int]
    quoted_row_id: Optional[int]
    mentioned_jids: Optional[str]
    multicast_id: Optional[str]
    edit_version: Optional[int]
    media_enc_hash: Optional[str]
    payment_transaction_id: Optional[str]
    forwarded: Optional[int]
    preview_type: Optional[int]
    send_count: Optional[int]
    lookup_tables: Optional[int]
    future_message_type: Optional[int]


def default_msg_fields():
    """
    # Caller should set non-nullable fields:
    id, key_id
    # Caller should also set important fields:
    key_remote_jid, key_from_me, data, timestamp, received_timestamp
    """

    return {
        # "id": chat_id,
        # "key_remote_jid": chat_name,
        # "key_from_me": key_from_me,
        # "key_id": key_id,
        "status": 0,
        "needs_push": 0,
        # "data": text,
        # "timestamp": timestamp,
        "media_url": None,
        "media_mime_type": None,
        "media_wa_type": 0,
        "media_size": 0,
        "media_name": None,
        "media_hash": None,
        "media_duration": 0,
        "origin": 1,
        "latitude": 0.0,
        "longitude": 0.0,
        "thumb_image": None,
        "remote_resource": "",
        # "received_timestamp": timestamp,
        "send_timestamp": -1,
        "receipt_server_timestamp": -1,
        "receipt_device_timestamp": -1,
        "raw_data": None,
        "recipient_count": None,
        "read_device_timestamp": None,
        "played_device_timestamp": None,
        "media_caption": None,
        "participant_hash": None,
        "starred": None,
        "quoted_row_id": 0,
        "mentioned_jids": None,
        "multicast_id": None,
        "edit_version": 0,
        "media_enc_hash": None,
        "payment_transaction_id": None,
        "forwarded": None,
        "future_message_type": None,
        "lookup_tables": None,
        "preview_type": None,
        "send_count": None,
    }


def parse_media(fname: str) -> bytes:
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


class MessageManager:
    def __init__(self, user_name: str, db: str):
        self.user_name = user_name

        if not Path(db).exists():
            self.init_db(db)

            self.lowest_msg = 1
            self.lowest_chat = 1
        else:
            self.db_file = db
            self.con = sqlite3.connect(db)
            self.cur = self.con.cursor()

            self.lowest_msg = self._next_lowest_msg()
            self.lowest_chat = self._next_lowest_chat()

    def init_db(self, db: str):
        with open("./data/msgstore.db.schema.sql", "r") as f:
            sql_script = f.read()

        self.con = sqlite3.connect(db)
        self.cur = self.con.cursor()

        self.cur.executescript(sql_script)
        self.con.commit()

    def _next_lowest_chat(self) -> int:
        proc = self.cur.execute("SELECT _id FROM chat")
        chat_ids = [p[0] for p in proc]
        return sorted(chat_ids)[-1] + 1

    def _next_lowest_msg(self) -> int:
        proc = self.cur.execute("SELECT _id FROM legacy_available_messages_view")
        msg_ids = [p[0] for p in proc]
        return sorted(msg_ids)[-1] + 1

    def add_chat(self, chat_path: Path):
        prep_jid = "insert into jid(_id, user, server, raw_string) values (?, ?, ?, ?)"
        prep_chat = "insert into chat(_id, jid_row_id, hidden) values (?, ?, ?)"
        # prep_msg_thumb = "insert into message_thumbnails (?, ?, ?, ?, ?)"

        r = re.match(r"WhatsApp Chat with (.*).txt", chat_file)
        assert r is not None
        chat_contact = r.group(1)
        server = "s.whatsapp.net"
        chat_name = "@".join([chat_contact, server])

        self.cur.execute(prep_jid, (self.lowest_chat, chat_contact, server, chat_name))
        self.cur.execute(prep_chat, (self.lowest_chat, self.lowest_chat, 0))

        # hardcoded for testing
        line = "5/12/17, 17:48 - First Last: This is a test message"
        lines = [line]

        msg_id = 0
        for msg_id, msg in enumerate(lines):
            self.add_message(chat_name, msg, msg_id)

        self.con.commit()

        self.lowest_chat += 1
        self.lowest_msg += msg_id

    def add_message(self, chat_name: str, msg: str, msg_id: int):
        """
        Only supports text messages (no media or system) yet.
        """
        # various system messages
        if ":" not in msg:
            assert re.search(r"Your security code with .* has changed. Tap to learn more.", msg)
            return

        formatted_ts, content = msg.split(" - ")
        timestamp = android_timestamp(formatted_ts)
        if ": " not in content:
            return
        part = content.index(": ")
        contact = content[:part]
        text = content[part + 2:]

        key_from_me = 1 if contact == self.user_name else 0
        key_id = f"keyId-{self.lowest_chat:>04}-{msg_id:>04}"

        fields = default_msg_fields()

        fields["id"] = self.lowest_msg + msg_id
        fields["key_remote_jid"] = chat_name
        fields["key_from_me"] = key_from_me
        fields["key_id"] = key_id
        fields["data"] = text
        fields["timestamp"] = timestamp
        fields["received_timestamp"] = timestamp

        prep_msg = "insert into messages values (" + ", ".join(["?" for _ in range(42)]) + ")"
        self.cur.execute(prep_msg, Message(**fields))


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--chat", nargs="*", help="Chat (.txt) to add to messages.db")

    parser.add_argument("--name", help="Your full name, as it appears in your exported chat .txt files")

    args = parser.parse_args()

    msg_manager = MessageManager(args.name, OUT_DB)

    for chat in args.chat:
        msg_manager.add_chat(chat)


if __name__ == "__main__":
    main()
