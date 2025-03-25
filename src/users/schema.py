from pydantic import BaseModel, EmailStr


class UserOutput(BaseModel):
    email: EmailStr
