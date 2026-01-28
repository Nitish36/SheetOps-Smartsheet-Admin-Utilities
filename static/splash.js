// Splash screen script
window.addEventListener("load", () => {
  const splash = document.getElementById("splash");
  const app = document.getElementById("app");

  setTimeout(() => {
    splash.classList.add("fade-out");
    app.classList.remove("hidden");
  }, 2200); // 2.2 seconds
});

// Snackbar Script
function myFunction() {
  var x = document.getElementById("snackbar");
  x.className = "show";
  setTimeout(function(){ x.className = x.className.replace("show", ""); }, 3000);
}