from sparkai_embedding import MySparkAIEmbeddings

def get_embedding(embedding, embedding_key = None):
    if embedding == "讯飞星火":
        return MySparkAIEmbeddings()
