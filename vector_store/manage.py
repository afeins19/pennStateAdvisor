
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
import pandas as pd
import csv

package__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb

class VectorStoreManager:
    def __init__(self):
        """Initialize ChromaDB with persistent storage"""
        self.client = chromadb.PersistentClient(path="./chroma_db")  # store vectors persistently
        self.collection = self.client.get_or_create_collection(name="psu_majors")

    def add_vector(self, embedding, document, metadata, doc_id):
        """Add a new vector and metadata to ChromaDB"""
        self.collection.add(
            embeddings=[embedding.tolist()],  #  numpy to list
            documents=[document],
            metadatas=[metadata], 
            ids=[doc_id]
        )

    def fromcsv(self, file_name: str):
        """Read courses from CSV generate embeddings then store in ChromaDB"""
        eg = EmbeddingGenerator()

        with open(file_name, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                if 'description' not in row or not row['description'].strip():
                    continue  # Skip rows with missing descriptions

                # make embedding from description
                embedding = eg.generate_embedding(row['description'])

                # row -> string for document storage
                documents = str(row)

                # store metadata
                metadata = {
                    "course_name": row.get("course_name", "N/A"),
                    "department_url": row.get("department_url", "N/A")
                }

                # course number is ID
                doc_id = row.get("course_number", f"course_{hash(documents)}")
                print(f"[Vectorizing] {str(doc_id)}")
                self.add_vector(embedding=embedding, document=documents, metadata=metadata, doc_id=doc_id)

        print(f"Successfully added courses from {file_name} into ChromaDB!")

    def query_vectors(self, query_embedding, n_results=3):
        """Find similar courses based on query embedding"""
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],  # numpy to list
            n_results=n_results
        )
        return results

class EmbeddingGenerator:
    def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2'):
        """Load Transformer model for embeddings"""
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)

    def generate_embedding(self, text):
        """Generate a sentence embedding"""
        inputs = self.tokenizer(text, return_tensors='pt', truncation=True, padding=True)

        with torch.no_grad():
            outputs = self.model(**inputs)

        # Use cls token 
        cls_embedding = outputs.last_hidden_state[:, 0, :]  # First token ([CLS])
        return cls_embedding.squeeze().numpy()  # to numpy

if __name__ == "__main__":
    vector_store = VectorStoreManager()
    embed_gen = EmbeddingGenerator()

    # load data from CSV and process
    csv_file = "/workspaces/pennStateAdvisor/crawler/processed_psu_courses.csv"
    vector_store.fromcsv(csv_file) # make into vector store

    # test 
    query_text = "Machine learning basics"
    query_embedding = embed_gen.generate_embedding(query_text)

    results = vector_store.query_vectors(query_embedding=query_embedding, n_results=3)

    print("\nQuery Results:")
    for metadata in results["metadatas"]:
        print(metadata)
