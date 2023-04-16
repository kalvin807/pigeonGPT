import time

from dotenv import load_dotenv

load_dotenv()

import structlog  # noqa: E402
from labeler import label_email  # noqa: E402
from provider import gmail  # noqa: E402

COOLDOWN_SECOND = 60


def main():
    structlog.configure(
        processors=[structlog.processors.JSONRenderer()],
    )
    log: structlog.stdlib.BoundLogger = structlog.get_logger()
    service = gmail.GmailProvider()

    # At start-up, check emails 1 mins ago
    last_check = int(time.time_ns() // 1e9 - 60)

    while True:
        new_emails = service.check_new_emails_since(last_check)
        if new_emails:
            for email in new_emails:
                try:
                    pred = label_email(email)
                    service.tag_email_by_id(email, pred)
                except Exception as e:
                    log.error("error during lableing email", error=e)

        else:
            log.info("no new emails")
        last_check = int(time.time_ns() // 1e9)
        time.sleep(COOLDOWN_SECOND)  # Check for new emails every 60 seconds


if __name__ == "__main__":
    main()
