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
    //techOrder: [ 'chromecast', 'html5' ],
    //plugins: {
    //  chromecast: {}
    //}
  };

  var player = videojs('tvPlayer', options)

  player.logo({
    image: '', //Insert link to logo here
    width: 30,
    height: 30,
    fadeDelay: null
  });

  let fetch_link = "/stream/nrk1"
  function setChannelNRK1(){
    fetch_link = "/stream/nrk1"
    updateProgram();
  }

  function setChannelNRK2(){
    fetch_link = "/stream/nrk2"
    updateProgram();
  }

  function setChannelCable(){
    fetch_link = "/stream/cable"
    updateProgram();
  }

  const noProgramSource = { src: '/video/noprogram?t=' + Date.now(), type: 'video/mp4' }
  let currentProgram = null;
  let currentChannel = null;

  function onProgramChanged(program){
    if (program.status === "available"){
      if (parseInt(program.offset) > parseInt(program.duration)){
        player.src(noProgramSource);
      } else {
        
        player.src(`/video/${program.filepath}`);
      }
      document.getElementById('programTitle').innerText = program.title;
      document.getElementById('programTime').innerText = `${program.start} - ${program.end}`;

      if (program.episode_number){
          document.getElementById('programDescription').innerText = `Episode ${program.episode_number}: ${program.description}`;
      } else {
          document.getElementById('programDescription').innerText = program.description;
      }

    } else {
      player.src(noProgramSource);
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
    const evtSource = new EventSource(fetch_link);

    evtSource.onmessage = (e) => {
      const program = JSON.parse(e.data);
      onProgramChanged(program);
    };
  }

  function updateProgram() {
    fetch(fetch_link)
      .then(response => response.json())
      .then(program => {
        if (program.id !== currentProgram || currentChannel !== program.channel) {
          currentProgram = program.id;
          currentChannel = program.channel;
          onProgramChanged(program);
        }
  })};

  function Polling(){
    updateProgram();
    setInterval(updateProgram, 5000);
  }

  addEventListener('DOMContentLoaded', (event) => {
    player.ready(function() {
      Polling();
    });
  });

  