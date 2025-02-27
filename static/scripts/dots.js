const bg = document.getElementById("background");
// size + gap defined in CSS, also change here if changed in CSS
const cellSize = 40;
const gap = 5;

function generateDots() {
  bg.innerHTML = "";

  const cols = Math.floor((window.innerWidth + gap) / (cellSize + gap));
  const rows = Math.floor((window.innerHeight + gap) / (cellSize + gap));

  for (let i = 0; i < cols * rows; i++) {
    const dot = document.createElement("div");
    dot.classList.add("circle");
    bg.appendChild(dot);
  }
}

generateDots();

document.addEventListener("mousemove", (e) => {
  const rect = bg.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;

  document.querySelectorAll(".circle").forEach((dot) => {
    const dotX = dot.offsetLeft + dot.clientWidth / 2;
    const dotY = dot.offsetTop + dot.clientHeight / 2;
    const distance = Math.sqrt((mouseX - dotX) ** 2 + (mouseY - dotY) ** 2);

    if (distance < 100) {
      dot.classList.add("glow");
    } else {
      dot.classList.remove("glow");
    }
  });
});

window.addEventListener("resize", generateDots);