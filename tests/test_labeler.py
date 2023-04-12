import json
import pytest
from pigeongpt.labeler import get_email_label
from pigeongpt.provider.gmail import Email


@pytest.fixture
def sample_emails():
    with open("emails.json", "r") as f:
        email_dicts = json.load(f)
    return [Email(**email_dict) for email_dict in email_dicts]


def test_get_email_label_default_params(sample_emails):
    for email in sample_emails:
        label = get_email_label(email)
        print(label)
        assert label in ["newsletter", "bills", "ads", "unknown"]


def test_get_email_label_custom_params(sample_emails):
    temperature = 0.8
    max_tokens = 30
    for email in sample_emails:
        label = get_email_label(email, temperature=temperature, max_tokens=max_tokens)
        assert label in ["newsletter", "bills", "ads", "unknown"]
