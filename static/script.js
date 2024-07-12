var questionNumber = 0;
var chained_lyrics = [];
var tries = 0;

function zip(arrays) {
    return arrays[0].map(function(_, i) {
        return arrays.map(function(array) {
            return array[i];
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const searchPage = document.querySelector('#searchPage');
    const quizPage = document.querySelector('#quizPage');
    
    const questionText = document.querySelector('#questionText');
    const answerText = document.querySelector('#answerText');
    const nextButton = document.querySelector('#next');
    const skipButton = document.querySelector('#skip');
    const learnButton = document.querySelector('#learn');
    const learnText = document.querySelector('#learnText');
    const backButton = document.querySelector('#back');
    const songChoice = document.querySelector('#songChoice');
    const songOptions = document.querySelector('#songOptions');

    function showSearchPage() {
        searchPage.style.display = 'block';
        quizPage.style.display = 'none';
    }

    function showQuizPage() {
        searchPage.style.display = 'none';
        quizPage.style.display = 'block';
        songChoice.value = '';
        songOptions.innerHTML = '';
    }

    function makeAPIRequest(song_id) {
        fetch(`http://127.0.0.1:8000/song/${song_id}`)
        .then(response => response.json())
        .then(data => {
            const songTitle = document.querySelector('#songTitle');
            songTitle.innerHTML = data['title'];
    
            let formatted_hindi_lyrics = data['hindi_lyrics'].split('\n');
            let formatted_english_lyrics = data['english_lyrics'].split('\n');
    
            chained_lyrics = zip([formatted_hindi_lyrics, formatted_english_lyrics]);
            chained_lyrics = chained_lyrics.slice(0, -2);         // The last value of chained lyrics is a number, due to the formatting of the table on the website.
    
            questionText.value = chained_lyrics[questionNumber][0];
        })
    }

    function nextQuestion() {
        questionNumber++;
        skipButton.style.display = 'none';
        answerText.value = '';
        learnText.value = '';
        tries = 0;
        while (chained_lyrics[questionNumber][0] == '') {
            questionNumber++;
        }
        questionText.value = chained_lyrics[questionNumber][0];
        learnText.innerHTML = '';
    }

    function skipQuestion() {
        chained_lyrics.push([chained_lyrics[questionNumber][0], chained_lyrics[questionNumber][1]]);
        nextQuestion();
        // Insert toast to show correct lyrics.
    }

    showSearchPage();

    nextButton.addEventListener('click', () => {
        if (!answerText.value) {
            return alert('Please key in an answer.');
        }
        if (answerText.value.toLowerCase() !== chained_lyrics[questionNumber][1].toLowerCase()) {
            tries++;
            if (tries === 2) {
                skipButton.style.display = 'block';
            }
            return alert('Wrong answer');
        }
        if (questionNumber > chained_lyrics.length) {
            return alert('The song is completed');
        }
        nextQuestion();
    });

    answerText.addEventListener('keyup', (event) => {
        if (event.key === 'Enter') {
            nextButton.click();
        }
    });

    
    songChoice.addEventListener('keyup', (event) => {
        if (event.key === 'Enter') {
            let query = new URLSearchParams({title: songChoice.value})
            fetch(`http://127.0.0.1:8000/get-song-id?${query}`)
            .then(response => {
                if (!response.ok) {
                    if (response.status === 404) {
                        alert("Song not found");
                    } else {
                        alert("An error occurred");
                    }
                    throw new Error("Song not found");
                }
                return response.json();
            })
            .then(data => {
                var song_id = data['id'];
                showQuizPage();
                makeAPIRequest(song_id);
            })
            .catch(error => console.log(error));
        } else {
            // Make another api request that takes what is inputted by the user and find the top 10 songs in the database with the substring in the title of the song
            let search_query = new URLSearchParams({search_query: songChoice.value});
            fetch(`http://127.0.0.1:8000/generate-song-autocomplete?${search_query}`)
            .then(response => response.json())
            .then(songs => {
                songOptions.innerHTML = '';
                
                songs.forEach(song => {
                    newSong = document.createElement('a');
                    newSong.className = 'list-group-item list-group-item-action';
                    newSong.innerHTML = `
                        <div class="d-flex w-100 justify-content-between">
                            <h5 class="mb-1">${song.title}</h5>
                            <small>${song.category}</small>
                        </div>`;
                    newSong.addEventListener('click', () => {
                        showQuizPage();
                        makeAPIRequest(song.id);
                    });

                    songOptions.append(newSong)
                });
            })
        }
    });

    skipButton.addEventListener('click', skipQuestion);

    backButton.addEventListener('click', showSearchPage);

    learnButton.addEventListener('click', () => {
        learnText.innerHTML = chained_lyrics[questionNumber][1];
    });
});