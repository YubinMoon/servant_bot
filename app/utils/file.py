from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from discord import Attachment, Message


def txt_files_from_message(message: "Message"):
    files = message.attachments
    text_files: "list[Attachment]" = []
    for file in files:
        if file.filename.endswith(".txt"):
            text_files.append(file)
    return text_files
