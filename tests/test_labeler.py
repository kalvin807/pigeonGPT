import json

import pytest

from pigeongpt.labeler import label_email, summarise_content
from pigeongpt.provider.gmail import Email


@pytest.fixture
def sample_emails():
    with open("emails.json", "r") as f:
        email_dicts = json.load(f)
    return [Email(**email_dict) for email_dict in email_dicts]


def test_get_email_label_default_params(sample_emails):
    for email in sample_emails[:3]:
        label = label_email(email)
        print(label)
        assert label in ["newsletter", "bills", "ads", "unknown"]


def test_get_email_summaiser(sample_emails):
    email = sample_emails[2]
    result = summarise_content(email.content)
    assert result is str
