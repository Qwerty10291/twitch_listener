class Streamer {
  constructor() {
    this.active_streamer = null;
    this.streamer_name = document.getElementById("current_sreamer");
    this.clips_container = document.querySelector(".videos");
    this.connect_add_button();
    this.get_streamers();
  }

  get_streamers() {
    fetch("/api/game").then((resp) => {
      if (resp.status != 200)
        alert(
          "Ошибка загрузки стримеров. Попробуйте перезагрузить страницу и проверьте работоспособность сервера"
        );
      else
        resp.json().then((data) => {
          this.data = data;
          this.sort_streamers();
          this.init_html();
        });
    });
  }

  init_html() {
    let container = document.querySelector(".streamers");
    container.innerHTML = "";
    for (let game of this.data) {
      let game_container = document.createElement("div");
      game_container.className = "game";
      game_container.innerHTML = `<span>${game.name}</span>`;
      game.element = game_container;
      for (let streamer of game.streamers) {
        let streamer_container = document.createElement("div");
        if (streamer.is_online)
          streamer_container.className = "streamer online";
        else streamer_container.className = "streamer offline";
        streamer_container.innerHTML = streamer.name;
        streamer.element = streamer_container;
        streamer_container.addEventListener("click", () => {
          this.change_streamer(streamer);
        });
        game_container.append(streamer_container);
      }
      container.append(game_container);
    }
  }

  generate_clip_html(clip_data) {
    this.clips_container.innerHTML = "";
    for (let clip of clip_data) {
      let container = document.createElement("div");
      container.className = "video-card";
      container.innerHTML = `<img src=${clip.image}></img><span class="count">${clip.activity}</span>`;
      container.addEventListener("click", () => {
        let link = document.createElement("a");
        link.setAttribute("href", clip.video);
        link.setAttribute("download", clip.id + ".mp4");
        link.click();
      });
      this.clips_container.append(container);
    }
  }

  change_streamer(streamer) {
    if (this.active_streamer !== null) {
      if (this.active_streamer.name == streamer.name) return;
      this.active_streamer.element.style.border = "";
      streamer.element.style.border = "2px solid gray";
      this.active_streamer = streamer;
      this.update_clips(streamer)
    } else {
      streamer.element.style.border = "2px solid gray";
      this.active_streamer = streamer;
      this.update_clips(streamer)
    }
  }

  sort_streamers() {
    this.data.sort();
    for (let game of this.data) {
      game.streamers.sort((a, b) => a.activity - b.activity);
    }
  }

  connect_add_button() {
    this.game_input = document.getElementById("game_name");
    this.streamer_input = document.getElementById("streamer_name");
    this.error_container = document.querySelector(".streamer-error");
    document.getElementById("streamer_commit").addEventListener("click", () => {
      this.add_streamer(this.game_input.value, this.streamer_input.value);
    });
  }

  add_streamer(game, streamer) {
    let form_data = new FormData();
    form_data.append("name", streamer);
    form_data.append("game", game);
    fetch("/api/streamer", { method: "POST", body: form_data }).then((resp) => {
      resp.json().then((data) => {
        if (data.error)this.error_container.innerHTML = data.error;
        else{
          this.error_container.innerHTML = ""
          setTimeout(this.get_streamers, 1000)
        }
      });
    });
  }

  update_clips(streamer) {
    fetch("/api/streamer/" + streamer.id).then((resp) => {
      if (resp.status != 200) alert("Ошибка загрузки информации о клипах");
      else {
        resp.json().then((data) => {
          data.clips.sort((a, b) => a.activity - b.activity);
          this.generate_clip_html(data.clips);
        });
      }
    });
  }
}

streamers = new Streamer();