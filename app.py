from fastapi import FastAPI, Path, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

app = FastAPI()

# models.Base.metadata.create_all(bind=engine)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to the specific origins you want to allow
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"Hello": "World"}

@app.get("/song/{song_id}")
def get_song_lyrics(song_id: int, db: Session = Depends(get_db)):
    return db.query(models.Song).filter(models.Song.id == song_id).first()

@app.get("/get-song-id")
def getSongId(title: str, db: Session = Depends(get_db)):
    song = db.query(models.Song).filter(models.Song.title == title.title()).first()
    if song is None:
        raise HTTPException(status_code=404, detail="Song not found")
    return song

@app.get("/generate-song-autocomplete", response_model=List[models.SongBase])
def generateSongAutocomplete(search_query: str, db: Session = Depends(get_db)):
    songs = db.query(
            models.Song, 
            func.length(models.Song.title).label("length"), 
            func.instr(func.lower(search_query), func.lower(models.Song.title)).label("position")
        ).filter(
            models.Song.title.ilike(f'%{search_query}%')
        ).order_by(
            "position", 
            "length"
        ).limit(10)
    return [models.SongBase.model_validate(song[0]) for song in songs]
