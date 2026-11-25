
import os
import json
import socket
import smtplib
import struct
import time
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

TARGET = "103.231.179.50"
HOSTNAME = "nrb.reabd.ru"
PORT = 123
TIMEOUT = 5

STATE_FILE = Path("state.json")
REPEAT_ALERT_SECONDS = 600

SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASS = os.environ["SMTP_PASS"]
MAIL_TO = "leshyi26@mail.ru"


def now():
    return datetime.now(timezone.utc).isoformat()


def check_ntp():
    request = bytearray(48)
    request[0] = 0x23

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(TIMEOUT)
            started = time.monotonic()
            sock.sendto(request, (TARGET, PORT))
            response, address = sock.recvfrom(512)
            elapsed = round((time.monotonic() - started) * 1000)

        if len(response) < 48:
            return False, "Invalid NTP packet"

        mode = response[0] & 0x07
        stratum = response[1]

        if mode != 4:
            return False, f"Invalid server mode: {mode}"

        if stratum == 0:
            return False, "NTP server returned Kiss-o'-Death"

        if stratum > 15:
            return False, f"Invalid stratum: {stratum}"

        return True, (
            f"Valid NTP response from {address[0]}; "
            f"Stratum {stratum}; {elapsed} ms"
        )

    except socket.timeout:
        return False, "UDP timeout: no NTP response"

    except OSError as error:
        return False, f"Network error: {error}"


def send_email(subject, body):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = MAIL_TO
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.mail.ru", 465, timeout=20) as smtp:
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(msg)

    print("EMAIL SENT:", subject)


def main():
    up, details = check_ntp()
    status = "UP" if up else "DOWN"
    timestamp = now()
    current_time = time.time()

    print("NRB EXTERNAL NTP MONITOR")
    print("Time:", timestamp)
    print("Target:", f"{HOSTNAME} ({TARGET}:{PORT}/UDP)")
    print("Status:", status)
    print("Details:", details)

    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
    else:
        state = {}

    previous = state.get("status")

    if previous is None:
        state = {
            "status": status,
            "since": timestamp,
            "last_alert": 0
        }
        print("INITIAL STATE:", status)

    elif previous != status:
        if status == "DOWN":
            subject = "[ALARM] NRB NTP SERVICE DOWN"
            body = (
                "NTP SERVICE FAILURE\n\n"
                f"Host: {HOSTNAME}\n"
                f"IP: {TARGET}\n"
                f"Port: UDP {PORT}\n"
                f"Detected: {timestamp}\n"
                f"Details: {details}\n"
            )
        else:
            subject = "[RECOVERY] NRB NTP SERVICE RESTORED"
            body = (
                "NTP SERVICE RESTORED\n\n"
                f"Host: {HOSTNAME}\n"
                f"IP: {TARGET}\n"
                f"Port: UDP {PORT}\n"
                f"Restored: {timestamp}\n"
                f"Previous failure started: {state.get('since')}\n"
                f"Details: {details}\n"
            )

        send_email(subject, body)

        state = {
            "status": status,
            "since": timestamp,
            "last_alert": current_time if not up else 0
        }

    elif not up:
        last_alert = state.get("last_alert", 0)

        if current_time - last_alert >= REPEAT_ALERT_SECONDS:
            send_email(
                "[ALARM] NRB NTP STILL DOWN",
                f"NTP is still unavailable.\n\n"
                f"Host: {HOSTNAME}\n"
                f"IP: {TARGET}\n"
                f"Port: UDP {PORT}\n"
                f"Since: {state.get('since')}\n"
                f"Checked: {timestamp}\n"
                f"Details: {details}\n"
            )
            state["last_alert"] = current_time

    STATE_FILE.write_text(
        json.dumps(state, indent=2),
        encoding="utf-8"
    )


if __name__ == "__main__":
    main()

