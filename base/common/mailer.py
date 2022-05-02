from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
import smtplib, ssl


@dataclass
class Credentials:
    username: str
    password: str

    @classmethod
    def from_credentials_file(cls, filename: Path = Path('/etc/base_mail_credentials')) -> Credentials:
        with open(filename, 'r') as credentials_file:
            content = credentials_file.readlines()
        username = password = ""
        username = cls.extract_value(content, "user")
        password = cls.extract_value(content, "password")
        return cls(
            username=username,
            password=password
        )

    @staticmethod
    def extract_value(content: List[str], key: str) -> Optional[str]:
        for line in content:
            if key in line:
                return line.split('=')[1]


class Mailer:
    def __init__(self) -> None:
        ...

    def send_summary(self) -> None:
        ...

    def login(self, server: smtplib.SMTP) -> None:
        credentials = Credentials.from_credentials_file()
        server.login(credentials.username, credentials.password)


def smtplib_trial():
    port = 465  # For SSL

    # Create a secure SSL context
    context = ssl.create_default_context()
    message = """\
    Subject: Hi there

    This message is sent from Python."""
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        m = Mailer()
        m.login(server)
        sender_email = "navi.deciv@gmail.com"
        receiver_email = "maxiwelsch@posteo.de"
        server.sendmail(from_addr=sender_email, to_addrs=receiver_email, msg=message)


if __name__ == "__main__":
    import yagmail

    receiver_email = "maxiwelsch@posteo.de"
    body = "Hello there from Yagmail"
    filename = "document.pdf"

    yag = yagmail.SMTP("navi.deciv@gmail.com")
    yag.send(
        to=receiver_email,
        subject="Yagmail test with attachment",
        contents=body,
    )
