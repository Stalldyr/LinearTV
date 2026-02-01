//Creates form for adding/editing new series or movie
const newProgram = document.getElementById('addProgram');
newProgram.onclick = () => openProgramForm();

function openProgramForm() {
    document.getElementById('formOverlay').style.display = 'block';
    document.getElementById('programForm').style.display = 'block';
}

function closeProgramForm() {
    document.getElementById('formOverlay').style.display = 'none';
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
        document.getElementById('programRelease').value = program.year;
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

//Creates form for updating schedule

let currentTime = "";
let currentDay = "";

function openscheduleForm(day, time) {
    currentTime = time;
    currentDay = day;

    document.getElementById('formOverlay').style.display = 'block';
    document.getElementById('scheduleForm').style.display = 'block';

    const currentProgram = scheduleData.find(e => e.start_time === time && e.day_of_week === day);

    if (currentProgram) {
        const programSelect = document.getElementById('scheduleTitleSelect');
        programSelect.value = currentProgram.name;
        document.getElementById('isRerun').checked = currentProgram.is_rerun;
        updateDurationLabel();
    }
}

function closeScheduleForm() {
    document.getElementById('formOverlay').style.display = 'none';
    document.getElementById('scheduleForm').style.display = 'none';

    document.getElementById('scheduleFormData').reset();
}

function updateScheduleType() {
    document.getElementById('scheduleFormData').reset();
    const movieSelect = document.getElementById("scheduleOption1").checked;

    if (movieSelect) {
        //document.getElementById('scheduleTitleSelectLabel').innerText = 'Velg film:';
        scheduleSelect = document.getElementById('scheduleTitleSelect');
        scheduleSelect.innerHTML = `<option selected value>[Ledig]</option>`;
        movieData.forEach(m => {
            option = document.createElement('option');
            option.id = m.id;
            option.text = m.name;
            option.setAttribute('data-duration', m.duration);
            option.setAttribute('data-rerun', m.is_rerun);
            scheduleSelect.appendChild(option);
        })
        document.getElementById("rerunGroup").style.display = "none";
    } else {
        scheduleSelect = document.getElementById('scheduleTitleSelect');
        scheduleSelect.innerHTML = `<option selected value>[Ledig]</option>`;
        seriesData.forEach(m => {
            option = document.createElement('option');
            option.id = m.id;
            option.text = m.name;
            option.setAttribute('data-duration', m.duration);
            option.setAttribute('data-rerun', m.is_rerun);
            scheduleSelect.appendChild(option);
        })
        document.getElementById("rerunGroup").style.display = "block";
    }

    updateDurationLabel()
}

function updateDurationLabel() {
    const programSelect = document.getElementById('scheduleTitleSelect');
    const selectedOption = programSelect.options[programSelect.selectedIndex];

    const duration = selectedOption.getAttribute('data-duration'); //Returns error when selectiing a movie
    const durationLabel = document.getElementById('duration');

    if (duration) {
        durationLabel.textContent = `Varighet: ${duration} minutter`;
    } else {
        durationLabel.textContent = '';
    }
}

function updateScheduleTable(name, isRerun, startTime, blocks, day) {
    const allRows = document.querySelectorAll('.schedule-calendar tr');
    const rows = Array.from(allRows).slice(1);
    const rowIndex = timeSlots.indexOf(startTime);
    const colIndex = day;

    if (rowIndex >= 0 && colIndex > 0 && rowIndex < rows.length) {
        for (let i = 0; i < blocks; i++) {
            if (rowIndex + i < rows.length) {
                const cellToUpdate = rows[rowIndex + i].children[colIndex];
                cellToUpdate.textContent = name;
                if (name === "[Ledig]") {
                    cellToUpdate.className = 'empty-slot';
                } else if (isRerun) {
                    cellToUpdate.className = 'rerun-slot';
                } else {
                    cellToUpdate.className = 'original-slot';
                }
            }
        }
    }
}

//Saves schedule to database
function saveSchedule() {
    const programType = document.querySelector('input[name="scheduleType"]:checked').value;

    title = document.getElementById('scheduleTitleSelect').options[document.getElementById('scheduleTitleSelect').selectedIndex].text

    if (title == "[Ledig]"){
        alert("Need to select a program");
        return;
    }

    let series_id = null
    let movie_id = null

    if (programType == "series"){
        series_id = document.getElementById('scheduleTitleSelect').options[document.getElementById('scheduleTitleSelect').selectedIndex].getAttribute('id')
    } else {
        movie_id = document.getElementById('scheduleTitleSelect').options[document.getElementById('scheduleTitleSelect').selectedIndex].getAttribute('id')
    }
    
    const data = {
        day_of_week: currentDay,
        start_time: currentTime,
        series_id: series_id,
        movie_id: movie_id,
        name: title,
        is_rerun: document.getElementById('isRerun').checked,
        duration: parseInt(document.getElementById('scheduleTitleSelect').options[document.getElementById('scheduleTitleSelect').selectedIndex].getAttribute('data-duration'))
    };

    fetch('/admin/save_schedule', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.status === 'success') {
                updateScheduleTable(data.name, data.is_rerun, data.start_time, data.blocks, data.day_of_week);
                scheduleData.push(data);
                closeScheduleForm();
            } else {
                alert(result.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Feil ved lagring av program!');
        })
        .finally(() => {
            location.reload();
        });
    }

function deleteFromSchedule() {
    data = {
        day: currentDay,
        time: currentTime
    }

    fetch('/admin/delete_schedule', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.status === 'success') {
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
        year: document.getElementById('programRelease').value,
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

    fetch('/admin/add_program', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.status === 'success') {
                alert('Program added');
                closeProgramForm();
            } else {
                alert(result.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Feil ved lagring av program!');
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

function fetchMetaData() {
    programType = document.querySelector('input[name="programType"]:checked').value
    tmdbId = document.getElementById('programTmdbId').value
    
    if (!tmdbId) {
        alert('Please enter a TMDB ID');
        return;
    }
    
    let url =`/admin/fetch_metadata/${programType}/${tmdbId}`
    
    fetch(url)
        .then(response => response.json())
        .then(result => {
            document.getElementById('programTitle').value = result.title ? result.title : result.original_title;
            document.getElementById('programRelease').value = result.release;
            document.getElementById('programDescription').value = result.overview;
            document.getElementById('programDuration').value = result.run_time;
        });
}
