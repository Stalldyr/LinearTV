header = ["Tid", "Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag", "Lørdag", "Søndag"];
days = header.length - 1 

function createScheduleTable(schedule, times, days, func = null){
    const tables = document.getElementsByClassName('schedule-calendar');

    //Move to backend?
    const scheduleByDay = {};
    for (let day = 1; day <= days; day++) {
        scheduleByDay[day] = {};
    }
    
    schedule.forEach(entry => {
        const day = entry.day_of_week;
        const start = entry.start_time;
        scheduleByDay[day][start] = entry;
    });

    Array.from(tables).forEach(table => {
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');

        header.forEach(head => {
            const th = document.createElement('th');
            th.textContent = head;
            headerRow.appendChild(th);
        });

        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        
        const skipCells = {};
        for (let day = 1; day <= days; day++) {
            skipCells[day] = {};
        }

        times.forEach((time, index) => {
            const row = document.createElement('tr');
            const timeCell = document.createElement('td');
            timeCell.className = 'time-slot';
            timeCell.innerText = time;

            row.appendChild(timeCell);

            for (let day = 1; day <= days; day++) {
                
                if (skipCells[day][time]) continue;

                program = scheduleByDay[day][time]

                const programCell = document.createElement('td');
                const programTitle = document.createElement('div')
                const programStatus = document.createElement('div')
                programTitle.className = 'program-title'
                programStatus.className = 'program-status'

                if (program) {
                    const rowSpan = program.blocks;
                    programCell.rowSpan = rowSpan;
                    programCell.className = program.is_rerun ? 'program-slot rerun' : 'program-slot original';

                    programTitle.innerText = program.name
                    programStatus.innerText = program.is_rerun ? 'Reprise' : ''

                    let currentTime = "";
                    for (let i = 1; i < rowSpan; i++) {
                        currentTime = times[index + i]
                        skipCells[day][currentTime] = true;
                    }
                }

                else {    
                    programCell.className = 'program-slot empty';
                    programTitle.innerText = '---'; 
                }

                programCell.appendChild(programTitle);
                programCell.appendChild(programStatus);
                programCell.addEventListener("click", () => func(day,time));

                row.appendChild(programCell);
            };

            tbody.appendChild(row);
            table.appendChild(tbody);
        });
    })
}



let currentTime = "";
let currentDay = "";

function openscheduleForm(day, time) {
    currentTime = time;
    currentDay = day;

    document.getElementById('overlay').style.display = 'block';
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
    document.getElementById('overlay').style.display = 'none';
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

function fetchMetaData() {
    programType = document.querySelector('input[name="programType"]:checked').value
    tmdbId = document.getElementById('programTmdbId').value
    
    if (!tmdbId) {
        alert('Please enter a TMDB ID');
        return;
    }
    
    let url =`/api/fetch_metadata/${programType}/${tmdbId}`
    
    fetch(url)
        .then(response => response.json())
        .then(result => {
            document.getElementById('programTitle').value = result.title ? result.title : result.original_title;
            document.getElementById('programRelease').value = result.release;
            document.getElementById('programDescription').value = result.overview;
            document.getElementById('programDuration').value = result.run_time;
        });
}
