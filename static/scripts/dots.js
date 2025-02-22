const bg=document.getElementById("background");

const cols = Math.ceil(window.innerWidth / 40);
const rows = Math.ceil(window.innerHeight / 40);

//That 270 thing is for my screen only, will fix later
for (let i = 0; i < cols*rows -270; i++) {
  let dot = document.createElement("div");
  dot.classList.add("circle");
  bg.appendChild(dot);
}

const dots = document.querySelectorAll(".circle");

document.addEventListener("mousemove", (e) => {
  const rect=bg.getBoundingClientRect();
  const mouseX=e.clientX-rect.left;
  const mouseY=e.clientY-rect.top;

  dots.forEach((dot) => {
    const dotX=dot.offsetLeft+dot.clientWidth/2;
    const dotY=dot.offsetTop+dot.clientHeight/2;

    const distance=Math.sqrt((mouseX-dotX)**2+(mouseY-dotY)**2);

    if (distance < 100) {
      dot.classList.add("glow");
    } else {
      dot.classList.remove("glow");
    }
  });
});
