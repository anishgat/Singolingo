import streamlit as st
from time import sleep
import requests
import re

# For switching between testing and production
HOST_URL = 'https://singolingo.onrender.com'                 # Use http://127.0.0.1:8000 to run locally

# Set the page title and layout
st.set_page_config(page_title="Singolingo", layout="centered")

# Initialize session state variables
if 'songChosen' not in st.session_state:
    st.session_state['songChosen'] = False
if 'songTitle' not in st.session_state:
    st.session_state['songTitle'] = ''
if 'chained_lyrics' not in st.session_state:
    st.session_state['chained_lyrics'] = []
if 'questionNumber' not in st.session_state:
    st.session_state['questionNumber'] = 0
if 'gameMode' not in st.session_state:
    # Game mode is 0 for playing, 1 for learning
    st.session_state['gameMode'] = 0               

def search_form():
    # Show search page if no song has been chosen
    if not st.session_state['songChosen']:
        with st.form("search_song_form"):
            st.header("Search for a song")
            song_search = st.text_input(label="Song", placeholder="Search for a song")
            song_search_submit = st.form_submit_button("Search")
            
            if song_search_submit:
                response = requests.get(f'{HOST_URL}/get-song-id', params={'title': song_search})
                if response.status_code == 200:
                    data = response.json()
                    st.session_state['songChosen'] = True
                    st.session_state['songTitle'] = data['title']
                    st.session_state['chained_lyrics'] = list(zip(re.split('\n+', data['hindi_lyrics']), re.split('\n+', data['english_lyrics'])))[0:-2]
                    st.session_state['questionNumber'] = 0
                    st.rerun(scope='app')
                
                elif response.status_code == 404:
                    st.warning(f'The song {song_search} was not found.')

@st.fragment
def quiz_form():
    # Show quiz page if a song has been chosen
    if st.session_state['songChosen']:
        with st.form("quiz_form"):
            chained_lyrics = st.session_state['chained_lyrics']
            questionNumber = st.session_state['questionNumber']
            question_text = chained_lyrics[questionNumber][0]
            model_answer = chained_lyrics[questionNumber][1]
            
            st.header(st.session_state['songTitle'])
            st.markdown(f'<p style="font-size: 1.5rem;">{question_text}<span style="font-size: 2rem;">🎵</span></p>', unsafe_allow_html=True)
            container = st.empty()
            translation = container.text_input(label='Translation', placeholder='Translate the line...', value='', label_visibility='hidden')
            
            check_button = st.form_submit_button("Next")
            learn_button = st.form_submit_button('Learn')
            reset_button = st.form_submit_button('Reset', type='primary')

            if reset_button:
                reset()
                st.rerun(scope='app')

            if learn_button:      
                container.write_stream(text_generator(model_answer))
                st.session_state['gameMode'] = 1

            if check_button:
                # Check if the user clicked the learn button
                # If the learn button was not clicked, then check the user's answer and move on to the next question
                if st.session_state['gameMode'] == 0 and translation:
                    response = requests.get(f'{HOST_URL}/check-answer', params={'question': question_text, 'user_answer': translation, 'model_answer': model_answer})
                    
                    if response.status_code == 200:
                        ai_response = response.json()
                        if ai_response['response'].lower() == 'no':
                            st.toast('Your answer is incorrect', icon='❌')
                        else:
                            if questionNumber == (len(chained_lyrics) - 1):
                                reset()
                                st.balloons()
                                st.toast('Congratulations, the song is complete!')
                                sleep(2.0)
                                st.rerun(scope='app')
                            else:
                                try:
                                    st.session_state['questionNumber'] += 1
                                    st.rerun(scope='fragment')
                                
                                except IndexError:
                                    st.toast('IndexError: list index out of range')
                                    reset()
                    else:
                        st.toast('An error occurred during the checking process')
                        st.toast(response)

                # If the learn button was clicked, then move on to the next question without checking anything
                else:
                    if questionNumber == (len(chained_lyrics) - 1):
                        reset()
                        st.balloons()
                        st.toast('Congratulations, the song is complete!')
                        sleep(2.0)
                        st.rerun(scope='app')
                    else:
                        try:
                            st.session_state['questionNumber'] += 1
                            st.rerun(scope='fragment')
                                
                        except IndexError:
                            st.toast('IndexError: list index out of range')
                            reset()

def reset():
    st.session_state['songChosen'] = False
    st.session_state['songTitle'] = ''
    st.session_state['chained_lyrics'] = []
    st.session_state['questionNumber'] = 0
    st.session_state['gameMode'] = 0

def text_generator(text):
    for word in text.split(' '):
        yield word + ' '
        sleep(0.1)

def main():
    st.title("Singolingo")
    search_form()
    quiz_form()

main()
