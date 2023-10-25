import click
from .client import *
from .message import *


@click.command()
@click.option('--app_id', prompt="APP ID", help='Your app_id')
@click.option('--app_secret', default='', prompt="APP SECRET", help='Your app_secret')
@click.option('--verification_token', default='',
              prompt="VERIFICATION TOKEN", help='Your verification_token')
@click.option('--encrypt_key', prompt="ENCRYPT KEY", help='Your encrypt_key')
@click.option('--debug', default=False, prompt="DEBUG MODE", help='debug mode')
def main(app_id, app_secret, verification_token, encrypt_key, debug):
    class MyBot(Bot):
        def on_message(self, data, *args, **kwargs):
            print('on_message', self.app_id, data)
            if 'header' in data:
                if data['header']['event_type'] == 'im.message.receive_v1' and data['event']['message']['message_type'] == 'text':
                    message_id = data['event']['message']['message_id']
                    content = json.loads(data['event']['message']['content'])
                    text = content['text']
                    # 测试回复消息，初始化bot的时候，需要配置app_secret才能发出去消息
                    self.reply_text(message_id, 'reply: ' + text)

    bot = MyBot(
        app_id,
        app_secret=app_secret,
        encrypt_key=encrypt_key,
        verification_token=verification_token
    )
    client = Client(bot)
    client.start(debug)


if __name__ == "__main__":
    main()

