const days = ['mandag', 'tirsdag', 'onsdag', 'torsdag', 'fredag', 'lørdag', 'søndag'];
const dayMapping = {
    'mandag': 1,
    'tirsdag': 2,
    'onsdag': 3,
    'torsdag': 4,
    'fredag': 5,
    'lørdag': 6,
    'søndag': 7
};
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

scheduleData.forEach(schedule => {
    updateScheduleTable(schedule.show_name, schedule.is_rerun, schedule.start_time, schedule.blocks, schedule.day_of_week);
});

const newProgram = document.getElementById('addProgram');
newProgram.onclick = () => openProgramForm();

function openProgramForm() {
    document.getElementById('formOverlay').style.display = 'block';
    document.getElementById('programForm').style.display = 'block';
}

function openscheduleForm(day, time) {
    currentDay = day;
    currentTime = time;

    document.getElementById('formOverlay').style.display = 'block';
    document.getElementById('scheduleForm').style.display = 'block';

    const currentProgram = scheduleData.find(e => e.start_time === currentTime && e.day_of_week === currentDay);

    if (currentProgram) {
        const programSelect = document.getElementById('scheduledProgramTitle');
        programSelect.value = currentProgram.show_name;
        document.getElementById('isRerun').checked = currentProgram.is_rerun;
        updateDurationLabel();
    }
}

function closeScheduleForm() {
    document.getElementById('formOverlay').style.display = 'none';
    document.getElementById('scheduleForm').style.display = 'none';

    document.getElementById('scheduleFormData').reset();
}

function closeProgramForm() {
    document.getElementById('formOverlay').style.display = 'none';
    document.getElementById('programForm').style.display = 'none';

    document.getElementById('programFormData').reset();
}

function updateDurationLabel() {
    const programSelect = document.getElementById('scheduledProgramTitle');
    const selectedOption = programSelect.options[programSelect.selectedIndex];

    const duration = selectedOption.getAttribute('data-duration');
    const durationLabel = document.getElementById('duration');

    if (duration) {
        durationLabel.textContent = `Varighet: ${duration} minutter`;
    } else {
        durationLabel.textContent = '';
    }
}

function updateSeriesForm() {
    const programSelect = document.getElementById('programTitleSelect');
    const selectedOption = programSelect.options[programSelect.selectedIndex];

    const programId = selectedOption.getAttribute('id');
    const program = seriesData.find(e => e.id == programId);

    if (program) {
        document.getElementById('programTitle').value = program.name;
        document.getElementById('programSource').value = program.source;
        document.getElementById('programUrl').value = program.source_url;
        document.getElementById('programSeason').value = program.season;
        document.getElementById('programEpisode').value = program.episode;
        document.getElementById('programYear').value = program.year;
        document.getElementById('programGenre').value = program.genre;
        document.getElementById('programDescription').value = program.description;
        document.getElementById('programDuration').value = program.duration;
        document.getElementById('programTmdbId').value = program.tmdb_id;
        document.getElementById('programIsReverse').checked = program.reverse_order;
    } else {
        document.getElementById('programFormData').reset();
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

function saveSchedule() {

    console.log()
    const data = {
        day_of_week: currentDay,
        start_time: currentTime,
        series_id: document.getElementById('scheduledProgramTitle').options[document.getElementById('scheduledProgramTitle').selectedIndex].getAttribute('id'),
        show_name: document.getElementById('scheduledProgramTitle').options[document.getElementById('scheduledProgramTitle').selectedIndex].text,
        is_rerun: document.getElementById('isRerun').checked,
        duration: parseInt(document.getElementById('scheduledProgramTitle').options[document.getElementById('scheduledProgramTitle').selectedIndex].getAttribute('data-duration'))
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
                updateScheduleTable(data.show_name, data.is_rerun, data.end_time, data.time, data.day);

                closeScheduleForm();
            } else {
                alert('Feil ved lagring av program?');
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

function saveProgram() {
    const programSelect = document.getElementById('programTitleSelect');
    const selectedOption = programSelect.options[programSelect.selectedIndex];
    const programId = selectedOption.getAttribute('id');

    const data = {
        id: programId ? programId : null,
        name: document.getElementById('programTitle').value,
        source: document.getElementById('programSource').value,
        source_url: document.getElementById('programUrl').value,
        season: document.getElementById('programSeason').value,
        episode: document.getElementById('programEpisode').value,
        year: document.getElementById('programYear').value,
        description: document.getElementById('programDescription').value,
        duration: document.getElementById('programDuration').value,
        genre: document.getElementById('programGenre').value,
        tmdb_id: document.getElementById('programTmdbId').value,
        reverse_order: document.getElementById('programIsReverse').checked
    };

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
                alert('Program lagt til!');
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
