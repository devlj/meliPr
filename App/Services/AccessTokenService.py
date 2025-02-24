import os

import requests

from App.Dynamo.MeliUsers import MeliUsers


class AccessTokenService:
    def __init__(self):
        pass

    def execption401(self,meli_seller_id):
        meli_user = MeliUsers()
        user = meli_user.get_user_by_id(int(meli_seller_id))
        if user is not None:
            return self.refresh_access_token_via_api(user["refresh_token"])
        return None

    def refresh_access_token_via_api(self,refresh_token):

        url = os.environ.get("ACCESS_TOKEN_URL")
        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            'refresh_token': refresh_token
        }

        try:
            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 200:
                tokens = response.json()  # Decodifica directamente el JSON de la respuesta
                return tokens
            else:
                raise Exception(f"Failed to refresh token: {response.status_code} - {response.text}")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request Error: {e}")