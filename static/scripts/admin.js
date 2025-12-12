const days = ['mandag', 'tirsdag', 'onsdag', 'torsdag', 'fredag', 'lørdag', 'søndag'];
const daysInt = [1, 2, 3, 4, 5, 6, 7];

let currentDay = '';
let currentTime = '';

//Creates a scheduletable
const startHour = 18;
const endHour = 23;
const timeSlots = [];
for (let i = startHour; i < endHour; i++) { 
    let timeWhole = `${i}:00`;
    timeSlots.push(timeWhole);
    let timeHalf = `${i}:30`;
    timeSlots.push(timeHalf);
}

const tableBody = document.getElementsByClassName('schedule-calendar')[0]

const thead = document.createElement('thead');
const headerRow = document.createElement('tr');
const th = document.createElement('th');
th.textContent = "Tid";
headerRow.appendChild(th);

days.forEach(day => {
    const th = document.createElement('th');
    th.textContent = day.charAt(0).toUpperCase() + day.slice(1);
    headerRow.appendChild(th);
});
thead.appendChild(headerRow);
tableBody.appendChild(thead);

const tbody = document.createElement('tbody');

timeSlots.forEach(time => {
    const row = document.createElement('tr');
    const timeCell = document.createElement('td');
    timeCell.className = 'time-slot';
    timeCell.textContent = time;
    row.appendChild(timeCell);

    daysInt.forEach(day => {
        const cell = document.createElement('td');
        cell.onclick = () => openscheduleForm(day, time);

        cell.textContent = '[Ledig]';
        cell.className = 'empty-slot';

        row.appendChild(cell);
    });

    tableBody.appendChild(row);
});

//Updates table with existing data
scheduleData.forEach(schedule => {
    updateScheduleTable(schedule.name, schedule.is_rerun, schedule.start_time, schedule.blocks, schedule.day_of_week);
});

//Creates ... for adding/editing new series or movie
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
        document.getElementById('programSource').value = program.source;
        document.getElementById('programUrl').value = program.source_url;
        document.getElementById('programYear').value = program.year;
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

//Creates ... for updating schedule

function openscheduleForm(day, time) {
    currentDay = day;
    currentTime = time;

    document.getElementById('formOverlay').style.display = 'block';
    document.getElementById('scheduleForm').style.display = 'block';

    const currentProgram = scheduleData.find(e => e.start_time === currentTime && e.day_of_week === currentDay);

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
        name: document.getElementById('scheduleTitleSelect').options[document.getElementById('scheduleTitleSelect').selectedIndex].text,
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
                updateScheduleTable(data.name, data.is_rerun, data.end_time, data.time, data.day);

                closeScheduleForm();
            } else {
                alert('Feil ved lagring av program');
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
        source: document.getElementById('programSource').value,
        source_url: document.getElementById('programUrl').value,
        year: document.getElementById('programYear').value,
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
                alert('Feil ved lagring av program?');
            }
        })
        .then(() => {
            location.reload();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Feil ved lagring av program!');
        })
        .finally(() => {
            location.reload();
        });
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
                alert('Error while deleting program');
            }
        })
        .then(() => {
            location.reload();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error while deleting program');
        })
        .finally(() => {
            location.reload();
        });
}
