import pyodbc
import json
import os
from datetime import datetime
from decimal import Decimal

# Connection string
connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=sqlmi-eu-prod-dbapp-01.704a0fbed2b5.database.windows.net;"
    "DATABASE=orion2;"
    "UID=sqladmin;"
    "PWD=sqlpower;"
)

# Connect to the database
connection = pyodbc.connect(connection_string)
cursor = connection.cursor()

# Define the folder paths
input_folder_path = r'E:\\Badri_NewVM\\deployment\\GenAIWorkSpace\\GenAIPOC\\fileRepository\\invoice_json'
output_folder_path = r'E:\Badri_NewVM\deployment\GenAIWorkSpace\GenAIPOC\genai_app\agents\circuit_agent\embedder\data\raw'
os.makedirs(output_folder_path, exist_ok=True)

# Define the attributes to extract
attributes = ['invoicenumber', 'billaccount']

# Initialize a list to hold all extracted data
all_extracted_data = []

# Iterate over each file in the input folder
for filename in os.listdir(input_folder_path):
    if filename.endswith('.json'):
        # Read the content of the file
        with open(os.path.join(input_folder_path, filename), 'r') as file:
            data = json.load(file)
        
        # Extract the required attributes
        extracted_data = [{attr: item[attr] for attr in attributes} for item in data]
        
        # Append the extracted data to the list
        all_extracted_data.extend(extracted_data)

# Function to convert datetime and decimal objects to strings
def convert_to_serializable(obj):
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

# Initialize a list to hold all SQL query results
all_sql_data = []

# Loop through each InvoiceNumber and execute the second query
for item in all_extracted_data:
    invoice_number = item['invoicenumber']
    get_data_query = f"""
    SELECT 
        i.InvoiceNumber, i.BillType, i.BillUCN, i.AccountNumber, i.AccountName, i.BillID, i.BillStartDate, i.CurrencyRate, i.Date_End,
        c.CircuitID, c.AccountID, c.CarrierCircuitTypeID, c.BandwidthID, c.Channel, c.ChannelBank, c.ChannelBank2, c.CCTTypeID_Customer,
        s.ServiceID, s.AlternateUCN, s.UCN_aCode, s.UCN_FULL, s.ProjectID, s.CompanyID_Customer, s.UCN_No
    FROM [Orion2].[dbo].[TBL_CIRCUIT] c WITH (NOLOCK)
    LEFT JOIN [Orion2].[dbo].[tbl_Service] s WITH (NOLOCK) ON c.[ServiceID] = s.[ServiceID]
    JOIN [Orion2].[dbo].[InvoiceCheck] i WITH (NOLOCK) ON s.[UCN_FULL] = i.[UCN]
    WHERE i.InvoiceNumber = '{invoice_number}'
    """
    cursor.execute(get_data_query)
    rows = cursor.fetchall()
    
    # Convert rows to a list of dictionaries
    columns = [column[0] for column in cursor.description]
    data = [dict(zip(columns, row)) for row in rows]
    
    # Convert datetime and decimal objects to strings
    for row in data:
        for key, value in row.items():
            if isinstance(value, (datetime, Decimal)):
                row[key] = convert_to_serializable(value)
    
    # Append the data to the list if it has content
    if data:
        all_sql_data.extend(data)

# Split the SQL data into chunks of 100 rows each
chunks = [all_sql_data[i:i + 100] for i in range(0, len(all_sql_data), 100)]

# Save each chunk into a separate JSON file in the output folder if it has content
for i, chunk in enumerate(chunks):
    if chunk:  # Check if chunk has data before saving to output file
        with open(os.path.join(output_folder_path, f'InvoiceData_{i+1}.json'), 'w') as outfile:
            json.dump(chunk, outfile, default=convert_to_serializable, indent=4)

print("Data queries executed and JSON files saved successfully.")

# Close the connection
cursor.close()
connection.close()
