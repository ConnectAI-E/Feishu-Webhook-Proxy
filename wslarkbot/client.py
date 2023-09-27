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

    def _validate(self, encrypt_key, message):
        if not encrypt_key or not message['headers'].get('x-lark-signature'):
            return
        timestamp = message['headers']['x-lark-request-timestamp']
        nonce = message['headers']['x-lark-request-nonce']
        signature = message['headers']['x-lark-signature']
        body = json.dumps(message['body'], separators=(',', ':')).encode()
        bytes_b = (timestamp + nonce + encrypt_key).encode("utf-8") + body
        hexdigest = hashlib.sha256(bytes_b).hexdigest()
        if signature != hexdigest:
            raise Exception('invalide signature')

    def process_message(self, message):
        # TODO validate message
        self._validate(self.encrypt_key, message)

        if 'encrypt' in message['body']:
            data = self._decrypt_data(self.encrypt_key, message['body']['encrypt'])
        else:
            data = message['body']

        if data.get('type') == 'url_verification':
            if self.verification_token and 'token' in data:
                if self.verification_token != data['token']:
                    raise Exception('invalide token')
            return self.url_verification({'body': data})
        self.on_message(data, message)

    def _decrypt_data(self, encrypt_key, encrypt_data):
        cipher = AESCipher(encrypt_key)
        return json.loads(cipher.decrypt_string(encrypt_data))

    def on_message(self, data, *args, **kwargs):
        pass


class Client(object):

    def __init__(self, *bot, bots=list(), server=WS_LARK_PROXY_SERVER, protocol=WS_LARK_PROXY_PROTOCOL):
        self.bots = list(bot) + bots
        self.bots_map = {b.app_id: b for b in self.bots}
        self.server = server
        self.protocol = protocol
        self.ws_protocol = 'wss' if protocol == 'https' else 'ws'

    def get_server_url(self, *channels, ws=False):
        return '{}://{}/sub/{}'.format(
            self.ws_protocol if ws else self.protocol,
            self.server,
            ','.join(channels)
        )

    def start(self, debug=False):
        if debug:
            websocket.enableTrace(True)
        proxy_url = self.get_server_url(*[b.app_id for b in self.bots], ws=True)
        app = websocket.WebSocketApp(proxy_url, on_message=self._on_message)
        app.run_forever()

    def _on_message(self, wsapp, message):
        message = json.loads(message)
        app_id = message['headers']['x-app-id']
        bot = self.bots_map.get(app_id)
        if bot:
            result = bot.process_message(message)
            if result:
                request_id = message['headers']['x-request-id']
                url = self.get_server_url(request_id)
                res = httpx.post(url, json=result)
                logging.debug("res %r", res.text)


if __name__ == "__main__":

    class MyBot(Bot):
        def on_message(self, data, *args, **kwargs):
            print('on_message', self.app_id, data)

    bot1 = MyBot('cli_a4593e8702c6100d', encrypt_key='e-fJKrqNbSz9NqSWL5')
    bot2 = MyBot('cli_a5993f93f3789013', encrypt_key='e-fJKrqNbSz9NqSWL5')
    client = Client(bot1, bot2)
    client.start(False)


