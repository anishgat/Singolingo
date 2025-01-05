from sqlalchemy import Column, Integer, String
from database import Base
from pydantic import BaseModel

class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    category = Column(String)          # Either songs or singles
    source_reference = Column(Integer) # The id in the filmyquotes website
    hindi_lyrics = Column(String)
    english_lyrics = Column(String)

# Pydantic model for data serialization
class SongBase(BaseModel):
    id: int
    title: str
    category: str
    source_reference: int
    hindi_lyrics: str
    english_lyrics: str

    class Config:
        orm_mode = True  # Ensure this is still included for backward compatibility
        from_attributes = True  # New configuration to support model_validate
