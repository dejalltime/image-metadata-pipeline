import os, io, logging
from datetime import datetime

import pymssql
from datetime import datetime
from PIL import Image

import azure.functions as func
import azure.durable_functions as df
from azure.storage.blob import BlobServiceClient

# 1) Instantiate a Durable Functions app (v2-preview model)
my_app = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Blob client for downloading/uploading
blob_service_client = BlobServiceClient.from_connection_string(
    os.environ["AzureWebJobsStorage"]
)

# --- 2) Blob trigger starter ---
@my_app.blob_trigger(arg_name="myblob", path="images-input/{name}", connection="AzureWebJobsStorage")
@my_app.durable_client_input(client_name="client")
async def blob_trigger(myblob: func.InputStream, client):
    logging.info(f"Blob received: {myblob.name} ({myblob.length} bytes)")
    # Start the orchestration, passing blob metadata
    await client.start_new(
        "OrchestratorFunction",
        client_input={
            "name": myblob.name,
            "size": myblob.length,
            "uri": myblob.uri
        }
    )

# --- 3) Orchestrator ---
@my_app.orchestration_trigger(context_name="context")
def OrchestratorFunction(context: df.DurableOrchestrationContext):
    info = context.get_input()
    # Extract metadata
    metadata = yield context.call_activity("ExtractMetadataActivity", info)
    # Store it
    yield context.call_activity("StoreMetadataActivity", metadata)
    return metadata

# --- 4) Activity: Extract metadata ---
@my_app.activity_trigger(input_name="input")
def ExtractMetadataActivity(input: dict) -> dict:
    # input["name"] looks like "images-input/myPhoto.jpg"
    container, blob_name = input["name"].split("/", 1)

    # Download the real blob bytes
    blob_client = blob_service_client.get_blob_client(
        container=container, blob=blob_name
    )
    raw = blob_client.download_blob().readall()

    # Now Pillow will recognize it
    img = Image.open(io.BytesIO(raw))
    w, h = img.size

    return {
        "fileName": blob_name,
        "fileSizeKB": round(input["size"] / 1024, 2),
        "width": w,
        "height": h,
        "format": img.format
    }

# --- 5) Activity: Store metadata in SQL + optional blob record ---
@my_app.activity_trigger(input_name="metadata")
def StoreMetadataActivity(metadata: dict) -> None:
    server = os.environ["SQL_SERVER_HOST"]
    user   = os.environ["SQL_USER"]
    pwd    = os.environ["SQL_PWD"]
    db     = os.environ["SQL_DB"]              

    conn = pymssql.connect(
        server   = server,
        user     = user,
        password = pwd,
        database = db,
        port     = 1433,
        login_timeout=30
    )
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO {os.getenv('METADATA_TABLE')}
          (FileName, FileSizeKB, Width, Height, Format, Uploaded)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        metadata["fileName"],
        metadata["fileSizeKB"],
        metadata["width"],
        metadata["height"],
        metadata["format"],
        datetime.utcnow()
    ))
    conn.commit()
    conn.close()