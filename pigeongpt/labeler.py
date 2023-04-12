import os
import re
import openai
import tiktoken
from pigeongpt.provider import gmail

openai.api_key = os.getenv("OPENAI_API_KEY")
enc = tiktoken.get_encoding("cl100k_base")


def get_gpt_response(prompt, temperature=0.0):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def estimate_token_size(prompt):
    return len(enc.encode(prompt))


def split_by_size(content_string, size=1000):
    return [content_string[i : i + size] for i in range(0, len(content_string), size)]


def summary_string(content_string):
    prompt = f"summarise following content: {content_string} in not more than 100 words"
    response = get_gpt_response(prompt)
    return response.choices[0].message.content.strip()


def preprocess_email(email):
    prompt = f"Given the following email:\n\nSubject: {email.subject}\nSender: {email.sender}\nContent:\n{email.content}\n\nDetermine the nature of this email. The possible labels are 'newsletter', 'bills', or 'ads', 'unknown'.\n\nReply the label by wrapping '###'. Only reply the label with wrap."
    if estimate_token_size(prompt) > 3000:
        splited_contents = split_by_size(email.content)
        compress_with_summary = "\n".join(
            [summary_string(text) for text in splited_contents]
        )
        email.content = compress_with_summary
    return email


def get_email_label(email: gmail.Email):
    processed_email = preprocess_email(email)

    prompt = f"Given the following email:\n\nSubject: {processed_email.subject}\nSender: {processed_email.sender}\nContent:\n{email.content}\n\nDetermine the nature of this email. The possible labels are 'newsletter', 'bills', or 'ads', 'unknown'.\n\nReply the label by wrapping '###'. Only reply the label with wrap."
    response = get_gpt_response(prompt)
    response_message = response.choices[0].message.content.strip()
    match = re.search(r"###(.*)###", response_message)
    if match:
        label = match.group(1)
        if label not in ["newsletter", "bills", "ads"]:
            return "unknown"
        return label
    else:
        raise ValueError("No match found")
