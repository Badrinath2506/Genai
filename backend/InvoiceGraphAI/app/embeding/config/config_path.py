from pathlib import Path
import os

#---------------------- BASE Files FOLDER DETAILS ------------------------------------------
BASE_FOLDER_PATH = Path(r"C:\Badri\IPC\GenAIPOC\agents")

# Print the contents of the base folder
print(os.listdir(BASE_FOLDER_PATH))

#---------------------- MODEL DETAILS ------------------------------------------------------
ENCODER_MODEL_NAME = "microsoft/layoutlmv3-base"
DECODER_MODEL_NAME = "deepset/roberta-base-squad2"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

#---------------------- LOG PATHS ----------------------------------------------------------
LOG_PATH_CIRCUIT = BASE_FOLDER_PATH / "circuit_agent/logs"
LOG_PATH_CIRCUIT_LOGFILE = LOG_PATH_CIRCUIT / "circuit_agent.log"

LOG_PATH_INVOICE = BASE_FOLDER_PATH / "invoice_agent/logs"
LOG_PATH_INVOICE_LOGFILE = LOG_PATH_CIRCUIT / "invoice_agent.log"

# Ensure log directories exist
LOG_PATH_CIRCUIT.mkdir(parents=True, exist_ok=True)
LOG_PATH_INVOICE.mkdir(parents=True, exist_ok=True)

#---------------------- VECTOR DB BASE PATH ------------------------------------------------
VECTOR_DB_BASE_FOLDER_PATH = BASE_FOLDER_PATH / "vector_stores"

#---------------------- CIRCUIT PATHS ------------------------------------------------------
CIRCUIT_BASE_FOLDER_PATH = BASE_FOLDER_PATH / "circuit_agent/embedder/data"
SOURCE_RAW_FOLDER_CIRCUIT_PATH = CIRCUIT_BASE_FOLDER_PATH / "raw"
SOURCE_PROCESSED_FOLDER_CIRCUIT_PATH = CIRCUIT_BASE_FOLDER_PATH / "processed"

#---------------------- INVOICE PATHS ------------------------------------------------------
INVOICE_BASE_FOLDER_PATH = BASE_FOLDER_PATH / "invoice_agent/embedder/data"
SOURCE_RAW_FOLDER_INVOICE_PATH = INVOICE_BASE_FOLDER_PATH / "raw"
SOURCE_PROCESSED_FOLDER_INVOICE_PATH = INVOICE_BASE_FOLDER_PATH / "processed"

#---------------------- VECTOR DB PATHS ----------------------------------------------------
# Circuit Vector DB Paths
VECTOR_DB_CIRCUIT_CHROMA_FOLDER_PATH = VECTOR_DB_BASE_FOLDER_PATH / "circuit_vector_store/chroma"
VECTOR_DB_CIRCUIT_CHROMA_QUERY_FOLDER_PATH = VECTOR_DB_CIRCUIT_CHROMA_FOLDER_PATH / "chroma.sqlite3"
VECTOR_DB_CIRCUIT_FIASS_FOLDER_PATH = VECTOR_DB_BASE_FOLDER_PATH / "circuit_vector_store/fiass"

# Invoice Vector DB Paths

# C:\Badri\IPC\GenAIPOC\agents\vector_stores\invoice_vector_store\chroma\chroma.sqlite3

VECTOR_DB_INVOICE_CHROMA_FOLDER_PATH = VECTOR_DB_BASE_FOLDER_PATH / "invoice_vector_store/chroma"
VECTOR_DB_INVOICE_CHROMA_QUERY_FOLDER_PATH = VECTOR_DB_INVOICE_CHROMA_FOLDER_PATH / "chroma.sqlite3"
VECTOR_DB_INVOICE_FIASS_FOLDER_PATH = VECTOR_DB_BASE_FOLDER_PATH / "invoice_vector_store/fiass"
