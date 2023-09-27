from setuptools import setup
from setuptools import find_packages


VERSION = '0.1.3'

with open('README.md') as f:
    LONG_DESCRIPTION = f.read()

setup(
    name='wslarkbot',  # package name
    version=VERSION,  # package version
    description='lark(feishu) websocket client',  # package description
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
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
