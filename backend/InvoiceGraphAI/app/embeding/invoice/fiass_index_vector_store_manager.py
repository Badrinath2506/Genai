import os
import logging
import numpy as np
import faiss
import requests
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import config.config_util as configUtil

class VectorStoreManager:
    def __init__(self, embedding_model_name="sentence-transformers/all-MiniLM-L6-v2", 
                 model_name="llama2", api_url="http://localhost:11434/api/generate"):
        self.embedding_model_name = embedding_model_name
        self.embeddings = HuggingFaceEmbeddings(model_name=self.embedding_model_name)
        self.vector_store = None
        self.model_name = model_name
        self.api_url = api_url
        self.logger = logging.getLogger(__name__)

    def _get_embeddings_array(self, texts):
        """Helper method to get embeddings as numpy array"""
        if isinstance(texts[0], Document):
            texts = [t.page_content for t in texts]
        return np.array(self.embeddings.embed_documents(texts), dtype='float32')

    def create_vector_store(self, texts, index_type="flat", **index_kwargs):
        """
        Create vector store with specified index type
        
        Args:
            texts: List of documents
            index_type: One of "flat", "ivf", "hnsw", "ivfpq"
            index_kwargs: Parameters for the specific index type
        """
        embeddings_array = self._get_embeddings_array(texts)
        dimension = embeddings_array.shape[1]
        
        if index_type == "flat":
            index = faiss.IndexFlatL2(dimension)
        elif index_type == "ivf":
            nlist = index_kwargs.get("nlist", 100)
            quantizer = faiss.IndexFlatL2(dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
            index.train(embeddings_array)
        elif index_type == "hnsw":
            M = index_kwargs.get("M", 32)
            index = faiss.IndexHNSWFlat(dimension, M)
        elif index_type == "ivfpq":
            nlist = index_kwargs.get("nlist", 100)
            m = index_kwargs.get("m", 8)  # number of subquantizers
            bits = index_kwargs.get("bits", 8)
            quantizer = faiss.IndexFlatL2(dimension)
            index = faiss.IndexIVFPQ(quantizer, dimension, nlist, m, bits)
            index.train(embeddings_array)
        else:
            raise ValueError(f"Unknown index type: {index_type}")
        
        index.add(embeddings_array)
        
        # Create LangChain FAISS store properly
        self.vector_store = FAISS(
            embedding_function=self.embeddings.embed_query,
            index=index,
            docstore=self._create_docstore(texts),
            index_to_docstore_id={i: str(i) for i in range(len(texts))}
        )

    def _create_docstore(self, texts):
        """Create a docstore from texts"""
        from langchain.docstore.in_memory import InMemoryDocstore
        return InMemoryDocstore({str(i): doc for i, doc in enumerate(texts)})

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

    def query_vector_store(self, query, k=5):
        if self.vector_store is None:
            raise ValueError("Vector store not loaded. Please process data first.")
        return self.vector_store.similarity_search(query, k=k)

    def query_vector_store_with_llama2(self, query, k=5):
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

    def get_document_by_id(self, doc_id):        
        # if self.vector_store is None:
        #     raise ValueError("Vector store not loaded. Please process data first.")
        
        vector_store =self.load_vector_store(configUtil.VECTOR_DB_FIASS_FOLDER_PATH)
        
        for doc in vector_store:
            if doc.metadata[doc_id] == doc_id:
                return doc
            else:
                return None            
        
        # docstore = self.vector_store.docstore
        # document = docstore.search(doc_id)
        
        # if document:
        #     return document.page_content
        # else:
        #     raise ValueError(f"Document with ID {doc_id} not found.")
        
    
