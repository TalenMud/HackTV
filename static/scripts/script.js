const hamLogos=document.getElementsByClassName("hamDesign");
let toggleSidebar=false;
const menu=document.getElementById("menu");
const mainContent=document.getElementById("main-content");
const searchBox=document.getElementById("searchbox");


// some default logic for smaller screens
if(window.innerWidth<=1040){
    menu.style.top="-100rem";
    menu.style.width = 0;
    mainContent.style.position="relative";
    mainContent.style.right="2rem";
    searchBox.style.width="0px";
    searchBox.style.display="none";
}

// Hamburger menu logic
Array.from(hamLogos).forEach((hamLogo)=>{

    hamLogo.classList.add("clicked");
    hamLogo.addEventListener("click",()=>{
        toggleSidebar=hamLogo.classList.toggle("clicked");
        if(toggleSidebar)
        {
            menu.style.top="-100rem";
            menu.style.width = 0;
            if(window.innerWidth<=1040){
              mainContent.style.display="flex";
            }
        }
        else
        {
            menu.style.top=0;
            if(window.innerWidth<=1040){
              mainContent.style.display="none";
              menu.style.width="100vw";
            }else{
              menu.style.width = "15rem";
            }
        }
        
    });
});


