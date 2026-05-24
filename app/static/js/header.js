document.addEventListener("DOMContentLoaded", () => {
    const tabs = document.querySelectorAll(".auth-tab");
    const underline = document.querySelector(".auth-underline");

    function updateUnderline(activeTab) {
        const rect = activeTab.getBoundingClientRect();
        const parentRect = activeTab.parentElement.getBoundingClientRect();
        const offset = rect.left - parentRect.left;

        underline.style.width = rect.width + "px";
        underline.style.transform = `translateX(${offset}px)`;
    }

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            updateUnderline(tab);

            // eventy do Twojej logiki
            if (tab.dataset.tab === "login") {
                console.log("Switch to login");
            } else {
                console.log("Switch to register");
            }
        });
    });

    // ustawienie startowe
    updateUnderline(document.querySelector(".auth-tab.active"));
});


document.getElementById("themeSwitch").addEventListener("change", e => {
    console.log("Theme toggled:", e.target.checked);
});

document.getElementById("compactSwitch").addEventListener("change", e => {
    console.log("Compact mode:", e.target.checked);
});
