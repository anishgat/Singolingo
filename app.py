from fastapi import FastAPI, Path, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from openai import OpenAI
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()
client = OpenAI()

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
        ).limit(50)
    return [models.SongBase.model_validate(song[0]) for song in songs]

@app.get("/check-answer")
def checkAnswer(question: str, user_answer: str, model_answer:str, db: Session = Depends(get_db)):
    prompt = f"Sentence: {question} \nModel answer: {model_answer} \nTranslation: {user_answer}"
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "you are a linguistic expert in english and hindi, and your job is to determine whether an english translation of a certain sentence in hindi is mostly accurate. As long as the english translation conveys the idea intended by the hindi sentence, it is valid. You will be provided with a model answer, and the answer is valid if the meaning of the answer closely matches the model answer. If the answer is valid, say yes, otherwise, say no. Your final response should tell me 'yes' or 'no'."},
            {"role": "user", "content": prompt}
        ]
    )
    response = completion.choices[0].message.content
    return {"response": response}
