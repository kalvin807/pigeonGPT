import base64
import os
import time
from dataclasses import dataclass

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CLIENT_SECRET_FILE = "client_secret.json"
API_NAME = "gmail"
API_VERSION = "v1"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


@dataclass
class Email:
    subject: str
    sender: str
    content: str


def parse_payload_for_text(payload):
    if "parts" in payload:
        text_content = ""
        for part in payload["parts"]:
            if text_content_partials := parse_payload_for_text(part):
                text_content += text_content_partials
        return text_content
    else:
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")


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

        content = parse_payload_for_text(payload)

        return Email(subject, sender, content)

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
        print(f"query gmail with: q={query}")
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
