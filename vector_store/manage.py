import chromadb
from transformers import AutoTokenizer, AutoModel
import torch
import requests

class VectorStoreManager:
    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.create_collection(name="psu_majors")

    def create_collection(self, name):
        return chromadb.create_collection(name=name)

    def add_vector(self, embedding, document, metadata, doc_id):
        # metadata for a collection
        self.collection.add(
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata],
            ids=[doc_id]
        )

    def query_vectors(self, query_embedding, n_results=3):
        # find similar vectors based on query 
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

class EmbeddingGenerator:
    def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)

    def generate_embedding(self, text):
        inputs = self.tokenizer(text, return_tensors='pt', truncation=True, padding=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # pool hidden states to create embeddings 
        embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
        return embedding


if __name__ == "__main__":
    #             # TEST CODE
    # vector_store = VectorStoreManager()
    # embed_gen = EmbeddingGenerator()

    # documents = [
    #     "Computer Science, B.S.(Abington): This program is designed to prepare students for employment as computer scientists in engineering, scientific, industrial, and business environments as software developers, programmers, and systems analysts.",
    #     "Data Sciences, B.S. (Abington):Data Sciences is a field of study concerned with developing, applying, and validating methods, processes, systems, and tools for drawing useful knowledge, justifiable conclusions, and actionable insights from large, complex and diverse data through exploration, prediction, and inference."
    # ]

    # metadata = [{"source": "psu_abington", "major_id": "CMPSC"}, {"source": "psu_abington", "major_id": "DTSAB"}]

    # for i, doc in enumerate(documents):
    #     embedding = embed_gen.generate_embedding(doc)
    #     vector_store.add_vector(embedding, doc, metadata[i], f"doc_{i}")

    # query_text = "analytics"
    # query_embedding = embed_gen.generate_embedding(query_text)

    # results = vector_store.query_vectors(query_embedding=query_embedding, n_results=1)

    # print("Query Results:")
    # for result in results["documents"]:
    #     print(result)


    # Load data
    df = pd.read_csv("psu_courses.csv")

    # Combicombinene relevant fields into a single text field for embedding
    df['text'] = df.apply(lambda row: f"{row['Course Number']} {row['Course Name']} {row['Description']} {row['Prerequisites']}", axis=1)
