from pydantic import BaseModel

class TaskRequest(BaseModel):
    client_name: str
    category: str
    url: str

class ClientRequest(BaseModel):
    client_name: str
    client_email: str
