# Create `messages.db` from exported WhatsApp chats

WhatsApp chats can be [individually exported](https://faq.whatsapp.com/android/chats/how-to-save-your-chat-history/?lang=en) to `.txt` files (and, if media is included, associated media files).

However, most tools for managing WhatsApp chats expect a `messages.db` file, which is typically retrieved by getting your phone's `messages.db.crypt` file from WhatsApp and then decrypting it.

There are a few tools to facilitate this[1][2], but they can require a rooted phone or some particular magic via `adb` to decrypt your whatsapp chats.

Instead, this project is focused on converting an exported chat's `.txt` file to the `messages.db` format.


## Usage

This project uses only stdlib `python3.8` or greater.

```
python3 ./create_messagesdb_from_export.py --name "Your Name" --chat chat1.txt chat2.txt chat3.txt
```

This command will import each chat you specify into a local `messages.db` sqlite3 file. That file can then be used by other projects that expect it, or viewed in a sqlite3 browser.


## Development

The [whatsapp-viewer](https://github.com/andreas-mausch/whatsapp-viewer) project was extremely useful for figuring out the `messages.db` database scheme and generating the proper conversion to a sqlite database.

The `.sql` files under `./data` are copied from that repository (MIT License).


## References

1. https://github.com/MarcoG3/WhatsDump
2. https://github.com/EliteAndroidApps/WhatsApp-Key-DB-Extractor
