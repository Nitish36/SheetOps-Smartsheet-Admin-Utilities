document.getElementById("loginForm").addEventListener("submit", function (event) {
  event.preventDefault();

  const username = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();

  const usernameError = document.getElementById("usernameError");
  const passwordError = document.getElementById("passwordError");

  let isValid = true;

  if (username === "") {
    usernameError.style.display = "block";
    isValid = false;
  } else {
    usernameError.style.display = "none";
  }

  if (password === "") {
    passwordError.style.display = "block";
    isValid = false;
  } else {
    passwordError.style.display = "none";
  }

  if (isValid) {
    this.submit();
  }
});


// Auto-hide flash messages after 4 seconds
window.addEventListener("DOMContentLoaded", (event) => {
  const flashMessages = document.querySelectorAll(".flash-message");
  flashMessages.forEach(msg => {
    setTimeout(() => {
      msg.style.transition = "opacity 0.5s ease-out";
      msg.style.opacity = "0";
      setTimeout(() => msg.remove(), 500);
    }, 4000); // 4000ms = 4 seconds
  });
});


