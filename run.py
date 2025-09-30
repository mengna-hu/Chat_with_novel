import gradio as gr
from QA_chain import Chat_QA_no_context,Chat_QA_with_context
from dotenv import load_dotenv,find_dotenv
from css import design_css

_ = load_dotenv(find_dotenv())

LLM_DICT = {
    "讯飞星火 MAX":"Spark-max",
    "讯飞星火 Ultra":"Spark-Ultra",
    "智谱":"Chatglm-4.5",
    "通义千问":"Qwen-plus",
    "文心一言":"ernie-speed"
}
LLM_LIST = list(LLM_DICT.keys()) # 包含所有模型的扁平列表
INIT_LLM = "文心一言"

EMBEDDING_LIST = ["讯飞星火"]
INIT_EMBEDDING = "讯飞星火"

DEFAULT_DB_PATH = "./novels"
DEFAULT_PERSIST_PATH = "./vector_db/chroma"

def get_model_by_platform(platform):
    return LLM_DICT.get(platform, "")

class Model_center():
    def __init__(self):
        self.chat_with_context = {}
        self.chat_no_context = {}
    
    def chat_with_context_answer(self, question, chat_history, model="generalv3.5", embedding="讯飞星火", temperature=0.01, top_k=4, history_len=10, file_path=DEFAULT_DB_PATH, persist_dir=DEFAULT_PERSIST_PATH):
        if question==None or len(question) < 1:
            return "",chat_history
        
        try:
            if (model, embedding) not in self.chat_with_context:
                if len(chat_history) > 0:
                    chat_history = [tuple(turn) for turn in chat_history]
                self.chat_with_context[(model, embedding)] = Chat_QA_with_context(LLM_DICT[model],temperature,top_k,chat_history,embedding, history_len, persist_dir,file_path)
            chain = self.chat_with_context[(model, embedding)]
            chat_history = chain.get_answer(question)
            return  "",chat_history
        
        except Exception as e:
            chat_history.append((question,e))
            return "",chat_history
    
    def clear_history(self):
        if len(self.chat_with_context) > 0:
            for chain in self.chat_with_context.values():
                chain.clear_history()


def format_chat_prompt(message, chat_history):
    prompt = ""
    for turn in chat_history:
        user_msg, bot_msg = turn
        prompt = f"{prompt}\nUser:{user_msg}\nAssistant:{bot_msg}"
    prompt = f"{prompt}\nUser:{message}]\nAssistant:"

    return prompt

def update_text_based_on_llm(llm):
    if llm == "讯飞星火 MAX":
        return "Spark-max，旗舰级大语言模型，具备千亿级参数规模，擅长处理复杂推理链和跨领域知识融合任务"
    if llm == "讯飞星火 Ultra":
        return "Spark-Ultra，全面对标GPT-4 Turbo的通用型大语言模型，综合性能均衡且强大"
    if llm == "智谱":
        return "Chatglm-4.5，聚焦通用对话、逻辑推理与长文本生成，适合高精度的知识密集型任务"
    if llm == "通义千问":
        return "Qwen-plus，专注于强化推理任务，在数学推理、编程任务上表现强劲"
    if llm == "文心一言":
        return "ernie-speed-128k，侧重响应速度，中文理解深度高，响应速度快​"
    

model_center = Model_center()

custom_css = design_css()
block = gr.Blocks(css=custom_css)

with block as demo:
    with gr.Row(equal_height=True):
        gr.HTML("""
            <div class="title">📚 墨问---小说智能查询助手</div>
            <div class="subtitle">基于RAG LLM技术的智能小说检索与推荐系统</div>
            """)
        
    with gr.Row(elem_classes="main-content"):
        with gr.Column(scale=4):
            chatbot = gr.Chatbot(height=500, show_copy_button=True, show_share_button=True, elem_id="transparent-chatbot")
            msg = gr.Textbox(label='您好！想查询什么小说呢？', elem_id="input")
            with gr.Row():
                clear = gr.ClearButton(components=[chatbot], value="清除历史对话", elem_id="clear")

        with gr.Column(scale=1):
            with gr.Accordion("参数配置", open=True, elem_classes="accordion-container") as model_argument:
                temperature = gr.Slider(0,1,value=0.1,step=0.1,label="回答随机性", interactive=True)
                top_k = gr.Slider(1,10,value=4,step=1,label="检索返回片段数量",interactive=True)
                history_len = gr.Slider(0,100,value=10,step=10,label="保留的对话长度",interactive=True)
                
            with gr.Accordion("大模型配置", open=True) as model_select:
                llm = gr.Dropdown(
                    LLM_LIST,
                    label="大模型",
                    value=INIT_LLM,
                    interactive=True
                )
                llm_text = gr.Markdown(
                    value=update_text_based_on_llm(INIT_LLM),
                    label="模型说明",
                    elem_classes='subtitle'
                )   

            with gr.Accordion("嵌入模型配置", open=True) as embedding_select:
                embeddings = gr.Dropdown(
                    EMBEDDING_LIST, 
                    label="嵌入模型", 
                    value=INIT_EMBEDDING,
                    interactive=False)
                
                embedding_text = gr.Markdown(
                    value="注：暂无法切换嵌入模型",
                    label="模型说明",
                    elem_classes='subtitle'
                )   
        # 设置点击事件，点击时传入对应的函数
        msg.submit(model_center.chat_with_context_answer, inputs=[msg,chatbot,llm,embeddings,temperature,top_k,history_len],outputs=[msg,chatbot])
        clear.click(model_center.clear_history)
        llm.change(
            fn=update_text_based_on_llm,
            inputs=llm,
            outputs=llm_text
        )

    gr.Markdown("""
        提醒：回答由AI生成，仅供参考
        """)


gr.close_all()
demo.launch(allowed_paths=['./'])
