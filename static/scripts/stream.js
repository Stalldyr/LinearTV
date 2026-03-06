 const options = {
    muted:false,
    preload:"auto",
    autoplay:true,
    controls: true,
    controlBar: {
      playToggle: false,
      progressControl: false, 
      remainingTimeDisplay: false,
      volumePanel: true,  
      fullscreenToggle: true
    },
    techOrder: [ 'chromecast', 'html5' ],
    plugins: {
      chromecast: {}
    }
  };

  var player = videojs('tvPlayer', options)

  player.logo({
    image: '', //Insert link to logo here
    width: 30,
    height: 30,
    fadeDelay: null
  });

  function onProgramChanged(program){
    if (program.status === "available"){
      if (parseInt(program.offset) > parseInt(program.duration)){
        player.src(`{{ url_for("streaming.static", filename="PM5544.mp4" ) }}`);
      } else {
        player.src(`/video/${program.filepath}`);
      }
      document.getElementById('programTitle').innerText = program.episode.series.title;
      document.getElementById('programTime').innerText = `${program.start} - ${program.end}`;

      if (program.episode.episode_number){
          document.getElementById('programDescription').innerText = `Episode ${program.episode.episode_number}: ${program.episode.description}`;
      } else {
          document.getElementById('programDescription').innerText = program.episode.description;
      }

    } else {
      player.src(`{{ url_for("streaming.static", filename="PM5544.mp4" ) }}`);
      document.getElementById('programTitle').innerText = program.title;
      document.getElementById('programTime').innerText = "";
      document.getElementById('programDescription').innerText = program.description;
    }

    player.currentTime(program.offset)

    if (program.is_rerun){
        document.getElementById('programTitle').innerText += " (R)"
    }
  }

  function create_subtitles(subtitles){
    subtitles.forEach(subtitle => {
      const track = document.createElement("track")
      track.src = subtitle.src
      track.srclang = subtitle.language
      track.label = subtitle.label

      player.appendChild(track)
    });
  }
  
  function SSE(){
    const evtSource = new EventSource("stream/current");

    evtSource.onmessage = (e) => {
      const program = JSON.parse(e.data);
      onProgramChanged(program);
    };
  }

  function Polling(){
    let currentProgram = "";
    function updateProgram() {
        fetch('/stream/current')
          .then(response => response.json())
          .then(program => {
            console.log(program)//REMOVEB4COMMIT
            if (program.filename !== currentProgram) {
              currentProgram = program.filename;
              onProgramChanged(program);
            }
          });
    }

    updateProgram();
    setInterval(updateProgram, 5000);
  }

  addEventListener('DOMContentLoaded', (event) => {
    player.src(`{{ url_for("streaming.static", filename="PM5544.mp4" ) }}`);
    Polling();
  });

  