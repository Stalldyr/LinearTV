header = ["Tid", "Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag", "Lørdag", "Søndag"];
days = header.length - 1 

function createScheduleTable(schedule, times, days, func = null){
    const tables = document.getElementsByClassName('schedule-calendar');

    //Move to backend?
    const scheduleByDay = {};
    for (let day = 1; day <= days; day++) {
        scheduleByDay[day] = {};
    }
    
    //Move to backend?
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
                    programTitle.innerText = '---'            
                }

                programCell.appendChild(programTitle)
                programCell.appendChild(programStatus)
                programCell.onclick = () => func(day,time);

                row.appendChild(programCell)
            };

            tbody.appendChild(row);
            table.appendChild(tbody);
        });
    })
}