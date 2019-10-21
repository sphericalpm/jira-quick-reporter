import requests
from requests.auth import HTTPBasicAuth
import json

from config import CREDENTIALS_PATH


def find_accountId_for_user(username):
   with open(CREDENTIALS_PATH, 'r', encoding='utf-8') as file:
      content = file.readline()
      email, token = content.split(';')

   url = "https://spherical.atlassian.net/rest/api/3/user/bulk/migration?username={}".format(username)

   auth = HTTPBasicAuth(email, token)

   headers = {
      "Accept": "application/json"
   }

   response = requests.request(
      "GET",
      url,
      headers=headers,
      auth=auth
   )

   try:
      decode_response = json.loads(response.text)
      account_id = decode_response[0]['accountId']

      return account_id

   except json.decoder.JSONDecodeError as e:
      return "Smth went wrong. It could be wrong email or token"
      # QMessageBox.about(self.view, 'Error', e.text)  # TODO: make error hendler
