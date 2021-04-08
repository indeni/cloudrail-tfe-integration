import os

import requests

import _version


class ExternalApiClient:
    def __init__(self, api_base_url: str = None):
        if api_base_url is None:
            raise ValueError('API path is a required')
        self.api_base_url = api_base_url
        self.headers = {'X-Client': 'cli:{}'.format(_version.__version__), 'X-Handshake-Version': self.get_cli_handshake_version()}

    def get_api_base_url(self):
        return self.api_base_url

    def set_api_key(self, api_key: str):
        self.headers['X-Api-Key'] = api_key

    def unset_api_key(self):
        self.headers.pop('X-Api-Key', None)

    def set_access_token(self, access_token: str):
        self.headers['Authorization'] = 'Bearer {}'.format(access_token)

    def unset_access_token(self):
        self.headers.pop('Authorization', None)

    def get(self, path: str) -> requests.Response:
        api_url = self.api_base_url + path
        response = requests.get(api_url, headers=self.headers)
        return response

    def post(self, path: str, payload: dict = None, data=None, headers=None) -> requests.Response:
        if headers is None:
            headers = {}
        api_url = self.api_base_url + path
        if data:
            response = requests.post(api_url, data=data, headers={**headers, **self.headers})
        else:
            payload_without_nones = {key: value for key, value in payload.items() if value is not None} if payload else None
            response = requests.post(api_url, json=payload_without_nones, headers={**headers, **self.headers})
        return response

    def patch(self, path: str, payload: dict = None, data=None, headers=None) -> requests.Response:
        if headers is None:
            headers = {}
        api_url = self.api_base_url + path
        if data:
            response = requests.patch(api_url, data=data, headers={**headers, **self.headers})
        else:
            payload_without_nones = {key: value for key, value in payload.items() if value is not None} if payload else None
            response = requests.patch(api_url, json=payload_without_nones, headers={**headers, **self.headers})
        return response

    def delete(self, path: str):
        api_url = self.api_base_url + path
        response = requests.delete(api_url, headers=self.headers)
        return response

    @staticmethod
    def get_cli_handshake_version() -> str:
        path = os.path.dirname(os.path.abspath(__file__))
        with open('{}/../../cloud_rail/api/handshake_version'.format(path), 'r') as file:
            return file.readline()
