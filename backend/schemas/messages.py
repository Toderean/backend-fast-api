from pydantic import BaseModel

class MessageSendRequest(BaseModel):
    to: str
    encrypted_content: str
