import os
import sys
from emailer import send_email

def main():
    to = os.getenv("REPORT_RECIPIENT", "dkushal1109@gmail.com")
    subject = "SMTP Test - stockanalysis"
    body = "This is a test email sent by the stockanalysis test_send.py script.\nIf you received this, SMTP is configured correctly."
    try:
        send_email(to, subject, body)
        print("OK: Test email sent to", to)
    except Exception as e:
        print("ERROR:", e)
        sys.exit(1)

if __name__ == '__main__':
    main()
