import getpass
import mimetypes

import requests


def print_color(color_code, text):
    '''
    Prints in color to the console according to the integer color code.

    color codes:
        91: red
        92: green
        93: yellow
        94: light purple
        95: purple
        96: cyan
        97: light gray
        98: black
    '''
    print("\033[{0}m {1}\033[00m".format(color_code, text))


def get_mimetype(filename):
    mimetype = mimetypes.guess_type(filename)
    return mimetype[0]


def get_user_auth_token(token_url):
    # username = input("Username: ")
    # password = getpass.getpass("Password: ")

    username = "cfs"
    password = "Pizza?69p"

    r = requests.post(
        token_url,
        json={
            "username": username,
            "password": password
        }
    )
    token = r.json().get("token", None)
    return token
