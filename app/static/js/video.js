// ===============================
// VIDEO COMPRESSION FRONTEND
// ===============================

const uploadForm = document.getElementById("uploadForm");
const fileInput = document.getElementById("files_video");
const dropZone = document.getElementById("dropZone");
const statusBox = document.getElementById("status");
const progressContainer = document.getElementById("fileProgressContainer");
const fill = document.getElementById("progressFill");

let currentTaskId = null;


// =========================
// RENDER VIDEO FILES
// =========================

function renderVideoFiles(files) {

    const container = document.getElementById("fileProgressContainer");
    container.innerHTML = "";

    for (let f of files) {

        const safeId = createSafeId(f.name);

        // Miniaturka wideo (pierwsza klatka)
        let videoThumb = "";
        if (f.type.startsWith("video/")) {
            const url = URL.createObjectURL(f);
            videoThumb = `
                <video class="file-thumb" src="${url}" muted preload="metadata"></video>
            `;
        }

        container.innerHTML += `
            <div class="file-block" id="file-${safeId}">

                <input                    
                    type="checkbox" 
                    class="file-select" 
                    data-filename="${f.name}" id="check-${safeId}"
                >

                ${videoThumb}

                <div class="file-size" id="size-${safeId}"></div>

                <div class="file-b">

                    <div class="file-name">
                        ${f.name}
                    </div>

                    <div class="progress-wrapper">

                        <div class="progress-bar">
                            <div class="progress-fill" style="width:0%"></div>
                        </div>

                        <div class="progress-label">
                            0%
                        </div>

                    </div>

                </div>

            </div>
        `;
    }
}

function createSafeId(name) {
    return btoa(unescape(encodeURIComponent(name)))
        .replace(/=/g, "");
}

function updateVideoSizes(files) {

    for (let f of files) {

        const safeId = createSafeId(f.name);
        const sizeMB = (f.size / 1024 / 1024).toFixed(2);

        const el = document.getElementById(`size-${safeId}`);
        if (el) {
            el.textContent = `${sizeMB} MB`;
        }
    }
}



// =========================
// INPUT
// =========================
document.getElementById("files_video").onchange = (e) => {

    const files = e.target.files;

    // LIMIT: tylko 1 film
    if (files.length > 3) {
        showWarning("Możesz przesłać tylko 3 filmy.");
        return;
    }

    // LIMIT: max 5 minut (sprawdzimy backendem)
    // LIMIT: max 350 MB (opcjonalnie)
    const sizeMB = files[0].size / 1024 / 1024;
    if (sizeMB > 350) {
        showWarning("Rozmiar pliku(-ów) jest zbyt duży (max 350 MB).");
        return;
    }

    renderVideoFiles(files);
    updateVideoSizes(files);
};



// ===============================
// DRAG & DROP
// ===============================

["dragenter", "dragover", "dragleave", "drop"].forEach(ev => {
    dropZone.addEventListener(ev, (e) => {
        e.preventDefault();
        e.stopPropagation();
    });
});

["dragenter", "dragover"].forEach(ev => {
    dropZone.addEventListener(ev, () => {
        dropZone.classList.add("dragover");
    });
});

["dragleave", "drop"].forEach(ev => {
    dropZone.addEventListener(ev, () => {
        dropZone.classList.remove("dragover");
    });
});

dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    e.stopPropagation();

    const dtFiles = e.dataTransfer.files;

    // LIMIT: tylko 1 film
    if (dtFiles.length > 3) {
        showWarning("Możesz przesłać tylko 3 filmy.");
        return;
    }

    // LIMIT: max 350 MB
    const sizeMB = dtFiles[0].size / 1024 / 1024;
    if (sizeMB > 350) {
        showWarning("warning_file_too_big", `„${dtFiles[0].name}” jest większy niż 350 MB`);
        return;
    }

    document.getElementById("files_video").files = dtFiles;

    renderVideoFiles(dtFiles);
    updateVideoSizes(dtFiles);

    document.getElementById("fileProgressContainer").scrollIntoView({
        behavior: "smooth"
    });
});


// ===============================
// FORM SUBMIT
// ===============================

uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const file = fileInput.files[0];
    if (!file) {
        alert("Wybierz plik wideo.");
        return;
    }

    progressContainer.innerHTML = "";
    statusBox.innerHTML = "Wysyłanie pliku...";

    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch("/compress/video", {
            method: "POST",
            body: formData
        });

        const data = await res.json();
        console.log("submit:", data);

        if (!res.ok) {
            statusBox.innerHTML = "Błąd: " + data.detail;
            return;
        }

        currentTaskId = data.task_id;
        statusBox.innerHTML = "Plik dodany do kolejki...";
        createProgressUI(file.filename)
        pollStatus();

    } catch (err) {
        statusBox.innerHTML = "Błąd połączenia.";
    }
});


function createProgressUI(filename) {
    const container = document.getElementById("fileProgressContainer");
    container.innerHTML = `
        <div class="progress-item" id="progress-item">
            <div class="progress-label" id="videoProgressLabel">0%</div>
            <div class="progress-bar">
                <div id="videoProgressFill" class="progress-fill" style="width:0%"></div>
            </div>
        </div>
    `;
}


// ===============================
// POLLING STATUS
// ===============================

async function pollStatus() {
    if (!currentTaskId) return;

    try {
        const res = await fetch(`/compress/video/status/${currentTaskId}`);
        const data = await res.json();

        console.log("pollStatus:", data);

        if (data.error) {
            statusBox.innerHTML = "Błąd: " + data.error;
            return;
        }

        // Kolejka
        if (data.queue_position > 0) {
            statusBox.innerHTML = `Przed tobą ${data.queue_position} użytkowników...`;
        } else if (data.status === "processing") {
            statusBox.innerHTML = data.message || "Twoje zadanie jest przetwarzane...";
        }

        // Upewnij się, że UI paska istnieje
        const fillEl = document.getElementById("videoProgressFill");
        const labelEl = document.getElementById("videoProgressLabel");

        if (data.progress !== undefined && fillEl && labelEl) {
            const pct = Math.max(0, Math.min(100, Number(data.progress)));
            fillEl.style.width = `${pct}%`;
            labelEl.textContent = `${pct}%`;

            // Kolor zależny od wartości
            if (pct < 40) {
                fillEl.style.background = "linear-gradient(90deg,#f44336,#ff7043)"; // czerwony
            } else if (pct < 80) {
                fillEl.style.background = "linear-gradient(90deg,#ffb300,#ffca28)"; // pomarańcz
            } else {
                fillEl.style.background = "linear-gradient(90deg,#4caf50,#8bc34a)"; // zielony
            }
        }

        // Zakończone
        if (data.status === "done") {
            statusBox.innerHTML = "Kompresja zakończona!";
            // zostaw pasek na 100% przez chwilę, potem wyczyść
            setTimeout(() => {
                document.getElementById("fileProgressContainer").innerHTML = "";
            }, 1200);

            downloadVideo(currentTaskId);
            return;
        }

        // Błąd
        if (data.status === "error") {
            statusBox.innerHTML = "Błąd: " + data.error;
            return;
        }

        // Poll co 1 sekundę
        setTimeout(pollStatus, 1000);

    } catch (err) {
        statusBox.innerHTML = "Błąd połączenia.";
    }
}



// ===============================
// DOWNLOAD RESULT
// ===============================

async function downloadVideo(taskId) {
    const res = await fetch(`/compress/video/download/${taskId}`);

    if (!res.ok) {
        statusBox.innerHTML = "Błąd pobierania pliku.";
        return;
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "compressed_video.mp4";
    a.click();

    URL.revokeObjectURL(url);
}




// =========================
// WARNING MODAL
// =========================
function showWarning(i18nKey, dynamicText = "") {
    const modal = document.getElementById("warningModal");
    const msgTooMany = document.getElementById("warningTooMany");
    const msgTooBig = document.getElementById("warningTooBig");
    const btn = document.getElementById("warningClose");

    // Reset widoczności
    msgTooMany.classList.add("hidden");
    msgTooBig.classList.add("hidden");

    // Wybór komunikatu
    if (i18nKey === "warning_too_many_files") {
        msgTooMany.classList.remove("hidden");
    }

    if (i18nKey === "warning_file_too_big") {
        msgTooBig.classList.remove("hidden");

        // dynamiczny tekst (np. nazwa pliku)
        if (dynamicText) {
            msgTooBig.textContent = dynamicText;
        }
    }

    // Odśwież tłumaczenia
    if (typeof applyTranslations === "function") {
        applyTranslations();
    }

    modal.classList.remove("hidden");

    btn.onclick = () => {
        modal.classList.add("hidden");
    };
}
