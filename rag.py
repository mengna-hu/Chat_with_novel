from QA_chain import Chat_QA_no_context, Chat_QA_with_context


def chat_no_context(question = "推荐几本都市惊悚类型小说"):
    qa_chain = Chat_QA_no_context(model='generalv3.5', temperature=0.01, top_k=5, embedding="讯飞星火")
    answer = qa_chain.get_answer(question)
    print(answer)


def chat_with_context(model):
    chat_history = []
    qa_chain = Chat_QA_with_context(model=model, temperature=0.01,top_k=5, chat_history=chat_history, embedding="讯飞星火")
    question = "可以给我推荐一部科幻小说吗"
    chat_history = qa_chain.get_answer(question)
    print(chat_history)

    qa_chain = Chat_QA_with_context(model="Spark-max", temperature=0.01,top_k=5, chat_history=chat_history, embedding="讯飞星火")
    question = "这部小说为什么这么火"
    chat_history = qa_chain.get_answer(question)
    print(chat_history)


if __name__ =="__main__":
    LLM_DICT = {
    "讯飞星火 MAX":"Spark-max",
    "讯飞星火 Ultra":"Spark-Ultra",
    "智谱":"Chatglm-4.5",
    "通义千问":"Qwen-plus",
    "文心一言":"ernie-4.5"
    }
    chat_with_context(LLM_DICT["文心一言"])
    # chat_no_context()

