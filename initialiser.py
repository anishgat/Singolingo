import requests
from requests_html import HTML
import models
from sqlalchemy.orm import Session
from database import SessionLocal
import time


def initialise_songs(highest_index, category, db: Session, lowest_index = 1):
    for song_index in range(lowest_index, highest_index + 1):
        url = f'https://www.filmyquotes.com/{category}/{song_index}'
        r = requests.get(url)
        if r.status_code == 200:
            html_text = r.text
            r_html = HTML(html=html_text)

            song_model = models.Song()
            song_model.title = r_html.find('h4[class="card-title"]')[0].text
            song_model.category = category
            song_model.source_reference = song_index

            hindi_lyrics = ''
            english_lyrics = ''
            
            lyrics_table = r_html.find('#lyricsSideBySideTable')
            if len(lyrics_table) == 1:
                lyrics_table = lyrics_table[0]
                rows = lyrics_table.find("tr")
                for row in rows[1:]:
                    cols = row.find("td")

                    hindi_lyrics += cols[0].text + '\n'                  # Add a \n for each line
                    english_lyrics += cols[1].text + '\n'                # Add a \n for each line
            
            song_model.hindi_lyrics = hindi_lyrics
            song_model.english_lyrics = english_lyrics

            db.add(song_model)
            db.commit()

            # writer.writerow({'id': song_index, 'name': song_title})
        
            print(f'Song {song_index} added.')


def delete_all_songs(db: Session):
    db.query(models.Song).delete()
    db.commit()


with SessionLocal() as db:
    start = time.time()
    
    # delete_all_songs(db)
    # initialise_songs(300, 'singles', db) # 541 seconds taken
    initialise_songs(4241, 'songs', db, 4212)

    end = time.time()
    print(f'Time taken: {end - start:.3f} seconds')
