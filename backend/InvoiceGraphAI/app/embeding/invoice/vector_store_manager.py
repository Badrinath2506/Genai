import os
import logging
import requests
from langchain_community.embeddings import HuggingFaceEmbeddings # type: ignore
from langchain_community.vectorstores import FAISS


class VectorStoreManager:
    def __init__(self, embedding_model_name="sentence-transformers/all-MiniLM-L6-v2", model_name="llama2", api_url="http://localhost:11434/api/generate"):
        self.embedding_model_name = embedding_model_name
        self.embeddings = HuggingFaceEmbeddings(model_name=self.embedding_model_name)
        self.vector_store = None
        self.model_name = model_name
        self.api_url = api_url
        self.logger = logging.getLogger(__name__)

    def create_vector_store(self, texts):
        self.vector_store = FAISS.from_documents(texts, self.embeddings)

    def load_vector_store(self, vector_store_path):
        self.vector_store = FAISS.load_local(
            vector_store_path,
            self.embeddings,
            allow_dangerous_deserialization=True
        )

    def save_vector_store(self, save_path):
        if self.vector_store is None:
            raise ValueError("No vector store available. Please process data first.")
        self.vector_store.save_local(save_path)

    def add_documents_to_vector_store(self, texts):
        if self.vector_store is None:
            raise ValueError("No vector store available. Please create or load a vector store first.")
        self.vector_store.add_documents(texts)

    def query_vector_store(self, query, k=100):
        if self.vector_store is None:
            raise ValueError("Vector store not loaded. Please process data first.")
        return self.vector_store.similarity_search(query, k=k)
    
    
    def query_vector_store_with_llama2(self, query, k=100):
        if self.vector_store is None:
            raise ValueError("Vector store not loaded. Please process data first.")
        
        # Perform similarity search
        results = self.vector_store.similarity_search(query, k=k)
        
        # Prepare the input for the API
        input_text = " ".join([result.page_content for result in results])
        # Truncate input text if too long
        max_input_length = 500  # Adjust as needed
        if len(input_text) > max_input_length:
            input_text = input_text[:max_input_length]
        
        payload = {
            "model": self.model_name,
            "input": input_text,
            "max_tokens": 150
        }
        
        # Send request to the API
        self.logger.info(f"Sending request to API with payload: {payload}")
        response = requests.post(self.api_url, json=payload)
        self.logger.info(f"API response status code: {response.status_code}")
        self.logger.info(f"API response text: {response.text}")
        
        if response.status_code == 200:
            response_json = response.json()
            generated_text = response_json.get("generated_text", "")
            if not generated_text:
                self.logger.warning("API returned an empty response.")
                return {"error": "The API returned an empty response. Please try again with a different query."}
            return {"generated_text": generated_text}
        else:
            raise RuntimeError(f"API request failed with status code {response.status_code}: {response.text}")
        
        
        