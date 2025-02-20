from app.schemas.core import CoreModel

class UploadPayload(CoreModel):
    pdf: str
    sections: str = ""
    cache: bool = True