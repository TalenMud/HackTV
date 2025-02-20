let hamLogos=document.getElementsByClassName("hamDesign");
let toggleSidebar=false;
let menu=document.getElementById("menu");

Array.from(hamLogos).forEach((hamLogo)=>{
    hamLogo.addEventListener("click",()=>{
        toggleSidebar=hamLogo.classList.toggle("clicked");
        if(toggleSidebar){
            menu.style.top="-100rem";
        }else{
            menu.style.top=0;
        }
        
    });
});

