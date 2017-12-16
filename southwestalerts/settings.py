import os


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

user = User(os.environ['SOUTHWEST_USERNAME'], os.environ['SOUTHWEST_PASSWORD'], os.environ['SOUTHWEST_EMAIL'])
users.append(user)
