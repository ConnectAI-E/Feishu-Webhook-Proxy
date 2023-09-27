import json
import logging
import httpx
import websocket
import hashlib
import base64
from Crypto.Cipher import AES
from time import time
from functools import cached_property

WS_LARK_PROXY_SERVER = 'feishu.forkway.cn'
WS_LARK_PROXY_PROTOCOL = 'https'
LARK_HOST = 'https://open.feishu.cn'


class AESCipher(object):
    def __init__(self, key):
        self.bs = AES.block_size
        self.key = hashlib.sha256(AESCipher.str_to_bytes(key)).digest()

    @staticmethod
    def str_to_bytes(data):
        u_type = type(b"".decode("utf8"))
        if isinstance(data, u_type):
            return data.encode("utf8")
        return data

    @staticmethod
    def _unpad(s):
        return s[: -ord(s[len(s) - 1 :])]

    def decrypt(self, enc):
        iv = enc[: AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size :]))

    def decrypt_string(self, enc):
        enc = base64.b64decode(enc)
        return self.decrypt(enc).decode("utf8")


class Bot(object):

    def __init__(self, app_id=None, app_secret=None, verification_token=None, encrypt_key=None, host=LARK_HOST):
        self.app_id = app_id
        self.app_secret = app_secret
        self.encrypt_key = encrypt_key
        self.verification_token = verification_token
        self.host = host

    @cached_property
    def _tenant_access_token(self):
        # https://open.feishu.cn/document/ukTMukTMukTM/ukDNz4SO0MjL5QzM/auth-v3/auth/tenant_access_token_internal
        url = f'{self.host}/open-apis/auth/v3/tenant_access_token/internal'
        result = self.post(url, json={
            'app_id': self.app_id,
            'app_secret': self.app_secret,
        }).json()
        if "tenant_access_token" not in result:
            raise Exception('get tenant_access_token error')
        return result['tenant_access_token'], result['expire'] + time()

    @property
    def tenant_access_token(self):
        token, expired = self._tenant_access_token
        if not token or expired < time():
            # retry get_tenant_access_token
            del self._tenant_access_token
            token, expired = self._tenant_access_token
        return token

    def request(self, method, url, headers=dict(), **kwargs):
        if 'tenant_access_token' not in url:
            headers['Authorization'] = 'Bearer {}'.format(self.tenant_access_token)
        return httpx.request(method, url, headers=headers, **kwargs)

    def get(self, url, **kwargs):
        return self.request('GET', url, **kwargs)

    def post(self, url, **kwargs):
        return self.request('POST', url, **kwargs)

    def url_verification(self, message):
        challenge = message['body']['challenge']
        logging.debug('url_verification %r', challenge)
        return {'challenge': challenge}

    def process_message(self, message):
        # TODO validate message
        # self._validate(self.verification_token, self.encrypt_key)

        if 'encrypt' in message['body']:
            data = self._decrypt_data(self.encrypt_key, message['body']['encrypt'])
        else:
            data = message['body']

        if data.get('type') == 'url_verification':
            return self.url_verification({'body': data})

    def _decrypt_data(self, encrypt_key, encrypt_data):
        cipher = AESCipher(encrypt_key)
        return json.loads(cipher.decrypt_string(encrypt_data))


class Client(object):

    def __init__(self, *bot_id, bot_ids=list(), server=WS_LARK_PROXY_SERVER, protocol=WS_LARK_PROXY_PROTOCOL):
        self.bot_ids = list(bot_id) + bot_ids
        self.server = server
        self.protocol = protocol
        self.ws_protocol = 'wss' if protocol == 'https' else 'ws'

    def get_server_url(self, *channels, ws=False):
        return '{}://{}/sub/{}'.format(
            self.ws_protocol if ws else self.protocol,
            self.server,
            ''.join(channels)
        )

    def start(self, debug=False):
        if debug:
            websocket.enableTrace(True)
        proxy_url = self.get_server_url(*self.bot_ids, ws=True)
        app = websocket.WebSocketApp(proxy_url, on_message=self._on_message)
        app.run_forever()

    def get_app_secret(self, app_id):
        raise NotImplementedError()

    def get_encrypt_key(self, app_id):
        raise NotImplementedError()

    def get_verification_token(self, app_id):
        raise NotImplementedError()

    def on_message(self, message, bot):
        raise NotImplementedError()

    def _on_message(self, wsapp, message):
        message = json.loads(message)

        app_id = message['headers']['x-app-id']

        bot = Bot(
            app_id,
            app_secret=self.get_app_secret(app_id),
            encrypt_key=self.get_encrypt_key(app_id),
            verification_token=self.get_verification_token(app_id),
        )
        result = bot.process_message(message)
        if result:
            request_id = message['headers']['x-request-id']
            url = self.get_server_url(request_id)
            res = httpx.post(url, json=result)
            print('res', res.text)
        # user define
        self.on_message(message, bot)


if __name__ == "__main__":

    class MyClient(Client):
        def get_app_secret(self, app_id):
            # TODO return real app_secret
            return ''
        def get_encrypt_key(self, app_id):
            return 'e-fJKrqNbSz9NqSWL5'
        def get_verification_token(self, app_id):
            return 'v-Ohw8k6KwVynNmzXX'

        def on_message(message, bot):
            print(message)

    client = MyClient('cli_a4593e8702c6100d')
    client.start(True)


