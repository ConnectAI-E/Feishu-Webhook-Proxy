import base64
import json
import logging
import sys

import websocket

from connectai.dingtalk.sdk import *
from connectai.dingtalk.sdk.mixin import BotMessageDecorateMixin

WS_DINGTALK_PROXY_SERVER = "dingtalk.ai2e.cn"
WS_DINGTALK_PROXY_PROTOCOL = "https"


class Client(BotMessageDecorateMixin):
    def __init__(
        self,
        *bot,
        bots=list(),
        server=WS_DINGTALK_PROXY_SERVER,
        protocol=WS_DINGTALK_PROXY_PROTOCOL,
        org_name="",
        org_passwd="",
    ):
        self.bots = list(bot) + bots
        self.bots_map = {b.app_id: b for b in self.bots}
        self.server = server
        self.protocol = protocol
        self.ws_protocol = "wss" if protocol == "https" else "ws"
        self.org_name = org_name
        self.org_passwd = org_passwd
        self.is_org = org_name and "org_" in org_name

    def get_server_url(self, *channels):
        return "{}://{}/sub/{}".format(
            self.ws_protocol,
            self.server,
            self.org_name if self.is_org else ",".join(channels),
        )

    @property
    def header(self):
        if self.org_name and self.org_passwd:
            auth = base64.b64encode(
                f"{self.org_name}:{self.org_passwd}".encode()
            ).decode()
            return dict(Authorization=f"Basic {auth}")
        return dict()

    def start(self, debug=False):
        if debug:
            websocket.enableTrace(True)
        proxy_url = self.get_server_url(*[b.app_id for b in self.bots])
        hooks = "\n".join(
            [
                self.protocol
                + "://"
                + self.server
                + "/"
                + (self.org_name if self.is_org else "hook")
                + "/"
                + b.app_id
                for b in self.bots
            ]
        )
        print(f"hooks: \n{hooks}", file=sys.stderr)

        def run_forever(*args):
            app.run_forever()

        app = websocket.WebSocketApp(
            proxy_url,
            header=self.header,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=run_forever,
        )
        run_forever()

    def _on_message(self, wsapp, message):
        try:
            message = json.loads(message)
            if "headers" not in message:
                logging.debug("no headers in message %r", message)
                return
            app_id = message["headers"]["x-app-id"]
            bot = self.bots_map.get(app_id)
            if bot:
                result = bot.process_message(message)
                logging.debug("result %r", result)
        except Exception as e:
            logging.exception(e)

    def _on_error(self, wsapp, error):
        logging.error("error %r", error)
        if isinstance(error, KeyboardInterrupt):
            sys.exit()
