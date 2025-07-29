from langchain.schema import Document
import config.config_util as configUtil  
from common_utilities.file_manager import FileManager
from data_engine.src.fiass_index_vector_store_manager import VectorStoreManager
import os
import json
import re

# python -m data_engine.src.faiss_datatrainer

class FAISSDataTrainer:
    def __init__(self, file_manager: FileManager, vector_manager: VectorStoreManager):
        # Initialize the file manager and vector manager
        self.file_manager = file_manager
        self.vector_manager = vector_manager

    def train_and_store(self, folder_path, save_path=None):
        # Set default save path if not provided
        if save_path is None:
            save_path = configUtil.VECTOR_DB_FAISS_FOLDER_PATH
        
        # Create directory if it doesn't exist
        os.makedirs(save_path, exist_ok=True)

        # Extract invoices from FileManager
        all_invoice_data = self.file_manager.process_folder()

        # Initialize count for document IDs
        count = 0
        
        # Create Document objects from invoice data
        documents = [
            Document(
                page_content="\n".join([
                    f"Invoice Number: {data['invoice_number']}",
                    f"Customer: {data['customer_name']}",
                    f"Amount: {data['invoice_amount']}",
                    f"Currency: {data['currency']}",
                    f"Date: {data['date']}",
                    f"customer id: {data['customer_id']}",
                    f"bill account: {data['bill_account']}",
                    f"bill address: {data['bill_address']}",
                    f"service address: {data['service_address']}"                  
                ]),
                metadata={
                    "file_name": data['file_name'],
                    "doc_id": count,
                    "InvoiceNumber": data['invoice_number'],
                    "Customer": data['customer_name'],
                    "Amount": data['invoice_amount'],
                    "Currency": data['currency'],
                    "Date": data['date'],
                    "customer_id": data['customer_id'],
                    "bill_account": data['bill_account'],
                    "bill_address": data['bill_address'],
                    "service_address": data['service_address']
                }
            )
            for data in all_invoice_data
        ]
        
        # Increment count for each document
        count += 1

        # Print created documents for debugging
        print(f'documents = {documents}')

        # Store documents in FAISS
        if documents:
            # Create vector store with flat index type
            # self.vector_manager.create_vector_store(documents, index_type="flat")
            # Uncomment the following lines to use different index types
            # self.vector_manager.create_vector_store(documents, index_type="ivf", nlist=100)
            self.vector_manager.create_vector_store(documents, index_type="hnsw", M=32)

            # Save the vector store to the specified path
            self.vector_manager.save_vector_store(save_path)
            print(f"✅ Successfully stored {len(documents)} documents in FAISS at: {save_path}")
            
            # Save metadata to a file
            self.save_metadata(documents, save_path)
        else:
            print("⚠️ No valid invoice data found.")

        return all_invoice_data

    def save_metadata(self, documents, save_path):
        # Extract metadata from documents
        metadata = [doc.metadata for doc in documents]
        metadata_file_path = os.path.join(save_path, "metadata.json")
        
        # Save metadata to a JSON file
        with open(metadata_file_path, 'w') as f:
            json.dump(metadata, f, indent=4)
        
        print(f"✅ Metadata saved to {metadata_file_path}")

    def clean_file(self, file_path):
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Remove non-printable characters
        cleaned_content = re.sub(r'[^\x20-\x7E]', '', content)
        
        # Save cleaned content back to file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(cleaned_content)
        
        print(f"✅ Cleaned file saved at {file_path}")

if __name__ == "__main__":
    # Initialize dependencies
    file_manager = FileManager()  
    vector_manager = VectorStoreManager()

    # Create an instance of FAISSDataTrainer
    trainer = FAISSDataTrainer(file_manager, vector_manager)

    # Define folder path where invoices are stored
    folder_path = configUtil.UPDATED_JSON_DATA_FILEPATH   
    # Run training process with custom save path
    trainer.train_and_store(folder_path, save_path=configUtil.VECTOR_DB_FIASS_FOLDER_PATH)

    