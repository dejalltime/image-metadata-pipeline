# Durable Workflow for Image Metadata Processing

A serverless pipeline that automatically extracts and stores metadata from user‑uploaded images using Azure Durable Functions, Blob Storage, and Azure SQL Database. 

---

## Demo Video

- **Project Walkthrough:** [Watch on YouTube](https://youtu.be/zQWpIJLWPZ4)

---

## Architecture Overview

```
Blob Upload (.jpg/.png/.svg)
         ⬇
[BlobTriggerFunction]            ← Blob trigger starts orchestration
         ⬇
[Durable Orchestrator]           ← Orchestrates activities
    ├─ ExtractMetadataActivity    ← Extract file name, size, dimensions, format
    └─ StoreMetadataActivity      ← Persist metadata to Azure SQL Database
```

---

## Repository Structure

```
image-metadata-pipeline/      ← Project root
├─ host.json                 ← Functions host configuration
├─ requirements.txt          ← Python dependencies
├─ local.settings.json       ← Local settings (not committed)
└─ function_app.py           ← Single-file Functions app (v2-preview model)
```

---

## Setup & Local Testing

1. **Clone the repository**
   ```bash
   git clone https://github.com/dejalltime/image-metadata-pipeline.git
   cd image-metadata-pipeline
   ```

2. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure local settings**  
   Create or update `local.settings.json`:
   ```json
   {
     "IsEncrypted": false,
     "Values": {
       "AzureWebJobsStorage": "<StorageAccountConnectionString>",
       "FUNCTIONS_WORKER_RUNTIME": "python",
       "METADATA_TABLE": "ImageMetadata",
       "SQL_SERVER_HOST": "<your_sql_server>.database.windows.net",
       "SQL_USER": "<db_user>",
       "SQL_PWD": "<db_password>",
       "SQL_DB": "<database_name>"
     }
   }
   ```

4. **Run the Functions host locally**
   ```bash
   func start
   ```

5. **Test via Storage Explorer**  
   Upload a `.jpg`, `.png`, or `.svg` to the `images-input` container and observe the console logs for each function invocation.  
   Verify that your Azure SQL `ImageMetadata` table has a new entry.

---

## Function Descriptions

- **BlobTriggerFunction**  
  Triggered on blob upload; starts the durable orchestrator.
- **OrchestratorFunction**  
  Coordinates the two activities.
- **ExtractMetadataActivity**  
  Uses Azure Storage SDK and Pillow to extract file name, size, dimensions, and format.
- **StoreMetadataActivity**  
  Inserts the metadata into an Azure SQL Database via `pymssql`.

---

## Table Schema

```sql
CREATE TABLE dbo.ImageMetadata (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    FileName NVARCHAR(260) NOT NULL,
    FileSizeKB DECIMAL(10,2) NOT NULL,
    Width INT NOT NULL,
    Height INT NOT NULL,
    Format NVARCHAR(20) NOT NULL,
    Uploaded DATETIME2 NOT NULL
);
```