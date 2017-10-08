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
while os.environ.get('USERNAME{}'.format(_index)):
    user = User(os.environ['USERNAME{}'.format(_index)], os.environ['PASSWORD{}'.format(_index)], os.environ['EMAIL{}'.format(_index)])
    users.append(user)
    _index += 1
