import json
import time

from dotenv import load_dotenv

load_dotenv()

import structlog  # noqa: E402
from labeler import label_email  # noqa: E402
from provider import gmail  # noqa: E402
from provider.utils import Email  # noqa: E402


def display_email_debug(email: Email):
    log: structlog.stdlib.BoundLogger = structlog.get_logger()
    log.debug("Recived email", email=email)


def dump_as_json(emails: list[Email]):
    email_dicts = [email.__dict__ for email in emails]
    with open("emails.json", "w") as f:
        json.dump(email_dicts, f)


def load_from_json():
    with open("emails.json", "r") as f:
        email_dicts = json.load(f)
        # Create a list of email instances from the list of dictionaries
        return [gmail.Email(**email_dict) for email_dict in email_dicts]


def main():
    structlog.configure(
        processors=[structlog.processors.JSONRenderer()],
    )
    log: structlog.stdlib.BoundLogger = structlog.get_logger()
    service = gmail.GmailProvider()

    while True:
        log.info("no new emails")
        new_emails = service.check_new_emails_since()
        if new_emails:
            for email in new_emails:
                display_email_debug(email)
                pred = label_email(email)
                service.tag_email_by_id(email, pred)
        else:
            log.info("no new emails")
        time.sleep(60)  # Check for new emails every 60 seconds


if __name__ == "__main__":
    main()
