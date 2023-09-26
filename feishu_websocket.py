import json
import httpx
import websocket



def on_message(wsapp, message):
    message = json.loads(message)
    print(message)
    if message['body'].get('type') == 'url_verification':
        request_id = message['headers']['x-request-id']
        challenge = message['body']['challenge']
        url = 'https://feishu.forkway.cn/sub/{}'.format(request_id)
        print('url_verification', url, challenge)
        res = httpx.post(url, json={'challenge': challenge})
        print('res', res.text)


wsapp = websocket.WebSocketApp("wss://feishu.forkway.cn/sub/cli_a4593e8702c6100d", on_message=on_message)
wsapp.run_forever()



