import logging
import azure.functions as func
import azure.durable_functions as df

async def main(event: func.EventGridEvent, starter: str):
    data = event.get_json()
    # Only handle blob‐created events
    if data.get("api") != "PutBlob":
        logging.info(f"Ignoring EventGrid event {data.get('api')}")
        return

    url       = data["url"]                  # full blob URL
    full_path = data["subject"]              # e.g. "/blobServices/default/containers/images-input/blobs/photo.jpg"
    # extract container and name
    parts     = full_path.split("/blobs/")[-1].split("/")
    container = parts[0]
    blob_name = parts[1]

    logging.info(f"[EventGridStart] New blob: container={container}, name={blob_name}")

    client = df.DurableOrchestrationClient(starter)
    await client.start_new(
        "OrchestratorFunction",
        client_input={
            "name": f"{container}/{blob_name}",
            "size": data.get("contentLength", 0),
            "uri": url
        }
    )
    logging.info(f"[EventGridStart] Orchestration started")
