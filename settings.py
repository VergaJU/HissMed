from pydantic import BaseModel, field_validator
from cat.mad_hatter.decorators import plugin

class MySettings(BaseModel):
    email: str = "your.email@mail.com"
    top_references: int = 5

    @field_validator("email")
    @classmethod
    def email_validator(cls, email):
        if "@" not in email:
            raise ValueError("Invalid email address")
        elif "your.email@mail.com" == email:
            raise ValueError("Please set your email address")

@plugin
def settings_model():
    return MySettings