from langchain_community.llms.sparkllm import SparkLLM
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate,ChatPromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, RunnableParallel
from build_db import build,load_db
from embedding import get_embedding
from dotenv import load_dotenv,find_dotenv
import os
import re

_ = load_dotenv(find_dotenv())

def combine_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def get_vectordb(embedding="讯飞星火", persisr_dir='./vector_db/chroma', file_path='./novels/',embedding_key=None):
    if os.path.exists(persisr_dir):
        content = os.listdir(persisr_dir)
        if len(content) == 0:
            vector_db = build(file_path, persisr_dir, embedding)
    else:
        vector_db = build(file_path, persisr_dir, embedding)
    vector_db = load_db(persisr_dir, embedding)

    return vector_db

def model_to_llm(model='generalv3.5', temperature=0.01):
    if model  == "Spark-max":
        llm = SparkLLM(
            model=model,
            app_id=os.environ["API_ID"],
            api_key=os.environ["API_Key"],
            api_secret=os.environ["API_Secret"],
            temperature=temperature,
            spark_api_url="wss://spark-api.xf-yun.com/v3.5/chat",
            spark_llm_domain = "generalv3.5"
        )
    elif model == "Spark-Ultra":
        llm = SparkLLM(
            model=model,
            app_id=os.environ["API_ID"],
            api_key=os.environ["API_Key"],
            api_secret=os.environ["API_Secret"],
            temperature=temperature,
            spark_api_url="wss://spark-api.xf-yun.com/v4.0/chat",
            spark_llm_domain = "4.0Ultra"
        )
    elif model == "Chatglm-4.5":
        llm = ChatOpenAI(
            model = "glm-4.5",
            temperature = temperature,
            openai_api_key = os.environ["ZHIPUAI_API_key"],
            openai_api_base = "https://open.bigmodel.cn/api/paas/v4/"
        )
    elif model == "Qwen-plus":
        llm = ChatOpenAI(
            model = "qwen-plus",
            api_key= os.environ["QIANWEN_API_Key"],
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
    elif model == "ernie-speed":
        llm = ChatOpenAI(
            model= "ernie-speed-128k",
            api_key= os.environ["QIANFAN_API_Key"],
            base_url="https://qianfan.baidubce.com/v2"
        )
    return llm

class Chat_QA_with_context:
    def __init__(self, model, temperature, top_k, chat_history, embedding, history_len, persist_dir='./vector_db/chroma', file_path='./novels/'):
        self.model = model
        self.temperature = temperature
        self.top_k = top_k
        self.chat_history = chat_history
        self.embedding = embedding
        self.history_len = history_len
        self.persist_dir = persist_dir
        self.file_path = file_path

        self.vector_db = get_vectordb(embedding, persist_dir, file_path)
        self.retriever = self.vector_db.as_retriever(search_type="similarity", search_kwargs={"k":self.top_k})


    def clear_history(self):
        return self.chat_history.clear()

    def change_history_length(self, history_len):
        n = len(self.chat_history)
        return self.chat_history[n-history_len:n]
    
    def get_answer(self, question):
        if len(question) == 0:
            return ''
        
        self.llm =  model_to_llm(self.model, self.temperature)
        
        self.sys_prompt = """
# 角色​：你是小说推荐助手“墨问”，亲和风趣，善用生活化比喻和轻松语气交流。

# ​核心原则​：严格基于提供的上下文：{context}和历史对话：{chat_history}回答用户问题：{question}，绝不虚构信息。无匹配内容时直接说明“暂未找到相关推荐”。

#​关键能力​：
### ​精准推荐​：仅使用上下文中明确的小说名称、作者、标签进行推荐，不自行扩展类型。
### ​结构化表达​：按类型归纳小说（如“暖心治愈书单”），每本书用1-2句突出核心亮点，结合关键标签（如#温暖治愈）和表情符号（如📚）。
### ​交互策略​：
1. 模糊查询时主动追问（如“想找赛博热血还是甜宠文？”）。
2. 无结果时幽默引导（如“试试关键词‘重生’或‘赛博朋克’？”）。
3. 若历史对话显示用户不满，主动道歉并调整。

# ​话术风格​：口语化，适当使用表情符号，保持专业亲和力。开场示例：“嗨！今天想探索哪种故事？暖心治愈还是搞笑甜宠？”

# ​禁止项​：严禁虚构情节、添加上下文中未出现的细节或过度玩笑影响专业性
"""
        self.prompt = ChatPromptTemplate.from_template(self.sys_prompt)

        # 使用历史对话对当前问题进行重写
        # 使用重写后的问题进行知识库检索
        # 使用原始问题、知识片段、历史对话生成最后的回复
        self.chain = ConversationalRetrievalChain.from_llm(
            llm = self.llm,
            retriever = self.retriever,
            combine_docs_chain_kwargs = {"prompt": self.prompt},
        )
        
        answer = self.chain.invoke({"question":question, "chat_history":self.chat_history[-self.history_len:]})
        answer = answer["answer"]
        answer = re.sub(r"\\n",'<br/>', answer)

        self.chat_history.append((question,answer))

        return self.chat_history

class Chat_QA_no_context:
    def __init__(self, model, temperature, top_k, embedding, persist_dir='./vector_db/chroma', file_path='./novels/'):
        self.model = model
        self.temperature  = temperature
        self.top_k = top_k
        self.embedding = embedding
        self.persist_dir = persist_dir
        self.file_path = file_path

        self.vector_db = get_vectordb(embedding, persist_dir, file_path)
        self.retriever = self.vector_db.as_retriever(search_type="similarity", search_kwargs={"k":self.top_k})
        self.combiner = RunnableLambda(combine_docs)
        self.retrieval_chain = self.retriever | self.combiner

        prompt = """使用以下上下文来回答最后的问题。 如果你不知道答案，就说你不知道，不要试图编造答案。最多回复三句号，尽量使答案简明扼要。请你在回复的最后说"谢谢你的提问！"
                上下文：{context}；问题：{input}"""
        self.prompt = PromptTemplate(template=prompt)
        self.rag_chain = (RunnableParallel({"context":self.retrieval_chain, "input":RunnablePassthrough()})
                        | self.prompt
                        | self.model
                        | StrOutputParser())
        
    def get_answer(self, question):
        if len(question) == 0:
            return ""
        
        answer = self.rag_chain.invoke(question)
        answer = re.sub(r"\\n",'<br/>', answer)
        
        return answer