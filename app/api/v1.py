from fastapi import APIRouter, File, UploadFile
from app.services.mapper import process_file
from app.schemas.upload import UploadPayload
import os 
os.makedirs("temp", exist_ok=True)

router = APIRouter(prefix="/extract")



@router.post(
    "/file",
    tags=["Excel Extraction"],
    description="Extract various sheets from excel File",
)
async def upload_file(
    excel: UploadFile = File(...)
):
    # save the file in temp folder
    with open(f"temp/{excel.filename}", "wb") as f:
        f.write(await excel.read())
    
    # user can upload excel or csv file
    file_location = f"temp/{excel.filename}"    
    # print(standardize_columns(file_location, roster_type))
    response = process_file(file_location)
    os.remove(file_location)
    return response


