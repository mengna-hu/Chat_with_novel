from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from dotenv import load_dotenv,find_dotenv
from langchain_chroma import Chroma
from sparkai_embedding import MySparkAIEmbeddings
from embedding import get_embedding
import os
import re
import chromadb


_ = load_dotenv(find_dotenv())

def clean_doc(content):

    # 替换
    content = content.replace("█", "").replace("/","")
    content = content.replace("●", "").replace("~","")
    content = content.replace("◆", "").replace("■","")
    content = content.replace("【","(").replace("】",")")
    content = content.replace("\ufeff","").replace("※","")

    # 去除常见的HTML标签（如果有的话）
    content = re.sub(r'<[^>]+>', '', content)

    # 处理多余的空格和换行
    content = re.sub(r'\s+', ' ', content).strip()

    # 移除颜文字
    kaomoji_pattern = r'[（][^）]*[\u3000-\u303f\uff00-\uffef][^）]*[）]'
    content = re.sub(kaomoji_pattern, '', content)

    # 在文案中可能有新文介绍，需要处理

    # 移除预收
    index = content.find("预收")
    # 如果找到了，则返回短语之前的部分；否则返回原字符串
    if index != -1:
        content = content[:index]
    
    
    # parts = re.split(r'-{2,}',content,maxsplit=1)
    # if len(parts) > 1:
    #     print(content)
    #     print(parts) 

    return content

def load_data(file_path="./novels/"):
    #  token不足了
    file_paths = ["./novels/jjwxc_novels_1_to_5.csv", "./novels/jjwxc_novels_6_to_10.csv"]
    folder_path = file_path

    # for root,dirs,files in os.walk(folder_path):
    #     for file in files:
    #         file_path = os.path.join(root, file)
    #         file_paths.append(file_path)
    
    docs = []
    for file_path in file_paths:
        loader = CSVLoader(file_path)
        docs.extend(loader.load())
    # loader = CSVLoader("./novels/jjwxc_novels_1_to_5.csv")
    # docs = loader.load()[:100]
    for doc in docs:
        doc.page_content = clean_doc(doc.page_content)
        
    return docs

class EnhancedNovelChunker:
    def __init__(self, chunk_size, chunk_overlap):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 递归字符分类器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = chunk_size,
            chunk_overlap = chunk_overlap,
            separators=["\n\n", "\n","！", "？",  "。", "...", '，'],
            length_function = len,
            is_separator_regex=False
        )

    def _build_enhanced_content(self, chunk, before, index, num_chunk):
        basic_info = "本片段来自"+before

        chunk_pos = f"[片段{index+1}/{num_chunk}]"

        enhanced_content = f"{chunk_pos}{basic_info}文案: {chunk}"
        
        return enhanced_content
    
    def  _build_enhanced_metadata(self, metadata, index, num_chunk):
        metadata["chunk_index"] = index
        metadata["total_chunks"] = num_chunk
        return metadata
    
    def get_chunks(self, docs):
        all_chunks = []

        for doc in docs:
            try:
                parts = doc.page_content.split("文案: ", 1)  # 第二个参数1表示只分割一次
                if len(parts) == 2:
                    before = parts[0]  # 文案: 之前的内容
                    text = parts[1]   # 文案: 之后的内容
                else:
                    before = doc.page_content      # 如果没有找到"文案："，整个字符串作为前部分
                    text = ""     
                text_chunks = self.text_splitter.split_text(text)

                for i,text_chunk in enumerate(text_chunks):
                    enhanced_content = self._build_enhanced_content(text_chunk, before, i, len(text_chunks))

                    enhanced_metadata = self._build_enhanced_metadata(doc.metadata, i, len(text_chunks))

                    enhanced_doc = Document(
                        page_content = enhanced_content,
                        metadata = enhanced_metadata
                    )
                    all_chunks.append(enhanced_doc)

            except Exception as e:
                print(f"处理{doc}时出错：{str(e)}")
                continue

        return all_chunks

    
def build_dataset(chunks, persist_dir ='./vector_db/chroma', embedding='讯飞星火'):
    # 添加
    if os.path.exists(persist_dir):
        vector_db = load_db(persist_dir, embedding)
        vector_db.add_documents(chunks)
    else:
        vector_db = Chroma.from_documents(
            documents = chunks,
            embedding = get_embedding(embedding),
            persist_directory = persist_dir
        )
    return vector_db

def load_db(persist_dir = './vector_db/chroma', embedding='讯飞星火'):
    vector_db = Chroma(
        persist_directory=persist_dir,
        embedding_function=get_embedding(embedding)
    )
    # print("向量数据库中数量：", vector_db._collection.count())
    return vector_db

def search_db(input, vector_db):
    sim_docs = vector_db.similarity_search(input, 3)
    for i, doc in enumerate(sim_docs):
        print(f"检索到的第{i}个内容为：{doc}")

def build(file_path="./novels/", persist_dir='./vector_db/chroma', embedding='讯飞星火'):
    docs = load_data(file_path)

    chunker = EnhancedNovelChunker(300, 50)
    split_chunks = chunker.get_chunks(docs)
    max_length = max(len(chunk.page_content) for chunk in split_chunks)
    print(f"page_content 的最大长度为: {max_length}")
    
    vector_db = build_dataset(split_chunks, persist_dir, embedding)
    print("向量数据库中数量：", vector_db._collection.count())


if __name__ == "__main__":
    build()
    # load_db()

    