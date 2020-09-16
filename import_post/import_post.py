import argparse
import json
import os
import re
import sys

import requests
import markdown2
from bs4 import BeautifulSoup

from base import *

"""
Usage: import_post.py [--localhost] post

Required:
    source: path to file (JSON or Markdown) or directory

Options:
    --localhost: if provided, the localhost api is called. Otherwise, the production api is called.
"""

LOCALHOST = "http://cfsdev"
PRODUCTION_HOST = "http://cfslectura.herokuapp.com"
TOKEN_PATH = "api/user/auth-token"
IMPORT_PATH = "api/blog/posts/import"


def strip_markdown_metadata(s):
    start = s.find('---')
    end = len(s) - s[::-1].find('---')
    return s[start:end]


def strip_post_audios(s):
    start = s.find('<div class="post-audios"')
    end = len(s) - s[::-1].find('</div>')
    return s[start:end]


def post_markdown_to_dict(md_text):
    post_audios_div = strip_post_audios(md_text)
    markdown_metadata = strip_markdown_metadata(md_text)
    html = markdown2.markdown(
        markdown_metadata,
        extras=["metadata", "markdown-in-html"]
    )
    data_dict = {
        "project_name": "",
        "name": "",
        "description": "",
        "content": "",
        "post_audios": [],
    }

    if "project_name" not in html.metadata:
        raise TypeError("Missing project_name attribute in metadata.")

    data_dict["project_name"] = html.metadata["project_name"]

    if "post_name" not in html.metadata:
        raise TypeError("Missing post_name attribute in metadata.")

    data_dict["name"] = html.metadata["post_name"]

    if "post_description" in html.metadata:
        data_dict["description"] = html.metadata["post_description"]

    html = markdown2.markdown(
        post_audios_div,
        extras=["metadata", "markdown-in-html"]
    )
    post_audios = BeautifulSoup(html, "html.parser")

    if post_audios:
        for post_audio in post_audios.find_all("p", recursive=True):
            # audio title: audio file link
            audio_list = [x.strip() for x in re.split(r':(?!//)', post_audio.string)]
            data_dict["post_audios"].append(
                {
                    "name": audio_list[0],
                    "audio_url": audio_list[1]
                }
            )

    md_text = md_text.replace(markdown_metadata, '')
    md_text = md_text.replace(post_audios_div, '')
    data_dict["content"] = md_text

    return data_dict


def import_post(token, filename, import_url):
    print_color(96, filename)

    with open(filename, "r") as file:
        mimetype = get_mimetype(filename)

        if mimetype == "application/json":
            data = json.load(file)
        elif mimetype == "text/markdown":
            markdown = file.read()
            data = post_markdown_to_dict(markdown)
        else:
            sys.exit("Source file must be json or markdown.")

    headers = {"Authorization": "Bearer {0}".format(token)}
    r = requests.post(import_url, headers=headers, json=data)
    print(r.status_code)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import post json data.")
    parser.add_argument(
        "--localhost",
        help="request from Lectura localhost",
        action="store_true"
    )
    parser.add_argument("source", help="post file or directory")
    args = parser.parse_args()

    if args.localhost:
        token_url = '{0}/{1}'.format(LOCALHOST, TOKEN_PATH)
        post_import_url = '{0}/{1}'.format(LOCALHOST, IMPORT_PATH)
    else:
        token_url = '{0}/{1}'.format(PRODUCTION_HOST, TOKEN_PATH)
        post_import_url = '{0}/{1}'.format(PRODUCTION_HOST, IMPORT_PATH)

    token = get_user_auth_token(token_url)
    if token:
        if os.path.isfile(args.source):
            import_post(token, args.source, post_import_url)
        elif os.path.isdir(args.source):
            for root, dirs, files in os.walk(args.source):
                for file in files:
                    import_post(token, os.path.join(root, file), post_import_url)
    else:
        sys.exit("Invalid login.")
