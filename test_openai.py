import logging
from wslarkbot import *
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain.callbacks.base import BaseCallbackHandler


class TextMessageBot(Bot):

    def __init__(self, app=None, *args, **kwargs):
        self.app = app
        super().__init__(*args, **kwargs)

    def on_message(self, data, *args, **kwargs):
        if 'header' in data:
            if data['header']['event_type'] == 'im.message.receive_v1' and data['event']['message']['message_type'] == 'text':
                content = json.loads(data['event']['message']['content'])
                if self.app:
                    return self.app.process_text_message(text=content['text'], **data['event']['message'])
        logging.warn("unkonw message %r", data)


class OpenAICallbackHandler(BaseCallbackHandler):
    def __init__(self, bot, message_id):
        self.bot = bot
        self.message_id = message_id
        self.result = ''
        self.send_length = 0
        self.reply_message_id = ''

    def on_llm_start(self, *args, **kwargs):
        response = self.bot.reply_card(
            self.message_id,
            FeishuMessageCard(
                FeishuMessageDiv(''),
                FeishuMessageNote(FeishuMessagePlainText('正在思考，请稍等...'))
            )
        )
        self.reply_message_id = response.json()['data']['message_id']

    def on_llm_new_token(self, token, **kwargs):
        logging.info("on_llm_new_token %r", token)
        self.result += token
        if len(self.result) - self.send_length < 25:
            return
        self.send_length = len(self.result)
        self.bot.update(
            self.reply_message_id,
            FeishuMessageCard(
                FeishuMessageDiv(self.result, tag="lark_md"),
                FeishuMessageNote(FeishuMessagePlainText('正在生成，请稍等...'))
            )
        )

    def on_llm_end(self, response, **kwargs):
        content = response.generations[0][0].text
        logging.info("on_llm_end %r", content)
        self.bot.update(
            self.reply_message_id,
            FeishuMessageCard(
                FeishuMessageDiv(content, tag="lark_md"),
                FeishuMessageNote(FeishuMessagePlainText("reply from openai.")),
            )
        )


class Application(object):

    def __init__(self, openai_api_base='', openai_api_key='', system_role='', temperature=0.7, streaming=True, **kwargs):
        self.system_role = system_role
        # self.bot.app = self
        self.bot = TextMessageBot(app=self, **kwargs)
        self.openai_options = dict(
            openai_api_base=openai_api_base,
            openai_api_key=openai_api_key,
            temperature=temperature,
            streaming=streaming,
        )
        self.chat_history = []

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
            messages = system_message + self.chat_history + [HumanMessage(content=text)]
            message = chat(messages)
            # save chat_history
            self.chat_history.append(HumanMessage(content=text))
            self.chat_history.append(message)
            logging.info("reply message %r\nchat_history %r", message, self.chat_history)
        else:
            logging.warn("empty text", text)


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
    client.start(False)  # debug mode


