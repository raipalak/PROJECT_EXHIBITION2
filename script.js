function setTheme(theme){
  if(theme === "night"){
    document.body.classList.add("night");
    localStorage.setItem("theme","night");
  } else {
    document.body.classList.remove("night");
    localStorage.setItem("theme","day");
  }
}

// Load saved theme
window.onload = function(){
  const saved = localStorage.getItem("theme");
  if(saved === "night"){
    document.body.classList.add("night");
  }
};