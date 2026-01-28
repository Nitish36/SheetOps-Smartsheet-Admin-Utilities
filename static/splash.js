window.addEventListener("load", () => {
  const splash = document.getElementById("splash");
  const app = document.getElementById("app");

  setTimeout(() => {
    splash.classList.add("fade-out");
    app.classList.remove("hidden");
  }, 2200); // 2.2 seconds
});
