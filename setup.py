from setuptools import setup
from setuptools import find_namespace_packages


VERSION = '0.0.2'

with open('README.md') as f:
    LONG_DESCRIPTION = f.read()

setup(
    name='ca-lark-websocket',  # package name
    version=VERSION,  # package version
    description='lark(feishu) client',  # package description
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    project_urls={
        "Documentation": "https://www.connectai-e.com",
        "Code": "http://github.com/connectAI-E/connectai",
        "Issue tracker": "http://github.com/connectAI-E/connectai/issues",
    },
    author="lloydzhou@gmail.com",
    license="MIT",
    keywords=["Feishu", "Lark", "Webhook", "Websocket", "Bot"],
    packages=find_namespace_packages(),
    zip_safe=False,
    install_requires=[
        "ca-lark-sdk",
        "websocket-client",
        "httpx"
    ],
    python_requires=">=3.8"
)
