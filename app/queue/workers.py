from ..db.collections.files import files_collection
from bson import ObjectId
from pdf2image import convert_from_path
import os
import base64
from openai import OpenAI
from ..graph import create_graph
from ..utils.file import delete_from_drive
from dotenv import loadenv

# flake8: noqa

loadenv()
OPENAI_API_KEY = os.getenv("OPENAI_KEY")
# openai_key = os.getenv("OPENAI_KEY")

client = OpenAI(
    api_key=OPENAI_API_KEY
)

graph = create_graph()

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
    
    
async def process_file(id: str, file_path: str, description: str):
    await files_collection.update_one({"_id": ObjectId(id)}, {
        "$set": {
            "status": "processing"
        }  # ObjectId used because it expects a object not string
    })
    print("process the file with this id")
    # Step-1 convert pdf to image
    # it will convert all pages of pdf to list of images
    pages = convert_from_path(file_path)
    images = []
    
    for i, page in enumerate(pages):
        image_save_path = f"/mnt/uploads/images/{id}/image-{i}.jpg"
        os.makedirs(os.path.dirname(image_save_path), exist_ok=True)
        # error aayega folder na hua to, to phle check kra then save
        page.save(image_save_path, 'JPEG')
        images.append(image_save_path)
        
    await files_collection.update_one({"_id": ObjectId(id)}, {
        "$set": {
            "status": "successfully converted pdf to image"
        }
    })
    
    image_base64 = [encode_image(img) for img in images]
    
    # result = client.responses.create(
    #     model="gpt-5.2",
    #     input=[
    #         {
    #             "role": "user",
    #             "content": [
    #                 {"type": "input_text", "text": "You are a resume roaster, roast the given resume according to you"},
    #                 {
    #                     # flake8: noqa  isne line 81>79 wala error hata diya
    #                     "type": "input_image",
    #                     "image_url": f"data:image/jpeg;base64,{image_base64[0]}",
    #                 },
    #             ],
    #         }
    #     ],
    # )
    state = {
        "jd_text": description,
        "resume_image_b64": image_base64,
        "hr_evaluation": {}
    }
    result = graph.invoke(state)
    
    print(result["final_report"])
    await files_collection.update_one({"_id": ObjectId(id)}, {
        "$set": {
            "status": "processed",
            "result": result["final_report"]
        }
    })
    
    delete_from_drive(id)