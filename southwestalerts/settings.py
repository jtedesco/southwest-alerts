import os
import logging

class User:
    username = None
    password = None
    email = None

    def __init__(self, username, password, email):
        self.username = username
        self.password = password
        self.email = email

# Find all USERNAME# / PASSWORD# pairs and add the to the list of users to check
_index = 1
mailgun_api_key = os.environ['MAILGUN_API_KEY']
mailgun_domain = os.environ['MAILGUN_DOMAIN']

users = []
username_keys = sorted([k for k in os.environ if k.startswith('SOUTHWEST_USERNAME')])
password_keys = sorted([k for k in os.environ if k.startswith('SOUTHWEST_PASSWORD')])
assert len(username_keys) == len(password_keys), 'Could not find matching username / password pairs'

for user_key, pass_key in zip(username_keys, password_keys):
    username = os.environ[user_key]
    password = os.environ[pass_key]
    users.append(User(username, password, os.environ['EMAIL']))

print('Found %d total Southwest users to scrape: %s' % (
      len(users), ', '.join(u.username for u in users)))
