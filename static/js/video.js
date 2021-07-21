let is_playing = false

document.onkeydown = (evt) => {
    evt = evt || window.event;
    switch (evt.key) {
        case "ArrowUp":
          video_speed_up();
          break;
        case "ArrowDown":
          video_speed_normal();
          break;
        case "Shift":
          download_video()
          break;
        case "Escape":
          window.close()
          break;
        case " ":
            if(is_playing)
              video_stop()
            else
              video_play()

    }
}

function video_speed_up(){
    document.querySelector('video').playbackRate = 2.0
}
function video_speed_normal() {
    document.querySelector('video').playbackRate = 1.0
}
function video_stop(){
    document.querySelector('video').pause()
}
function video_play(){
    document.querySelector('video').play()
}
function download_video(){
    let href = document.querySelector('.download').getAttribute("href")
    let download = document.querySelector('.download').getAttribute("download")
    let link = document.createElement("a");
    link.setAttribute("href", href);
    link.setAttribute("download", download);
    link.click();
}
