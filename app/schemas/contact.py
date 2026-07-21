from pydantic import BaseModel, EmailStr, Field


class ContactCreate(BaseModel):
    """A message submitted through the public contact form."""

    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    subject: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=10, max_length=5000)
    # Honeypot: hidden field in the form; humans leave it empty, bots fill it.
    website: str = ""
