import json

import structlog

from pigeongpt.provider.utils import Email


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
        return [Email(**email_dict) for email_dict in email_dicts]
