from pydantic import BaseModel, Field, field_validator

class MySettings(BaseModel):
    email: str = "your.email@mail.com"
    top_references: int = 5

    @field_validator("email")
    @classmethod
    def email_validator(cls, email):
        if "@" not in value:
            raise ValueError("Invalid email address")
        elif "your.email@mail.com" == value:
            raise ValueError("Please set your email address")

#@plugin
def settings_model():
    return MySettings