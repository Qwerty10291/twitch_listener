document.onkeydown = (evt) => {
    evt = evt || window.event;
    switch (evt.key) {
        case "ArrowUp":
          video_speed_up();
          break;
        case "ArrowDown":
          video_speed_normal();
          break;
    }
}

function video_speed_up(){
    document.querySelector('video').playbackRate = 2.0
}
function video_speed_normal() {
    document.querySelector('video').playbackRate = 1.0
}