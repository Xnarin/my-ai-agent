from pydantic import BaseModel


class SetupResponse(BaseModel):
    users: int
    posts: int
    comments: int
