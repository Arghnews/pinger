#!/usr/bin/env python3

# pip install mailjet_rest

from datetime import datetime, timedelta
from mailjet_rest import Client
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
import textwrap
import time

# fmt: off
# credentials.json schema
"""
{
    "api_key": "xxx",
    "api_secret": "yyy",
    "from": "a@gmail.com",
    "cmd": "ping -c4 -w12 192.168.1.2",
    "addresses_to": [
        "a@hotmail.co.uk",
        "a@gmail.com"
    ]
}
"""
# fmt: on


# When next to send according to backoffs list, repeats last elem forever
class NextSendTime:
    def __init__(self, BACKOFFS, now: datetime):
        self.start = now
        self.send_exceeded_times = list(BACKOFFS)

    def should_send(self) -> bool:
        now = datetime.now()
        if now >= self.start + self.send_exceeded_times[0]:
            if len(self.send_exceeded_times) > 1:
                self.send_exceeded_times.pop(0)
            self.start = now
            return True
        return False


def send_email(
    time_now,
    api_key,
    api_secret,
    from_,
    to,
    send_immediate_test_message_and_exit,
    print_only,
):
    mailjet = Client(auth=(api_key, api_secret), version="v3.1")
    now = time_now.strftime("%a %d %b %Y, %H:%M")
    if send_immediate_test_message_and_exit:
        message_body = f"""
            This is a test message at {now}
            If you're receiving this it just means the chickenpi pinger is being tested.
            This was sent by Justin.
                """
    else:
        message_body = f"""
            PLEASE NOTE:
            The chicken coop network connection is likely BROKEN (and has been for a few hours)

            This means the chicken coop doors and food bins won't be opening/closing.

            Please go to 192.168.1.2 in an internet browser and check the website is working and you can see the buttons to open and close the doors.
            If that webpage does not load or if the buttons to open and close the doors don't appear, the chicken coop pi is not able to connect to the home network.

            Either the pi needs rebooting, or the powerlines need resyncing via a laptop.

            This is an automated email setup by Justin.
            Timestamp: {now}
                """
    data = {
        "Messages": [
            {
                "From": from_,
                "To": to,
                "Subject": "Chicken coop doors are broken",
                "TextPart": textwrap.dedent(
                    f"""
            Hi,
            {message_body}

            Cheers,
            Justin
            """
                ),
                #   "HTMLPart": "<h3>Dear passenger 1, welcome to <a href='https://www.mailjet.com/'>Mailjet</a>!</h3><br />May the delivery force be with you!",
                #   "CustomID": "AppGettingStartedTest"
            }
        ]
    }
    print(f"Would send now {time_now}")
    print(data)
    print("Message content:")
    text = data["Messages"][0]["TextPart"]
    print(f"{text}")
    if print_only:
        print("NOTE: print_only option set, so not actually sending")
    if not print_only:
        result = mailjet.send.create(data=data)
        print(result.status_code)
        print(result.json())


def loop(params):
    last_successful_ping = datetime.min
    last_failed_email_sent_time = datetime.min
    next_fail_send_timer = None
    BACKOFFS = params["backoffs"]
    print(f"Starting at {datetime.now()}")

    send_test_email_and_exit = params["send_test_email_and_exit"]
    print_only = params["print_only"]

    # Just used to know when to print, when state changes
    state = None

    now = datetime.now()

    if send_test_email_and_exit:
        print("Running send_test_email_and_exit")
        send_email(
            now,
            params["api_key"],
            params["api_secret"],
            params["from"],
            params["addresses_to"],
            send_test_email_and_exit,
            print_only,
        )
        return

    while 1:
        result = subprocess.run(
            ["bash", "-c", params["cmd"]],
            capture_output=True,
            timeout=15,
            encoding="utf8",
        )
        now = datetime.now()

        if result.returncode == 0:
            if state is not True:
                print(f"{now} Ping success")
            state = True
            last_successful_ping = now
            next_fail_send_timer = None
        else:
            if state is not False:
                print(f"{now} Now failing")
                state = False
            if next_fail_send_timer is None:
                next_fail_send_timer = NextSendTime(BACKOFFS, now)
            if next_fail_send_timer.should_send():
                print(f"{now} Sending email")
                send_email(
                    now,
                    params["api_key"],
                    params["api_secret"],
                    params["from"],
                    params["addresses_to"],
                    send_test_email_and_exit,
                    print_only,
                )

        time.sleep(1)


def validate_arg(params, credentials, param):
    try:
        params = credentials[param]
    except Exception as e:
        print(
            f"Credentials json did not contain expected parameter {param}",
            file=sys.stderr,
        )
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--print_only",
        help="Just print, don't send any email, and reduce timeouts to every few seconds",
        action="store_true",
    )
    parser.add_argument(
        "--send_test_email_and_exit",
        help="Immediately send a test email and quit",
        action="store_true",
    )
    parser.add_argument(
        "--credentials_json",
        required=True,
        help="Path to credentials json file",
        type=argparse.FileType("r", encoding="utf8"),
    )
    args = parser.parse_args()
    credentials = json.load(args.credentials_json)
    params = {}
    params["api_key"] = credentials["api_key"]
    params["api_secret"] = credentials["api_secret"]
    params["from"] = credentials["from"]
    params["addresses_to"] = credentials["addresses_to"]
    params["cmd"] = credentials["cmd"]
    params["print_only"] = args.print_only
    params["send_test_email_and_exit"] = args.send_test_email_and_exit
    assert type(params["addresses_to"]) is list
    if len(params["addresses_to"]) == 0:
        print(f"Warning: 0 'To' email addresses given", file=sys.stderr)
    # backoffs are delay from first failure to sending email, and then delay
    # thereafter to next ones, last elem repeats forever
    if params["print_only"]:
        params["backoffs"] = [timedelta(seconds=10), timedelta(seconds=20)]
    else:
        params["backoffs"] = [
            timedelta(hours=6),
            timedelta(hours=12),
            timedelta(hours=24),
        ]

    params["from"] = {"Email": params["from"], "Name": "Justin"}
    params["addresses_to"] = [{"Email": email} for email in params["addresses_to"]]

    loop(params)


if __name__ == "__main__":
    main()
