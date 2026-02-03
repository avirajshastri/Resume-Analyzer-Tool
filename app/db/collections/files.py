from pydantic import Field
from typing import TypedDict, Optional
from pymongo.asynchronous.collection import AsyncCollection
from ..db import database


class FileSchema(TypedDict):
    name: str = Field(..., description="File name")
    status: str = Field(..., description="status of file")
    result: Optional[str] = Field(None, description="The result from openAI")
    job_description: str = Field(..., description="description of the job")
    # id arleady stored in MngoDB so no need to define one here


COLLECTION_NAME = "files"
files_collection: AsyncCollection = database[COLLECTION_NAME]
