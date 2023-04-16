import os
import time

import structlog
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from pigeongpt.provider.utils import (
    Email,
    clean_html_content,
    parse_payload_for_text,
    remove_urls,
)

CLIENT_SECRET_FILE = "client_secret.json"
API_NAME = "gmail"
API_VERSION = "v1"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.labels",
]


log: structlog.stdlib.BoundLogger = structlog.get_logger()


class GmailProvider:
    _gmail_api_service = None
    _label_mapping = None

    def __init__(self) -> None:
        self._get_gmail_api_service()
        self._retrieve_labels()

    def _get_gmail_api_service(self):
        if self._gmail_api_service:
            return self._gmail_api_service

        creds = None
        if os.path.exists("token.json"):
            with open("token.json", "rb") as token:
                creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        if not creds or not creds.valid or not creds.has_scopes(SCOPES):
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CLIENT_SECRET_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open("token.json", "w") as token:
                token.write(creds.to_json())

        self._gmail_api_service = build(API_NAME, API_VERSION, credentials=creds)
        return self._gmail_api_service

    def _retrieve_labels(self):
        if self._label_mapping:
            return self._label_mapping

        service = self._get_gmail_api_service()
        results = service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])
        if not labels:
            log.warning("No labels found.")
        else:
            label_dict = {label["name"]: label["id"] for label in labels}
            log.info(f"Labels: {label_dict}")
            self._label_mapping = label_dict

        return self._label_mapping

    def _get_email_details_by_id(self, message_id: str):
        msg = (
            self._get_gmail_api_service()
            .users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        headers = msg["payload"]["headers"]

        subject, sender, payload = "", "", msg["payload"]
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

        return Email(message_id, subject, sender, raw_content, content, mime_type)

    def check_new_emails_since(
        self, last_check_epoch=int(time.time_ns() // 1e9 - (24 * 60 * 60))
    ) -> list[Email]:
        query = f"after:{last_check_epoch}"
        service = self._get_gmail_api_service()
        # userId = 'me', only check the service owner's email
        log.debug(f"query gmail with: q={query}")
        results = service.users().messages().list(userId="me", q=query).execute()
        raw_messages = results.get("messages", [])
        parsed_messages = []

        while len(raw_messages):
            parsed = [self._get_email_details_by_id(msg["id"]) for msg in raw_messages]
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

    def tag_email_by_id(self, email: Email, label_name: str):
        service = self._get_gmail_api_service()
        labels = self._retrieve_labels()

        message_id = email.id
        if label_name not in labels:
            log.error(f"Label {label_name} not found.")
            return

        label_id = labels[label_name]
        label_data = {"addLabelIds": [label_id]}
        response = (
            service.users()
            .messages()
            .modify(userId="me", id=message_id, body=label_data)
            .execute()
        )

        log.info(f"Message with ID {message_id} has been labeled with {label_name}.")
        return response
