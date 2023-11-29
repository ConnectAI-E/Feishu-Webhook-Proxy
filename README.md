# Feishu-Webhook-Proxy

1. 将飞书webhook代理成websocket
2. 企业自建应用不用创建公网的回调地址，直接本地使用websocket客户端连上这个转发地址


# 设计
1. 使用nchan维护websocket的连接
2. 将飞书的回调消息，抽取飞书相关的头信息，外面包一层json，使用X-Request-Id作为唯一ID，推送给对应的channel，如果连接对应websocket的客户端回复了X-Request-Id对应的消息，就回复给飞书（这里主要用于第一次配置回调）
3. 客户端自己保存飞书的密钥信息，从转发服务走的消息都是加密的。
4. 客户端调用飞书其他接口，直接走自己的网络

## 安全性
1. 飞书回调消息都是加密的，只能由websocket客户端自己解密，转发服务是透明的。
2. 如何确保自己的channel不会被别人恶意使用？
> 使用nginx basic auth，nchan支持auth_request，在对应的request里面使用basic auth就能做校验  


## 实现
- [x] 部署一个nchan（openresty版本）
- [x] 配置一个internal的location，给内部转发飞书消息使用
- [x] 配置一个location，作为飞书webhook转发（处理消息转发逻辑，如果是配置连接，就重定向到request_id对应的channel等待客户端返回challenge给飞书）


# organization
> 使用一个organization对当前组织下面的所有bot进行管理
> 这样所有的消息可以通过`org_<name>`一个channel推送，这种模式下启动服务的时候可以不用提前注册所有的bot，可以动态的加入新的bot进去
- [x] 对org_<name>的channel增加basic auth
- [x] hook链接转发消息兼容organization
- [x] 新增一个支持organization的client

```
client = Client(bot1, bot2, org_name='org_lloyd', org_passwd='passwd')
```


# 使用

## python sdk
```
pip install wslarkbot

from wslarkbot import *

class MyBot(Bot):
    def on_message(self, data, raw_message, **kwargs):
        # 定义每一个机器人拿到消息后的处理逻辑
        print('on_message', self.app_id, data, raw_message)
        if 'header' in data:
            if data['header']['event_type'] == 'im.message.receive_v1' and data['event']['message']['message_type'] == 'text':
                message_id = data['event']['message']['message_id']
                content = json.loads(data['event']['message']['content'])
                text = content['text']
                # 测试回复消息，初始化bot的时候，需要配置app_secret才能发出去消息
                self.reply_text(message_id, 'reply: ' + text)
                # 回复卡片消息
                self.reply_card(message_id, FeishuMessageCard(
                    FeishuMessageDiv('reply'),
                    FeishuMessageHr(),
                    FeishuMessageDiv(text),
                    FeishuMessageNote(FeishuMessagePlainText('🤖'))
                ))

bot1 = MyBot('cli_xxx', app_secret='xxx', encrypt_key='xxx')
bot2 = MyBot('cli_xxx', app_secret='xxx', encrypt_key='xxx')

# 一个websocket连接，支持同时监听多个机器人回调消息
client = Client(bot1, bot2)
client.start()
```

## 集成openai
> test_openai.py文件中
1. 继承Bot增加自己处理消息的回调
```
class TextMessageBot(Bot):
    def on_message(self, data, *args, **kwargs):
        if 'header' in data:
            if data['header']['event_type'] == 'im.message.receive_v1' and data['event']['message']['message_type'] == 'text':
                content = json.loads(data['event']['message']['content'])
                if self.app:
                    return self.app.process_text_message(text=content['text'], **data['event']['message'])


```
2. 写一个应用：处理文本消息
```
class Application(object):
    def process_text_message(self, text, message_id, **kwargs):
        if text == '/help' or text == '帮助':
            self.bot.reply_card(
                message_id,
                FeishuMessageCard(
                    FeishuMessageDiv('👋 你好呀，我是一款基于OpenAI技术的智能聊天机器人'),
                    FeishuMessageHr(),
                    FeishuMessageDiv('🎒 **需要更多帮助**\n文本回复 *帮助* 或 */help*', tag='lark_md'),
                    header=FeishuMessageCardHeader('🎒需要帮助吗？'),
                )
            )
        elif text:
            chat = ChatOpenAI(
                callbacks=[OpenAICallbackHandler(self.bot, message_id)],
                **self.openai_options
            )
            system_message = [SystemMessage(content=self.system_role)] if self.system_role else []
            chat_history = []  # TODO
            messages = system_message + chat_history + [HumanMessage(content=text)]
            message = chat(messages)
            logging.debug("reply message %r", message)
        else:
            logging.warn("empty text", text)
```
3. 初始化应用，启动机器人
```
if __name__ == "__main__":
    app = Application(
        openai_api_base='',
        openai_api_key='',
        app_id='',
        app_secret='',
        encrypt_key='',
        verification_token='',
    )
    client = Client(app.bot)
    client.start(True)  # debug mode

```

### 运行示例
```
pip install wslarkbot langchain openai click
python test_openai.py
```
![image](https://github.com/ConnectAI-E/Feishu-Webhook-Proxy/assets/1826685/531c8ff5-3b46-4c15-9600-e02dae55cee2)



