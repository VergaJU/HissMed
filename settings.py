from pydantic import BaseModel, field_validator
from cat.mad_hatter.decorators import plugin

class MySettings(BaseModel):
    email: str = "your.email@mail.com"
    top_references: int = 5
    top_n_articles: int=10
    citation_weight: float=0.7
    year_weight: float=0.5
    journal_weight: float=0.9

    @field_validator("email")
    @classmethod
    def email_validator(cls, email):
        if "@" not in email:
            raise ValueError("Invalid email address")
        elif "your.email@mail.com" == email:
            raise ValueError("Please set your email address")
    
    @field_validator("top_references")
    @classmethod
    def top_references_validator(cls, top_references):
        assert isinstance(top_references, int), f"Top references is {type(top_references)}, it must be an integer"
        if top_references < 0:
            raise ValueError("Invalid top references")
        
    
    @field_validator("top_n_articles")
    @classmethod
    def top_n_articles_validator(cls, top_n_articles):
        assert isinstance(top_n_articles, int), f"Top n articles is {type(top_n_articles)}, it must be an integer"
        if top_n_articles < 0:
            raise ValueError("Invalid top n articles")
    
    @field_validator("citation_weight")
    @classmethod
    def citation_weight_validator(cls, citation_weight):
        assert isinstance(citation_weight, float), f"Citation weight is {type(citation_weight)}, it must be a float"
        if citation_weight < 0 or citation_weight > 1:
            raise ValueError("Invalid citation weight")

    @field_validator("year_weight")
    @classmethod
    def year_weight_validator(cls, year_weight):
        assert isinstance(year_weight, float), f"Year weight is {type(year_weight)}, it must be a float"
        if year_weight < 0 or year_weight > 1:
            raise ValueError("Invalid year weight")
    
    @field_validator("journal_weight")
    @classmethod
    def journal_weight_validator(cls, journal_weight):
        assert isinstance(journal_weight, float), f"Journal weight is {type(journal_weight)}, it must be a float"
        if journal_weight < 0 or journal_weight > 1:
            raise ValueError("Invalid journal weight")


@plugin
def settings_model():
    return MySettings