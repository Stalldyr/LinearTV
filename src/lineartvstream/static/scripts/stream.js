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
};

var player 

function create_subtitles(subtitles){
  subtitles.forEach(subtitle => {
    const track = document.createElement("track")
    track.src = subtitle.src
    track.srclang = subtitle.language
    track.label = subtitle.label

    player.appendChild(track)
  });
}

function onProgramChanged(el) {
    const source = el.dataset.source;
    const offset = parseFloat(el.dataset.offset) || 0;

    player.src({ src: `/video/${source}`, type: 'video/mp4' });
    player.currentTime(offset);
}

addEventListener('DOMContentLoaded', () => {
  player = videojs('tvPlayer', options)

  player.logo({
    image: '', //Insert link to logo here
    width: 30,
    height: 30,
    fadeDelay: null
  });
});

