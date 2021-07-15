let admin_container = document.querySelector(".admin-container");
let users_container = document.querySelector(".user-container");

function update_users() {
  fetch("/api/user").then((resp) => {
    if (resp.status != 200) alert("Ошибка загрузки списка пользователей");
    else
      resp.json().then((data) => {
        generate_users_html(data);
      });
  });
}

function generate_users_html(users_data) {
  document.querySelectorAll('span.user').forEach((node) => {node.remove()})
  for (let user of users_data) {
    let user_container = document.createElement("div");
    user_container.className = "user offline";
    user_container.innerText = user.login;
    switch (user.role) {
      case "admin":
        admin_container.append(user_container);
        break;
      case "user":
        users_container.append(user_container);
    }
  }
}

update_users()