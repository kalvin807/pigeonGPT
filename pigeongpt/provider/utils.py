import base64
import re
from dataclasses import dataclass

from bs4 import BeautifulSoup


@dataclass
class Email:
    id: str
    subject: str
    sender: str
    raw_content: str
    content: str
    mime_type: str


def clean_html_content(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "lxml")
    for script in soup(["script", "style"]):
        script.decompose()
    text = soup.get_text()
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace("\xa0", " ")

    return text


def remove_urls(text: str):
    url_pattern = re.compile(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    )
    return url_pattern.sub("", text)


def parse_payload_for_text(payload):
    if "parts" in payload:
        text_content = ""
        mime_type = None
        for part in payload["parts"]:
            text_content_partials, mime_type_partials = parse_payload_for_text(part)
            if text_content_partials and mime_type_partials:
                text_content += text_content_partials
                mime_type = mime_type_partials
        return text_content, mime_type
    else:
        return (
            base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8"),
            payload.get("mimeType", None),
        )
