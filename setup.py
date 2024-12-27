#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author:wfeng007
# @Date:2024-12-27 01:07:06
# @Last Modified by:wfeng007
#
#
#  部署发布至pip线上库；
#  作为模块发布，不包含插件部分；
#
from setuptools import setup, find_packages

setup(
    name='ananxw_jumpin',  # 包的名称
    version='0.7.0',  # 包的版本
    author='wfeng007',  # 作者
    author_email='wfeng007@163.com',  # 作者邮箱
    description='ANAN Jumpin - AI Performance Tools and Platform',  # Brief description
    long_description=open('README.md', encoding='utf-8').read(),  # 详细描述
    long_description_content_type='text/markdown',  # 描述内容类型
    url='https://github.com/wfeng007/ananxw_jumpin',  # 项目主页

    install_requires=[
        'python-dotenv==1.0.1',
        'pyyaml==6.0.2',
        'typing-extensions==4.12.2; python_version < "3.12"',
        'PySide6==6.7.2',  # GUI
        'pynput==1.7.3',  # Keyboard control
        'markdown==3.3.6',  # Markdown support
        'openai==1.42.0',  # AI/LLM related
        'langchain==0.3.0',
        'langchain-openai==0.2.2',
        'langchain-community==0.3.0',
        'langchain-chroma==0.1.4',  # for builtin plugins
        # 'chromadb==0.5.23',  # Vectordb pdf-tools
        'pymupdf==1.24.10',  # PDF tools
        'httpx==0.27.0',  # 补偿指定依赖
        # 'pyinstaller==6.11.1',  # 打包工具，需打包时安装（可选）
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    license='Apache License 2.0',  # 开源许可证
    python_requires='>=3.9',  # 
    # packages=find_packages(),  # 自动查找包
    packages=['ananxw_jumpin'],
    package_dir={'ananxw_jumpin': '.'}, #指定为当前目录为包
    py_modules=['ananxw_jumpin_allin1f', 'builtin_plugins'],  # 
    include_package_data=True,  # 如果有非 Python 文件需要包含，设置为 True 同时会检测MANIFEST.in文件？
    package_data={
        'ananxw_jumpin': [
            'requirements.txt',
            'README.md',
            'LICENSE',
            'NOTICE',
            # '_libs_ext',
            'readme_ref_res\\**',
        ],  #可以添加相应的通配符 如：'*.txt'
    },
    exclude_package_data={
        'ananxw_jumpin': ['.env','icon.png'],  # 排除 data.txt 文件
    }
)