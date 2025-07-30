from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from datetime import datetime
from model import TaskRequest, ClientRequest
from task import scrape_and_store

app = FastAPI()

# ---- MongoDB Connection ----
client = MongoClient("mongodb://localhost:27017/")
db = client["Walmart_data"]
task_col = db["tasks"]
product_col = db["product"]
client_col = db["clients"]

@app.post("/submit-task/")
def submit_task(task: TaskRequest):
    # Insert task data into MongoDB
    task_data = {
        "client_name": task.client_name,
        "category": task.category,
        "url": task.url,
        "status": "pending",
        "created_at": datetime.now()
    }
    result = task_col.insert_one(task_data)
    task_id = str(result.inserted_id)

    # Start scraping
    try:
        scrape_and_store(task.url, task.category, task.client_name, task_id)
        task_col.update_one({"_id": result.inserted_id}, {"$set": {"status": "completed"}})
    except Exception as e:
        task_col.update_one({"_id": result.inserted_id}, {"$set": {"status": "failed", "error": str(e)}})
        return JSONResponse(status_code=500, content={"message": "Scraping failed", "error": str(e)})

    return {"message": "✅ Task created and scraping completed", "task_id": task_id}


@app.post("/register-client/")
def register_client(client_data: ClientRequest):
    existing = client_col.find_one({"client_email": client_data.client_email})
    if existing:
        return JSONResponse(status_code=400, content={"message": "Client already registered."})

    client_doc = {
        "client_name": client_data.client_name,
        "client_email": client_data.client_email,
        "registered_at": datetime.now()
    }
    result = client_col.insert_one(client_doc)
    return {
        "message": "✅ Client registered successfully",
        "client_id": str(result.inserted_id)
    }
