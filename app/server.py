from fastapi import FastAPI, UploadFile, Path, File, Form
from uuid import uuid4
from .utils.file import save_to_drive
from .db.collections.files import files_collection, FileSchema
from .queue.q import q
from .queue.workers import process_file
from bson import ObjectId

app = FastAPI()


@app.get("/")
def hello():
    return {"status": "healthy"}


@app.get("/{id}")
async def get_file_by_id(id: str = Path(..., description="file ID")):
    print("id->", id)
    db_file = await files_collection.find_one({"_id": ObjectId(id)})
    
    print("get id kara tab file aayi ki nai", db_file)
    return {
        "_id": str(db_file["_id"]),
        "name": db_file["name"],
        "status": db_file["status"],
        "result": db_file["result"] if "result" in db_file else None
    }


@app.post("/upload")
async def uploadFile(
    description: str = Form(..., description="Enter job description here"),
    file: UploadFile = File(...)
):
    mongoDb_file = await files_collection.insert_one(document=FileSchema(
        name=file.filename,
        job_description=description,
        status="saving in mongoDb",
    ))
    # mongoDb_file.id is object that's why convert it to string
    file_path = f"/mnt/uploads/{str(mongoDb_file.inserted_id)}/{file.filename}"
    await save_to_drive(file=await file.read(), path=file_path)
    
    # queue me save
    # flake8: noqa
    q.enqueue(process_file, str(mongoDb_file.inserted_id), file_path, description)
    # MongoDb save
    await files_collection.update_one({"_id": mongoDb_file.inserted_id}, {
        "$set": {
            "status": "queued"
        }
    })
    return {"file_id": str(mongoDb_file.inserted_id)}
