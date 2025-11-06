let timeOnPage = 0;

setInterval(() => {
    timeOnPage += 10;
    
    fetch('/api/traffic', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({seconds: timeOnPage})
    });
}, 10000); 

let currentProgram = null;

function updateProgram() {
    const tvPlayer = document.getElementById('tvPlayer');

    fetch('/api/current')
        .then(response => response.json())
        .then(program => {
            console.log("Fetched program:", program);
            if (JSON.stringify(program) !== JSON.stringify(currentProgram)) {
                console.log("Program changed!", program);
                currentProgram = program;
                
                const player = document.getElementById('tvPlayer');
                if (program.status === "off_air" || program.status === "no_program" || program.status === "unavailable") {
                    player.src = ``;
                    document.getElementById('programTitle').innerText = program.name;
                    document.getElementById('programTime').innerText = "";
                    document.getElementById('programDescription').innerText = program.description;
                } else {
                    player.src = `/video/${program.directory}/${program.filename}`;
                    document.getElementById('programTitle').innerText = program.name;
                    document.getElementById('programTime').innerText = `${program.start_time} - ${program.end_time}`;
                    if (program.episode_description){
                        document.getElementById('programDescription').innerText = program.episode_description;
                    } else {
                        document.getElementById('programDescription').innerText = program.series_description;
                    }
                }
            }
        });
}

setInterval(updateProgram, 1000)