# [Dingtalk-Webhook-Proxy](https://github.com/ConnectAI-E/Feishu-Webhook-Proxy/tree/dingding)

1. 将钉钉(dingtalk)webhook代理成websocket
2. 企业自建应用不用创建公网的回调地址，直接本地使用websocket客户端连上这个转发地址


# 设计
1. 使用nchan维护websocket的连接
2. 将钉钉的回调消息，抽取钉钉相关的头信息，外面包一层json，使用X-Request-Id作为唯一ID，推送给对应的channel
3. 客户端自己保存钉钉的密钥信息，从转发服务走的消息都是加密的。
4. 客户端调用钉钉其他接口，直接走自己的网络

## 安全性
1. 钉钉回调消息都是加密的，只能由websocket客户端自己解密，转发服务是透明的。
2. 如何确保自己的channel不会被别人恶意使用？
> 使用nginx basic auth，nchan支持auth_request，在对应的request里面使用basic auth就能做校验


## 实现
- [x] 部署一个nchan（openresty版本）
- [x] 配置一个internal的location，给内部转发钉钉消息使用
- [x] 配置一个location，作为钉钉webhook转发（处理消息转发逻辑，如果是配置连接，就重定向到request_id对应的channel等待客户端返回challenge给钉钉）


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
> 使用装饰器可以更简洁的通过一个回调函数处理消息
```
pip install ca-dingtalk-websocket

from connectai.dingtalk.websocket import Client

client = Client()

@client.on_bot_message(app_id='dingxxx', app_secret='xxx', agent_id='xxx', msgtype='text')
def on_message_callback1(bot, sessionwebhook, content, **kwargs):
    text = content['content']
    bot.reply(sessionWebhook, DingtalkTextMessage("reply: " + text))

client.start()
```
