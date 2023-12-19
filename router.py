import asyncio
import os
import json
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.tools import StructuredTool
from langchain.prompts import PromptTemplate
from langchain.agents import load_tools, initialize_agent, AgentType
from app_class import MessageProcessor

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class Router:

    def __init__(self, bot, user_message):
        self.bot = bot
        self.user_message = user_message
        self.result = None

    async def process(self):
        llm = ChatOpenAI(model_name="gpt-4-1106-preview", openai_api_key=OPENAI_API_KEY, temperature=0.8, verbose=True)
        tools = load_tools(['llm-math'], llm=llm)

        agent = initialize_agent(
            tools + [
                StructuredTool.from_function(
                    func=self.process_message,
                    name='process_message',
                    description="""Useful to analyze users messages and return result""",
                ),
            ], llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )

        loop = asyncio.get_running_loop()

        result = await agent.arun(
            "Анализируйте каждое входящее сообщение и определяйте, является ли оно уточнением предыдущего"
            "запроса или новым самостоятельным сообщением. Если сообщение является уточнением, передайте его в уже "
            "существующий объект для дополнительной обработки. Если сообщение является новым запросом, создайте новый" 
            "объект для его обработки. Используйте контекст предыдущих сообщений для понимания связи между запросами."
            f'user message" - {self.user_message.text}'
        )

        # loop.create_task(self.bot.reply_to(self.user_message, result))
        print(result)

    def process_message(self, *args):
        """Useful to analyze users messages and return result"""

        is_new_message = self.analyze_message()
        print(f'ETO IS_NEW_MESSAGE{is_new_message}')

        # Получаем user_id из сообщения
        user_id = self.user_message.from_user.id
        print(f'ETO USER_ID {user_id}')

        if is_new_message:
            processor = MessageProcessor(self.bot, self.user_message)
        else:
            # Если это уточнение, получаем существующий экземпляр
            processor = MessageProcessor.instances.get(user_id)

            if not processor:
                # Если нет, создаем новый экземпляр
                processor = MessageProcessor(self.bot, self.user_message)
            else:
                # Если экземпляр существует, добавляем уточняющее сообщение
                processor.additional_user_message = self.user_message

        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(processor.process())
        return result

    def analyze_message(self):

        prompt_template = PromptTemplate.from_template("""system" "Ты должен проанализировать сообщение и определить 
        является ли сообщение уточнением предыдущего сообщения (запроса), оно похоже на уточнение другого сообщения или 
        новым самостоятельным сообщением. Верни true если сообщение новое и false если уточняющее." 
        'user message - {user_message_text}'""")

        prompt = prompt_template.format(user_message_text=self.user_message.text)
        llm = ChatOpenAI(model_name="gpt-4-1106-preview", openai_api_key=OPENAI_API_KEY, temperature=0.8)
        result = llm.predict(prompt)

        print(f'ETO ANALYZE RESULT {result}')
        print(f'ETO type ANALYZE RESULT {type(result)}')

        result = json.loads(result)

        self.result = result
        return result

#Новый тулс (он будет единственным) handle_analysis_result - он будет единственным для агента
#Внутри этого тулса будет эвэйт analyze_message
