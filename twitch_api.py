from typing import Dict
import requests
from dataclasses import dataclass

@dataclass
class User:
    login:str
    display_name:str

class TwitchApi:
    def __init__(self, client_id:str, oauth:str) -> None:
        self.client_id = client_id
        self.oauth = oauth
        self._auth_headers = {
            'Authorization': 'Bearer ' + oauth,
            'Client-Id': client_id }
    
    def check_live(self, login:str) -> bool:
        url = 'https://api.twitch.tv/helix/streams'
        resp = self._get(url, user_login=login)
        if 'data' not in resp:
            raise ValueError(f'unknown response: {resp}')
        return bool(len(resp['data']))
    
    def get_user(self, login:str) -> User:
        url = 'https://api.twitch.tv/helix/users'
        resp = self._get(url, login=login)
        if 'data' not in resp:
            raise ValueError(f'unknown response: {resp}')
        if len(resp['data']) == 0:
            raise NameError(f'Unkown user: {login}')
        user_data = resp['data'][0]
        return User(user_data['login'], user_data['display_name'])
    
    def _get(self, url, **params) -> Dict:
        resp = requests.get(url, params=params, headers=self._auth_headers)
        return resp.json()