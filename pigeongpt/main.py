import json
import time

from dotenv import load_dotenv

load_dotenv()

from labeler import label_email
from provider import gmail


def display_email_debug(email: gmail.Email):
    print(
        f"subject: {email.subject} | sender: {email.sender} | content : {email.content}"
    )


def dump_as_json(emails):
    email_dicts = [email.__dict__ for email in emails]
    with open("emails.json", "w") as f:
        json.dump(email_dicts, f)


def load_from_json():
    with open("emails.json", "r") as f:
        email_dicts = json.load(f)
        # Create a list of email instances from the list of dictionaries
        return [gmail.Email(**email_dict) for email_dict in email_dicts]


def main():
    print("hi")
    service = gmail.GmailProvider()

    while True:
        print("check new emails")
        new_emails = service.check_new_emails()
        dump_as_json(new_emails)
        if new_emails:
            print(f"You have {len(new_emails)} new email(s)!")
            for email in new_emails:
                display_email_debug(email)
                pred = label_email(email)
                print(pred)
        else:
            print("no new emails")
        time.sleep(60)  # Check for new emails every 60 seconds


if __name__ == "__main__":
    main()
