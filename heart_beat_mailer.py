#!/usr/bin/env python3
import logging
import sys
import smtplib
import time
from datetime import datetime
import json


#Email Variables

try:
    with open('.email_profile.log', 'r') as f:
        email_profile = json.loads(f.read())

except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
    print('No profile found')
    print('''
            Looking for email profile, a dictionary containing following key/value pairs:
            {
                "server" : "smtp.someprovider.com",
                "port" : int_value,
                "s_name" : "some_email@domain.net",
                "s_password" : "VeryComplicatedPassword",
                "r_name" : "i_like_spam@domain.com"
            }
            Terminating now.

        ''')
    exit()

if email_profile:
    SMTP_SERVER = email_profile['server'] 
    SMTP_PORT = email_profile['port'] 
    MAIL_USERNAME = email_profile['s_name'] 
    MAIL_PASSWORD = email_profile['s_password'] 
    RECEIVER = email_profile['r_name']

class Emailer:
    def sendmail(self, recipient, subject, content):
        #Create Headers
        headers = ["From: " + MAIL_USERNAME, "Subject: " + subject, "To: " + recipient,
                   "MIME-Version: 1.0", "Content-Type: text/html"]
        headers = "\r\n".join(headers)
        #Connect to mail Server
        session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        session.ehlo()
        session.starttls()
        session.ehlo()
        #Login to mail
        session.login(MAIL_USERNAME, MAIL_PASSWORD)

        #Send Email & Exit
        session.sendmail(MAIL_USERNAME, recipient, headers + "\r\n\r\n" + content)
        session.quit


sender = Emailer()

levels = [{'title' : 'DS9 Notification ', 'content' : 'Unit 3 notifies that at '}, 
    {'title' : 'DS9 Warning ', 'content' : 'Unit 3 warns that at '}, 
    {'title' : 'DS9 Failure ', 'content' : 'Unit 3 warns that a fatal error has occurred at '}]


def notify(level=0, title='', body=''):
    sub = levels[level]['title'] + str(title)
    cont = levels[level]['content'] + str(body)
    sender.sendmail(RECEIVER, sub, cont)

#notify(0)


if __name__ == "__main__":
    notify(0, "Test", "Test mail")
    print("Mail sent")

