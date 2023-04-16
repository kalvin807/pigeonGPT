<h1 align="center">PigeonGPT: Automate Email Labeling with charGPT</h1>

PigeonGPT Email Labeler is a Python project that automatically labels your Gmail emails using chatGPT. The script checks for new emails every minute, labels them based on their content, and applies appropriate tags. Enjoy a well-organized inbox without lifting a finger!

## 🚀 Features

- Automatically label incoming emails in Gmail
- Utilize chatGPT to identify email content
- Auto summarising long emails

## 🛠️ Installation

### Requirements

- Python 3.11+
- Poetry

### Steps

1. Clone the repository:
   ```
   git clone https://github.com/kalvin807/pigeongpt-email-labeler.git
   ```
2. Change into the project directory:
   ```
   cd pigeongpt
   ```
3. Install dependencies with poetry
   ```
   poetry install
   ```
4. Create a `.env` file
   ```
   OPENAI_API_KEY={...open ai apikey...}
   GMAIL_CREDENTIALS_JSON={..content of token.json if you decide to host it to some PAAS (eg railway)...}
   ```
5. Prepare your gmail API auth with this guide: https://developers.google.com/gmail/api/quickstart/python
6. Put the `client_secret.json` to project root folder

## 🚀 Usage

To run the PigeonGPT Email Labeler script,run

```sh
poetry run python -m pigeongpt
```

The script will continuously check for new emails every minute and label them based on their content. It will apply tags to the emails in your Gmail account.

## ⚙️ Customization

You can customize the email labeling by modifying the `label_email()` function in `labeler.py`. Additionally, you can adjust the cooldown period between checks by changing the `COOLDOWN_SECOND` variable in `main.py`.

## 👩‍💻 Development

This project uses Poetry for dependency management and the following tools for development:

- black: Code formatter
- ruff: Linter and formatter
- pytest: Testing framework
- mypy: Static type checker

<footer><br/> <em>Readme.md by kalvin807 + gpt-4 </em></footer>
