# Feishu-Webhook-Proxy

1. 将飞书webhook代理成websocket
2. 企业自建应用不用创建公网的回调地址，直接本地使用websocket客户端连上这个转发地址就可以了


# 设计
1. 使用nchan维护websocket的连接
2. 将飞书的回调消息，抽取飞书相关的头信息，外面包一层json，使用X-Request-Id作为唯一ID，推送给对应的channel，如果连接对应websocket的客户端回复了X-Request-Id对应的消息，就回复给飞书（这里主要用于第一次配置回调）
3. 客户端自己保存飞书的密钥信息，从转发服务走的消息都是加密的。
4. 客户端调用飞书其他接口，直接走自己的网络

## 安全性
1. 飞书回调消息都是加密的，只能由websocket客户端自己解密，转发服务是透明的。
2. 如何确保自己的channel不会被别人恶意使用？
  2.1. 需要引入一个帐号注册机制，每次创建应用的时候，生成一对<appid, appsecret>
  2.2. 这里使用appid作为channel，客户使用appsecret才能连上这个channel这个channel


## 实现
- [ ] 部署一个nchan（openresty版本）
- [ ] 配置一个internal的location，给内部转发飞书消息使用
- [ ] 配置一个location，作为飞书webhook转发（处理消息转发逻辑，如果是配置连接，就重定向到nchan_publisher_upstream_request等待客户端返回challenge给飞书）
- [ ] 配置一个nchan_publisher_upstream_request的location，接收客户端消息把内容返回给飞书



