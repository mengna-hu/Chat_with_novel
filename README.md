# Chat_with_novel
小说智能助手---墨问
![Uploading 截屏2025-09-30 14.39.38.png…]()

### 爬虫获取晋江小说
爬取榜单上的小说基本信息，包括：书名、作者、积分、简介、类型、文案等

### 封装嵌入函数
langchain并没有讯飞星火的嵌入封装，手动封装spark embedding

### 构造知识向量库
根据中文标点符号使用RecursiveCharacterTextSplitter进行片段划分，随后嵌入、保存到chroma向量数据库

### 基于RAG的LLM回复
主要基于langchain调用大模型api，选择了讯飞、智谱、文心一言、通义等大模型，使用gradio来实现简单的页面可视化

感谢https://github.com/logan-zou/Chat_with_Datawhale_langchain/tree/main
