import asyncio
import functools
import typing
import ast
from asyncio import Event
from uuid import UUID

import telebot.async_telebot
import os
import json

from langchain.callbacks.base import AsyncCallbackHandler
from langchain.callbacks.human import HumanRejectedException

from models import Session, FinancialRecord
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.tools import StructuredTool
from pydantic.v1 import BaseModel, Field
from telebot import types
from langchain.agents import Tool
from langchain.prompts import PromptTemplate
from langchain.agents import load_tools, initialize_agent, AgentType

from langchain.callbacks import HumanApprovalCallbackHandler
from app_class import MessageProcessor

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class Router:

    def __init__(self, bot, user_message):
        self.bot = bot
        self.user_message = user_message
        self.result = None

    async def process(self):

        template = PromptTemplate.from_template("""system" "Ты должен проанализировать сообщение и определить является 
        ли сообщение уточнением предыдущего сообщения (запроса), оно похоже на уточнение другого сообщения или новым 
        самостоятельным сообщением. Верни True если сообщение новое или же False если сообщение - уточняющее." 
        'user message - {user_message_text}'""")

        print(f'ETO USER MESSAGE {self.user_message.text}')

        prompt = template.format(user_message_text=self.user_message.text)
        llm = ChatOpenAI(model_name="gpt-4-1106-preview", openai_api_key=OPENAI_API_KEY, temperature=0.8)
        result = llm.predict(prompt)

        print(f'ETO ANALYZE RESULT {result}')
        print(f'ETO type ANALYZE RESULT {type(result)}')

        bool_result = bool(result)
        print(f'ETO ANALYZE RESULT 2 {bool_result}')
        print(f'ETO type ANALYZE RESULT 2 {type(bool_result)}')

        # result = json.loads(result)
        #
        # print(f'ETO ANALYZE RESULT json {result}')
        # print(f'ETO type ANALYZE RESULT json {type(result)}')

        print(f'ETO USER MESSAGE {self.user_message.text}')

        self.result = bool_result

        user_id = self.user_message.from_user.id
        print(f'ETO USER_ID {user_id}')

        if self.result:
            processor = MessageProcessor(self.bot, self.user_message)
        else:
            processor = MessageProcessor.instances.get(user_id)
            if not processor:
                processor = MessageProcessor(self.bot, self.user_message)
            else:
                processor.additional_user_message = self.user_message

        print(f'ETO PROCESSOR {processor}')

        print(f'ETO USER MESSAGE {self.user_message}')

        result = await processor.process()
        print(f'ETO RESULT LOOP {result}')
        print(f'ETO TYPE {type(result)}')
