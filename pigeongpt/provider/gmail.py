import base64
import os
import re
import time
from dataclasses import dataclass

import structlog
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CLIENT_SECRET_FILE = "client_secret.json"
API_NAME = "gmail"
API_VERSION = "v1"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

log: structlog.stdlib.BoundLogger = structlog.get_logger()


@dataclass
class Email:
    subject: str
    sender: str
    raw_content: str
    content: str
    mime_type: str


def clean_html_content(raw_html):
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


class GmailProvider:
    service = None

    def get_email_details(self, message_id):
        msg = (
            self.get_gmail_service()
            .users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        headers = msg["payload"]["headers"]

        subject, sender, payload = None, None, msg["payload"]
        for header in headers:
            if header["name"].lower() == "subject":
                subject = header["value"]
            if header["name"].lower() == "from":
                sender = header["value"]

        raw_content, mime_type = parse_payload_for_text(payload)

        # Clean content based on MIME type
        if mime_type == "text/html":
            content = clean_html_content(raw_content)
        else:
            content = raw_content.strip()
        content = remove_urls(content)

        return Email(subject, sender, raw_content, content, mime_type)

    def get_gmail_service(self):
        if self.service:
            return self.service

        creds = None
        if os.path.exists("token.json"):
            with open("token.json", "rb") as token:
                creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CLIENT_SECRET_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open("token.json", "w") as token:
                token.write(creds.to_json())

        self.service = build(API_NAME, API_VERSION, credentials=creds)
        return self.service

    def check_new_emails(
        self, last_check_epoch=int(time.time_ns() // 1e9 - (24 * 60 * 60))
    ) -> list[Email]:
        query = f"after:{last_check_epoch}"
        service = self.get_gmail_service()
        # userId = 'me', only check the service owner's email
        log.debug(f"query gmail with: q={query}")
        results = service.users().messages().list(userId="me", q=query).execute()
        raw_messages = results.get("messages", [])
        parsed_messages = []

        while len(raw_messages):
            parsed = [self.get_email_details(msg["id"]) for msg in raw_messages]
            parsed_messages += parsed
            raw_messages = []
            nextPageToken = results.get("nextPageToken", None)
            if nextPageToken:
                results = (
                    service.users()
                    .messages()
                    .list(userId="me", q=query, pageToken=nextPageToken)
                    .execute()
                )
                raw_messages = results.get("messages", [])
        return parsed_messages
