document.getElementById("loginForm").addEventListener("submit", function (event) {
  event.preventDefault();

  const username = document.getElementById("username").value.trim();
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
