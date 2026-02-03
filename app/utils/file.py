import os
import aiofiles
import asyncio
import shutil


async def save_to_drive(file: bytes, path: str) -> bool:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    async with aiofiles.open(path, "wb") as open_file:
        await open_file.write(file)
        
    return True


async def delete_from_drive(file_id: str) -> bool:
    folder_path = f"/mnt/uploads/{file_id}"
    
    if os.path.exists(folder_path):
        await asyncio.to_thread(shutil.rmtree, folder_path)
    
    return True 