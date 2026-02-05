//Creates form for adding/editing new series or movie

function openProgramForm() {
    document.getElementById('overlay').style.display = 'block';
    document.getElementById('programForm').style.display = 'block';
}

function closeProgramForm() {
    document.getElementById('overlay').style.display = 'none';
    document.getElementById('programForm').style.display = 'none';

    document.getElementById('programFormData').reset();
}

function updateProgramType(){
    document.getElementById('programFormData').reset();
    const movieSelect = document.getElementById("programOption1").checked;

    if (movieSelect) {
        document.getElementById('programTitleSelectLabel').innerText = 'Velg film:';
        document.getElementById('programTitleSelect').innerHTML = `<option selected>--Ny film--</option>`;
        programSelect = document.getElementById('programTitleSelect');
        movieData.forEach(m => {
            option = document.createElement('option');
            option.id = m.id;
            option.text = m.name;
            programSelect.appendChild(option);
        }
        )

        document.getElementById('programSeasonLabel').style.display = 'none';
        document.getElementById('programSeason').style.display = 'none';
        document.getElementById('programEpisodeLabel').style.display = 'none';
        document.getElementById('programEpisode').style.display = 'none';
        document.getElementById('programIsReverseLabel').style.display = 'none';
        document.getElementById('programIsReverse').style.display = 'none';
    } else {
        document.getElementById('programTitleSelectLabel').innerText = "Velg serie:";
        document.getElementById('programTitleSelect').innerHTML = `<option selected>--Ny serie--</option>`;
        programSelect = document.getElementById('programTitleSelect');
        seriesData.forEach(m => {
            option = document.createElement('option');
            option.id = m.id;
            option.text = m.name;
            programSelect.appendChild(option);
        }
        )

        document.getElementById('programSeasonLabel').style.display = 'block';
        document.getElementById('programSeason').style.display = 'block';
        document.getElementById('programEpisodeLabel').style.display = 'block';
        document.getElementById('programEpisode').style.display = 'block';
        document.getElementById('programIsReverseLabel').style.display = 'block';
        document.getElementById('programIsReverse').style.display = 'block';
    }
}

function updateProgramForm() {
    const programSelect = document.getElementById('programTitleSelect');
    const selectedOption = programSelect.options[programSelect.selectedIndex];

    const programId = selectedOption.getAttribute('id');

    const programType = document.querySelector('input[name="programType"]:checked').value;

    let program = ""
    if (programType == "series"){
        program = seriesData.find(e => e.id == programId);
    } else {
        program = movieData.find(e => e.id == programId);
    }

    if (program) {
        document.getElementById('programTitle').value = program.name;
        document.getElementById('programUrl').value = program.source_url;
        document.getElementById('programRelease').value = program.release;
        document.getElementById('programGenre').value = program.genre;
        document.getElementById('programDescription').value = program.description;
        document.getElementById('programDuration').value = program.duration;
        document.getElementById('programTmdbId').value = program.tmdb_id;
        
        if (programType == "series"){
            document.getElementById('programSeason').value = program.season;
            document.getElementById('programEpisode').value = program.episode;
            document.getElementById('programIsReverse').checked = program.reverse_order;
        }
    } else {
        document.getElementById('programFormData').reset();
    }
}



//Saves program to database
function saveProgram() {
    const programSelect = document.getElementById('programTitleSelect');
    const selectedOption = programSelect.options[programSelect.selectedIndex];
    const programId = selectedOption.getAttribute('id');
    const programType = document.querySelector('input[name="programType"]:checked').value

    const data = {
        id: programId ? programId : null,
        program_type: programType,
        name: document.getElementById('programTitle').value,
        source_url: document.getElementById('programUrl').value,
        release: document.getElementById('programRelease').value,
        description: document.getElementById('programDescription').value,
        duration: document.getElementById('programDuration').value,
        genre: document.getElementById('programGenre').value,
        tmdb_id: document.getElementById('programTmdbId').value,
    };

    if (programType == "series") {
        Object.assign(
            data,
            {
                season: document.getElementById('programSeason').value,
                episode: document.getElementById('programEpisode').value,
                reverse_order: document.getElementById('programIsReverse').checked
            }
        )
    }

    fetch('/admin/save_program', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.status === 'success') {
                alert('Program added/edited');
                closeProgramForm();
            } else {
                alert(result.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error while saving program');
        })
}

function deleteProgram() {
    const programSelect = document.getElementById('programTitleSelect');
    const selectedOption = programSelect.options[programSelect.selectedIndex];
    
    data = {
        program_id: selectedOption.getAttribute('id'),
        program_type: document.querySelector('input[name="programType"]:checked').value
    }

    fetch('/admin/delete_program', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.status === 'success') {
                alert('Program deleted');
                closeProgramForm();
            } else {
                alert(result.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error while deleting program');
        })
        .finally(() => {
            location.reload();
        });
}

