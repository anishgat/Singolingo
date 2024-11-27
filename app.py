from fastapi import FastAPI, Path, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
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

@app.head("/")
def read_root_head():
    return Response(status_code=200)

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
    prompt = f"Sentence: {question} \nTranslation: {user_answer}"
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": """You will be provided with 2 sentences, one in hindi and one in english. The hindi sentence will be referred to as the question, and the english sentence will be referred to as the translation. You are a linguistic expert in english and hindi, and your job is to determine whether the english translation of the hindi sentence (question) is semantically accurate. You will break down your job into 3 steps:
                Step 1 - Translate the question to english without considering the translation given.
                Step 2 - Compare the semantic closeness of your translation to the translation given.
                Step 3 - Output "yes" if the translation given is close to your translation, otherwise output "no"

                Your final response must be restricted to "yes" or "no".

                These are some examples of translations that are semantically close to one another. and hence you should output "yes" for them.
                <example1>
                Your translation: I've gone totally crazy for you
                Given translation: I am crazy for you
                </example1>

                <example2>
                Your translation: The night is formed when we both unite
                Given translation: Together we make night
                </example2>

                <example3>
                Your translation: And I pray for your well-being all night long
                Given translation: All night I pray for your wellbeing
                </example3>
            """
            },
            {"role": "user", "content": prompt}
        ]
    )
    response = completion.choices[0].message.content
    return {"response": response}
