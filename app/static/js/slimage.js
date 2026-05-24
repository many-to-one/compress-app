document.addEventListener("DOMContentLoaded", function () {
    const snail = document.getElementById("slimage-snail");
    const shell = document.querySelector(".snail-shell");
    const spiralOuter = document.querySelector(".spiral-outer");
    const spiralInner = document.querySelector(".spiral-inner");
    const portalCore = document.querySelector(".portal-core");
    const trail = document.getElementById("snail-trail");
    const layers = document.querySelectorAll("#slimage-snail .snail-layer");
    const lensflareContainer = document.getElementById("snail-lensflare");
    const sparksContainer = document.getElementById("snail-sparks");

    if (!snail) {
        console.warn("Slimage: #slimage-snail not found");
        return;
    }

    function spawnSpark(x, y) {
        if (!sparksContainer) return;
        const spark = document.createElement("div");
        spark.className = "spark";
        spark.style.left = x + "px";
        spark.style.top = y + "px";
        sparksContainer.appendChild(spark);
        setTimeout(() => spark.remove(), 600);
    }

    function spawnFlare(x, y) {
        if (!lensflareContainer) return;
        const flare = document.createElement("div");
        flare.className = "lensflare";
        flare.style.left = x + "px";
        flare.style.top = y + "px";
        lensflareContainer.appendChild(flare);
        setTimeout(() => flare.remove(), 800);
    }

    function updateSnail() {
        const scrollTop = window.scrollY || window.pageYOffset || 0;
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        const progress = docHeight > 0 ? scrollTop / docHeight : 0;

        // ruch po X
        const maxX = window.innerWidth * 0.9;
        const x = progress * maxX;
        snail.style.transform = `translateX(${x}px)`;

        // neonowy ślad
        if (trail) {
            trail.style.width = `${x}px`;
        }

        // parallax
        layers.forEach(layer => {
            const depth = layer.dataset.depth ? Number(layer.dataset.depth) : 1;
            layer.style.transform = `translateY(${progress * depth * 2}px)`;
        });

        // portal 3D – wewnętrzna paralaksa
        if (portalCore) {
            const innerShift = progress * 8;
            portalCore.style.transform = `translate(${innerShift}px, ${innerShift}px)`;
        }

        // obrót portalu tylko podczas scrolla
        const rotation = progress * 720;
        if (shell) shell.style.transform = `rotate(${rotation}deg)`;
        if (spiralOuter) spiralOuter.style.transform = `rotate(${rotation}deg)`;
        if (spiralInner) spiralInner.style.transform = `rotate(${rotation * 1.4}deg)`;

        // grawitacja portalu – ciało lekko ciągnięte
        const bodies = document.querySelectorAll(".snail-body");
        if (progress > 0.05) {
            bodies.forEach(b => b.classList.add("gravity"));
        } else {
            bodies.forEach(b => b.classList.remove("gravity"));
        }

        // iskry energii
        if (Math.random() < 0.15) {
            const rect = snail.getBoundingClientRect();
            spawnSpark(rect.left + 70, rect.top + 55);
        }

        // lens flare
        if (Math.random() < 0.1) {
            const rect = snail.getBoundingClientRect();
            spawnFlare(rect.left + 70, rect.top + 55);
        }
    }

    window.addEventListener("scroll", updateSnail);
    window.addEventListener("resize", updateSnail);
    updateSnail();

    // API dla batch.js / logiki aplikacji

    // loading (oczekiwanie na wynik)
    window.snailStartLoading = function () {
        snail.classList.add("loading");
    };

    window.snailStopLoading = function () {
        snail.classList.remove("loading");
    };

    // sukces
    window.snailSuccess = function () {
        snail.classList.remove("loading");
        snail.classList.add("success");
        setTimeout(() => snail.classList.remove("success"), 700);
    };

    // błąd
    window.snailError = function () {
        snail.classList.remove("loading");
        snail.classList.add("error");
        setTimeout(() => snail.classList.remove("error"), 600);
    };

    // Turbo Snail (kompresja – otwieranie portalu)
    window.startShellSpin = function () {
        if (portalCore) portalCore.classList.add("open");
        if (spiralOuter) spiralOuter.classList.add("open");
        if (spiralInner) spiralInner.classList.add("open");
        if (shell) shell.classList.add("open");
        snailStartLoading();
    };

    window.stopShellSpin = function () {
        if (portalCore) portalCore.classList.remove("open");
        if (spiralOuter) spiralOuter.classList.remove("open");
        if (spiralInner) spiralInner.classList.remove("open");
        if (shell) shell.classList.remove("open");
        snailStopLoading();
    };
});


// Matrix
document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("matrix-mouse");
    // const chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    const chars = "0123456789";


    let lastX = 0;
    let lastY = 0;
    let lastTime = performance.now();

    document.addEventListener("mousemove", (e) => {
        const now = performance.now();
        const dt = now - lastTime;

        const dx = e.clientX - lastX;
        const dy = e.clientY - lastY;

        const speed = Math.sqrt(dx*dx + dy*dy) / dt; // px/ms

        lastX = e.clientX;
        lastY = e.clientY;
        lastTime = now;

        // liczba kolumn zależna od prędkości
        const columns = Math.min(1 + Math.floor(speed * 4), 8);

        for (let i = 0; i < columns; i++) {
            const span = document.createElement("div");
            span.className = "matrix-char";

            // losowy znak
            span.textContent = chars[Math.floor(Math.random() * chars.length)];

            // promień 20px
            const offsetX = (Math.random() * 40) - 20;
            const offsetY = (Math.random() * 40) - 20;

            span.style.left = (e.clientX + offsetX) + "px";
            span.style.top = (e.clientY + offsetY) + "px";

            container.appendChild(span);

            // usuń po animacji
            setTimeout(() => span.remove(), 500);
        }
    });
});

