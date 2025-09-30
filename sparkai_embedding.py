from typing import List,Optional,Any,Dict
from langchain_core.embeddings import Embeddings
from sparkai.embedding.spark_embedding import Embeddingmodel
import os
import time

class MySparkAIEmbeddings(Embeddings):

    def __init__(
            self,
            spark_embedding_app_id: Optional[str] = None,
            spark_embedding_api_key: Optional[str] = None,
            spark_embedding_api_secret: Optional[str] = None,
            spark_embedding_domian: str = "para",
            max_retries: int = 3,
            retry_delay: float = 2.0
    ):
        self.spark_embedding_app_id = spark_embedding_app_id or os.environ.get("API_ID")
        self.spark_embedding_api_key = spark_embedding_api_key or os.environ.get("API_Key")
        self.spark_embedding_api_secret = spark_embedding_api_secret or os.environ.get("API_Secret")
        self.spark_embedding_domian = spark_embedding_domian
        self.max_tries = max_retries
        self.retry_delay = retry_delay
        self.last_request_time = 0 # 上次请求时间

        if not self.spark_embedding_app_id or not self.spark_embedding_api_key or not self.spark_embedding_api_secret:
            raise ValueError("必须提供讯飞星火API的凭据")
        
        try:
            self.client = Embeddingmodel(
                spark_embedding_app_id=self.spark_embedding_app_id,
                spark_embedding_api_key=self.spark_embedding_api_key,
                spark_embedding_api_secret=self.spark_embedding_api_secret,
                spark_embedding_domain=self.spark_embedding_domian
            )
        except Exception as e:
            print(f"初始化客户端时出错：{str(e)}")
            raise
    
    def _throttle_request(self):
        # 空值请求速率，确保QPS不超过2
        current_time = time.time()
        elapsed = current_time - self.last_request_time

        if elapsed < 0.5:
            sleep_time = 0.5-elapsed
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_embedding_request_with_retry(self, text_data):
        for attemp in range(self.max_tries):
            try:
                self._throttle_request()

                embedding = self.client.embedding(text=text_data)
                return embedding
            except Exception as e:
                if attemp < self.max_tries -1:
                    print(f"尝试{attemp+1}/{self.max_tries}失败：{str(e)}；将在{self.retry_delay}后重试")
                    time.sleep(self.retry_delay)
                    self.retry_delay *= 1.1
                else:
                    raise e
                
    def embed_documents(self, texts):
        results =  []
        failed_count = 0
        for i,text in enumerate(texts):
            try:
                print(f"处理文档{i+1}/{len(texts)}")
                embedding = self._make_embedding_request_with_retry({"role":"user", "content":text})
                results.append(embedding)
            except Exception as e:
                failed_count += 1
                print(f"文件嵌入错误，索引{i}：{str(e)}")
                if results:
                    results.append([0.0]*len(results[0]))
                else:
                    if i < 3:
                        print("前几个请求均失败，可能是API问题，暂停10s后重试")
                        time.sleep(10)
                        try:
                            embedding = self._make_embedding_request_with_retry({"role":"user", "content":text})
                            results.append(embedding)
                        except Exception as retry_e:
                            print(f"重试仍失败:{str(retry_e)}")
                            results.append([0.0]*1024)
                    else:
                        results.append([0.0]*len(results[0]))
        if failed_count > 0:
            print(f"共有{failed_count}/{len(texts)}嵌入失败")
        return results
    
    def embed_query(self, text):
        try:
            original_domain = self.client.spark_embedding_domain
            self.client.spark_embedding_domain = "query"

            embedding = self._make_embedding_request_with_retry({"role":"user", "content":text})
            self.client.spark_embedding_domain = original_domain
            return embedding
        except Exception as e:
            print(f"查询嵌入失败：{str(e)}")
            raise
