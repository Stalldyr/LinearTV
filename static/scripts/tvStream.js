let timeOnPage = 0;
const video = document.getElementById('tvPlayer');

setInterval(() => {
    timeOnPage += 10;
    
    fetch('/api/traffic', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({seconds: timeOnPage})
    });
}, 10000); 


//Fetches current program
let currentProgram = null;

function updateProgram() {
    fetch('/api/current')
        .then(response => response.json())
        .then(program => {
            if (JSON.stringify(program) !== JSON.stringify(currentProgram)) {
                console.log("Program changed!", program);
                currentProgram = program;
                
                if (program.status === "off_air" || program.status === "no_program" || program.status === "unavailable") {
                    video.src = ``;
                    document.getElementById('programTitle').innerText = program.name;
                    document.getElementById('programTime').innerText = "";
                    document.getElementById('programDescription').innerText = program.description;
                } else {
                    video.src = `/video/${program.content_type}/${program.directory}/${program.filename}`;
                    document.getElementById('programTitle').innerText = program.name;
                    document.getElementById('programTime').innerText = `${program.start_time} - ${program.end_time}`;
                    if (program.episode_description){
                        if (program.episode_number){
                            document.getElementById('programDescription').innerText = `Episode ${program.episode_number}: ${program.episode_description}`;
                        } else {
                            document.getElementById('programDescription').innerText = program.episode_description;
                        }
                    } else {
                        document.getElementById('programDescription').innerText = program.program_description;
                    }
                }

                if (program.is_rerun){
                    document.getElementById('programTitle').innerText += " (R)"
                }
            }
        });
}

function getCorrectTime(){
  return "10:02"
}

video.addEventListener('pause', function() {
  video.play();
});

video.addEventListener('seeking', function() {
  video.currentTime = getCorrectTime(); // Hopper tilbake til riktig tid
});

video.addEventListener('keydown', function(e) {
  if(e.code === 'Space' || e.code === 'ArrowLeft' || e.code === 'ArrowRight') {
    e.preventDefault();
  }
});

const fullscreenBtn = document.getElementById("fullscreenBtn");

// Function to request fullscreen
function enterFullscreen() {
  if (video.requestFullscreen) {
    video.requestFullscreen();
  } else if (video.webkitRequestFullscreen) {
    // Safari
    video.webkitRequestFullscreen();
  } else if (video.mozRequestFullScreen) {
    // Firefox
    video.mozRequestFullScreen();
  } else if (video.msRequestFullscreen) {
    // IE/Edge
    video.msRequestFullscreen();
  }
}

// Function to exit fullscreen
function exitFullscreen() {
  if (document.exitFullscreen) {
    document.exitFullscreen();
  } else if (document.webkitExitFullscreen) {
    // Safari
    document.webkitExitFullscreen();
  } else if (document.mozCancelFullScreen) {
    // Firefox
    document.mozCancelFullScreen();
  } else if (document.msExitFullscreen) {
    // IE/Edge
    document.msExitFullscreen();
  }
}

// Toggle fullscreen on button click
fullscreenBtn.addEventListener("click", function () {
  if (!document.fullscreenElement) {
    enterFullscreen();
  } else {
    exitFullscreen();
  }
});

testBtn.addEventListener("click", function () {
  video.currentTime = 60*10
});
setInterval(updateProgram, 5000)