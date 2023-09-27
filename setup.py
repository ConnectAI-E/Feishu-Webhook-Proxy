from setuptools import setup
from setuptools import find_packages


VERSION = '0.1.0'

setup(
    name='wslarkbot',  # package name
    version=VERSION,  # package version
    description='lark(feishu) websocket client',  # package description
    project_urls={
        "Documentation": "https://www.connectai-e.com",
        "Code": "http://github.com/connectAI-E/Feishu-Webhook-Proxy",
        "Issue tracker": "http://github.com/connectAI-E/Feishu-Webhook-Proxy/issues",
    },
    author="lloydzhou@gmail..com",
    license="BSD",
    keywords=["Feishu", "Lark", "Webhook", "Websocket", "Bot"],
    packages=find_packages(),
    zip_safe=False,
)
