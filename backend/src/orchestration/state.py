from pydantic import BaseModel
from typing import List , Optional 
from lang
class Message(BaseModel):
    message : str
class Document(BaseModel):
    id: str
    content: str
    metadata: Optional[dict] = None

class State(BaseModel):
    user_id : int
    query : str
    messages : List[Message]
    documents : List[Document]
    documents_id : List[str]
    