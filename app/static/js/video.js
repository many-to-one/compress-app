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

const videoCompBtn = document.getElementById("startVideosBtn");


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

    const dtFiles = e.target.files;
    const closeBtn = document.getElementById("warningClose");

    // LIMIT: tylko 1 film
    if (dtFiles.length > 3) {
        showVideoWarning("warning_video_too_many_files");
        closeBtn.addEventListener("click", () => {
            window.location.href = "/";
        });
        return;
    }

    // LIMIT: max 350 MB
    for (const f of dtFiles) {
        console.log('Drop --- Processing file:', f);
        if (f.type.startsWith("video/")) {
            const sizeMB = f.size / 1024 / 1024;
            console.log(`File: ${f.name}, Size: ${sizeMB} MB`);
            if (sizeMB > 350) {
                showVideoWarning("warning_video_file_too_big");
                closeBtn.addEventListener("click", () => {
                    window.location.href = "/";
                });
                return;
            }
        } 
    }


    renderVideoFiles(dtFiles);
    updateVideoSizes(dtFiles);
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
    const closeBtn = document.getElementById("warningClose");

    // LIMIT: tylko 1 film
    if (dtFiles.length > 3) {
        showVideoWarning("warning_video_too_many_files");
        closeBtn.addEventListener("click", () => {
            window.location.href = "/";
        });
        return;
    }

    // LIMIT: max 350 MB
    for (const f of dtFiles) {
        console.log('Drop --- Processing file:', f);
        if (f.type.startsWith("video/")) {
            const sizeMB = f.size / 1024 / 1024;
            console.log(`File: ${f.name}, Size: ${sizeMB} MB`);
            if (sizeMB > 350) {
                showVideoWarning("warning_video_file_too_big");
                closeBtn.addEventListener("click", () => {
                    window.location.href = "/";
                });
                return;
            }
        } 
    }

    document.getElementById("files_video").files = dtFiles;

    renderVideoFiles(dtFiles);
    updateVideoSizes(dtFiles);

    document.getElementById("fileProgressContainer").scrollIntoView({
        behavior: "smooth"
    });
});



// function updateProgressUI(safeId, pct, finished = false) {
//     const block = document.getElementById(`file-${safeId}`);
//     if (!block) return;

//     const fillEl = block.querySelector(".progress-fill");
//     const labelEl = block.querySelector(".progress-label");

//     const pctNum = Math.max(0, Math.min(100, Number(pct || 0)));
//     if (fillEl) fillEl.style.width = `${pctNum}%`;
//     if (labelEl) labelEl.textContent = `${pctNum}%`;

//     // opcjonalne style końcowe
//     if (finished) {
//         if (fillEl) fillEl.style.background = "linear-gradient(90deg,#4caf50,#8bc34a)";
//     }
// }

function updateProgressUI(safeId, pct, finished = false) {
    const block = document.getElementById(`file-${safeId}`);
    if (!block) return;

    const fillEl = block.querySelector(".progress-fill");
    const labelEl = block.querySelector(".progress-label");

    const pctNum = Math.max(0, Math.min(100, Number(pct || 0)));
    
    if (fillEl) {
        fillEl.style.width = `${pctNum}%`;
        
        // Opcjonalna zmiana koloru w zależności od postępu dla wideo
        if (pctNum < 100) {
            block.classList.add("active");
        }
    }
    
    if (labelEl) {
        labelEl.textContent = `${Math.floor(pctNum)}%`;
    }

    if (finished || pctNum === 100) {
        block.classList.remove("active");
        block.classList.add("success");
    }
}


function updateErrorUI(safeId, errorMsg = "Błąd") {
    const block = document.getElementById(`file-${safeId}`);
    if (!block) return;

    const labelEl = block.querySelector(".progress-label");
    if (labelEl) labelEl.textContent = errorMsg;

    block.classList.add("file-error");
}


// =========================
// WARNING MODAL
// =========================
// function showVideoWarning(i18nKey, dynamicText = "") {
//     console.log("showVideoWarning called with:", { i18nKey, dynamicText });
//     document.getElementById("status").innerHTML =
//             `<p class="neon-text" i18n="${i18nKey}">${dynamicText}</p>`;
// }

function showVideoWarning(i18nKey, dynamicText = "") {
    const modal = document.getElementById("warningModal");
    const msgVideoTooMany = document.getElementById("warningVideoTooMany");
    const msgVideoTooBig = document.getElementById("warningVideoTooBig");
    const msgInvalidFileType = document.getElementById("warningInvalidFileType");
    const btn = document.getElementById("warningClose");

    // Reset widoczności
    msgVideoTooMany.classList.add("hidden");
    msgVideoTooBig.classList.add("hidden");
    msgInvalidFileType.classList.add("hidden");

    // Wybór komunikatu
    if (i18nKey === "warning_video_too_many_files") {
        msgVideoTooMany.classList.remove("hidden");
    }

    if (i18nKey === "warning_video_file_too_big") {
        msgVideoTooBig.classList.remove("hidden");

        // dynamiczny tekst (np. nazwa pliku)
        if (dynamicText) {
            msgVideoTooBig.textContent = dynamicText;
        }
    }

    if (i18nKey === "warning_invalid_file_type") {
        msgInvalidFileType.classList.remove("hidden");

        // dynamiczny tekst (np. nazwa pliku)
        if (dynamicText) {
            msgInvalidFileType.textContent = dynamicText;
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


async function uploadSelectedToDrive() {
    const selectedCheckboxes = document.querySelectorAll(".file-select:checked");
    const taskIds = [];
    
    selectedCheckboxes.forEach(cb => {
        const filename = cb.getAttribute("data-filename");
        if (finishedTasks[filename]) taskIds.push(finishedTasks[filename]);
    });

    if (taskIds.length === 0) {
        alert("Select finished files first!");
        return;
    }

    const btn = document.getElementById("googleDriveBtn");
    btn.disabled = true;
    btn.innerText = "Uploading...";

    try {
        const res = await fetch("/compress/upload-to-drive", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(taskIds)
        });

        console.log("uploadSelectedToDrive", res)

        if (res.status === 401) {
            window.location.href = "/auth/google-drive";
            return;
        }

        const data = await res.json();
        alert(`Successfully uploaded ${data.uploaded.length} files to Google Drive!`);
    } catch (e) {
        alert("Upload failed.");
    } finally {
        btn.disabled = false;
        await updateDriveButton();
    }
}

// Wywołaj sprawdzenie statusu przy ładowaniu
checkDriveStatus();



// ***************************************** NEW ***************************************** //

// app/static/js/video.js
let currentMode = "video";
const finishedVideoTasks = {};
const MAX_PARALLEL_VIDEO = 3;
let isDriveConnected = false;

// ===============================
// INITIALIZE
// ===============================
document.addEventListener("DOMContentLoaded", async () => {
    await checkDriveStatus();
});

async function checkDriveStatus() {
    const res = await fetch("/auth/google-drive/status");
    const data = await res.json();
    isDriveConnected = data.connected;
    updateDriveButton();
}

function updateDriveButton() {
    const btn = document.getElementById("googleDriveBtn");
    if (!btn) return;
    if (isDriveConnected) {
        btn.innerHTML = "<span>Upload selected to Drive</span>";
        btn.onclick = uploadSelectedToDrive;
    } else {
        btn.innerHTML = "<span>Connect Google Drive</span>";
        btn.onclick = () => window.location.href = "/auth/google-drive";
    }
}

// ===============================
// RENDER & SIZE
// ===============================
function renderVideoFiles(files) {

    if (files.length) videoCompBtn.classList.remove("hidden");

    const container = document.getElementById("fileProgressContainer");
    container.innerHTML = "";
    for (let f of files) {
        const safeId = createSafeId(f.name);
        const url = URL.createObjectURL(f);
        container.innerHTML += `
            <div class="file-block" id="file-${safeId}">
                <input type="checkbox" class="file-select-video file-select" data-filename="${f.name}" id="check-${safeId}">
                <video class="file-thumb" src="${url}" muted preload="metadata"></video>
                <div class="file-size" id="size-${safeId}"></div>
                <div class="file-b">
                    <div class="file-name">${f.name}</div>
                    <div class="progress-wrapper">
                        <div class="progress-bar">
                            <!-- DODANO KLASĘ neon-fill -->
                            <div class="progress-fill neon-fill" style="width: 0%"></div>
                        </div>
                        <div class="progress-label">0%</div>
                    </div>
                </div>
            </div>
        `;
    }
}

function createSafeId(name) {
    return btoa(unescape(encodeURIComponent(name))).replace(/=/g, "");
}



// ===============================
// SUBMIT & QUEUE
// ===============================
document.getElementById("uploadForm").onsubmit = async (e) => {

    // submitter to przycisk, który wywołał submit
    const submitter = e.submitter || document.activeElement;

    if (!submitter) {
        // fallback: nic nie rób
        e.preventDefault();
        return;
    }


    if (submitter.id === "startImagesBtn") {

        e.preventDefault();
        const files = Array.from(
            document.getElementById("files").files
        );

        if (!files.length) return;

        document.getElementById("status").innerHTML =
            `<p class="neon-text">Processing ${files.length} files...</p>`;

        
        await processQueue(files); //from batch.js
        return;
    }




    if (submitter.id === "startVideosBtn") {
        e.preventDefault();
        const files_video = Array.from(document.getElementById("files_video").files);
        if (!files_video.length) return;

        const files = Array.from(
            document.getElementById("files").files
        );

        document.getElementById("status").innerHTML = `<p class="neon-text">Processing ${files_video.length} videos...</p>`;
        

        renderVideoFiles(files_video);
        updateVideoSizes(files_video);
        // Przetwarzanie równoległe (limit 3)
        const queue = [...files_video];
        const workers = Array(MAX_PARALLEL_VIDEO).fill(null).map(() => videoWorker(queue));
        await Promise.all(workers);
    }
    
};

async function videoWorker(queue) {
    while (queue.length > 0) {
        const file = queue.shift();
        if (!file.type.startsWith("video/")) {
            showVideoWarning("warning_invalid_file_type", `„${file.name}”`);    
            return;
        }
        if (file) await processSingleVideo(file);
    }
}

async function processSingleVideo(file) {
    const safeId = createSafeId(file.name);
    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch("/compress/video", { method: "POST", body: formData });
        const data = await res.json();
        await pollVideoStatus(data.task_id, file.name, file.size);
    } catch (err) {
        updateErrorUI(safeId);
    }
}

// ===============================
// STATUS POLLING
// ===============================
async function pollVideoStatus(taskId, filename, originalSize) {
    const safeId = createSafeId(filename);
    return new Promise((resolve) => {
        const interval = setInterval(async () => {
            const res = await fetch(`/compress/video/status/${taskId}`);
            const data = await res.json();
            console.log(`Status for ${filename}:`, data);

            updateProgressUI(safeId, data.progress || 0);

            if (data.status === "done") {
                clearInterval(interval);
                const compressedBytes = data.compressed_size;
                const reduction = ((originalSize - compressedBytes) / originalSize) * 100;
                
                const sizeDiv = document.getElementById(`size-${safeId}`);
                sizeDiv.innerHTML = `
                    <span class="original-size">${(originalSize/1024/1024).toFixed(2)} MB</span> → 
                    <span class="reduction-pct">-${reduction.toFixed(0)}%</span> | 
                    <span class="compressed-size">${(compressedBytes/1024/1024).toFixed(2)} MB</span>
                `;

                showDownloadButton(safeId, taskId, filename);
                finishedVideoTasks[filename] = taskId;
                updateProgressUI(safeId, 100, true);
                checkGlobalVideoCompletion();
                resolve();
            }
            if (data.status === "error") {
                clearInterval(interval);
                updateErrorUI(safeId, data.error);
                resolve();
            }
        }, 2000);
    });
}

function showDownloadButton(safeId, taskId, filename) {
    const block = document.getElementById(`file-${safeId}`);
    const actionArea = block.querySelector(".file-b");
    const dlBtn = document.createElement("a");
    dlBtn.href = `/compress/video/download/${taskId}`;
    dlBtn.className = "btn-mini";
    dlBtn.innerHTML = "Download";
    dlBtn.download = filename;
    actionArea.prepend(dlBtn);
}

// ===============================
// COMPLETION (ZIP & DRIVE)
// ===============================

// Helper: zwraca lub inicjalizuje kontener akcji (actions)
function getActionsContainer() {
    let actionsEl = actions;
    if (!actionsEl) {
        // jeśli nie ma w DOM, tworzymy i dodajemy w status (bez stylów)
        actionsEl = document.createElement("div");
        actionsEl.id = "drive-actions";
        actionsEl.className = "drive-actions";
        // możesz dodać tu checkbox/select all itp. jeśli potrzebujesz
    }
    return actionsEl;
}

// Helper: tworzy przycisk upload do Drive (nowy element, nie przenosimy istniejącego)
function createGoogleDriveUploadButton() {
    updateDriveButton();
    const btn = document.createElement("button");
    btn.id = "googleDriveBtnUpload";
    btn.className = "success-btn";
    btn.innerHTML = `<img src="/static/icons/gdup.png" alt="Google Drive" width="40" height="40">`;
    btn.style.marginLeft = "10px";
    btn.onclick = uploadVideosToDrive; // upewnij się, że ta funkcja istnieje
    return btn;
}



// ===============================
// COMPLETION (ZIP & DRIVE)
// ===============================

// Główna funkcja
function checkGlobalVideoCompletion() {
    const totalFiles = (document.getElementById("files_video") || {}).files?.length || 0;
    const completed = Object.keys(finishedVideoTasks || {}).length;

    console.log("checkGlobalVideoCompletion:", { totalFiles, completed, finishedVideoTasks, isDriveConnected });

    if (totalFiles === 0) return;

    if (totalFiles === completed) {
        const statusDiv = document.getElementById("status");
        if (!statusDiv) {
            console.warn("Brak elementu #status w DOM");
            return;
        }

        // Wyczyść status i przygotuj miejsce
        statusDiv.innerHTML = "";

        // Przycisk ZIP
        const zipBtn = document.createElement("button");
        zipBtn.className = "btn success-btn";
        zipBtn.innerHTML = "Download All as ZIP";
        zipBtn.onclick = () => {
            const query = Object.values(finishedVideoTasks).join(",");
            window.location.href = `/compress/video/download-multi?tasks=${encodeURIComponent(query)}`;
        };
        statusDiv.appendChild(zipBtn);

        // Akcje (checkboxy, upload) - upewnij się, że są widoczne
        const actionsEl = getActionsContainer();
        actionsEl.classList.remove("hidden");
        statusDiv.appendChild(actionsEl);

        // Przycisk Drive - tylko jeśli połączenie jest aktywne
        if (typeof isDriveConnected !== "undefined" && isDriveConnected) {
            // Tworzymy nowy przycisk (nie przenosimy istniejącego elementu z DOM)
            const driveBtn = createGoogleDriveUploadButton();
            statusDiv.appendChild(driveBtn);
        } else {
            console.log("Drive not connected or isDriveConnected is false");
        }
    }
}


async function uploadVideosToDrive() {

    const selected = Array.from(document.querySelectorAll(".file-select:checked"))
        .map(cb => finishedVideoTasks[cb.getAttribute("data-filename")]);
    
    if (!selected.length) return alert("Select videos first!");

    const btn = document.getElementById("googleDriveBtnUpload");
    btn.disabled = true;
    btn.innerText = "Uploading...";   

    try {
        const res = await fetch("/compress/video/upload-to-drive", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(selected)
        });
        const data = await res.json();
        console.log("uploadVideosToDrive response:", data);
        alert(`Uploaded ${data.uploaded.length} videos to Drive!`);
        if (data.uploaded.length > 0) {
            btn.disabled = false;
            btn.innerText = "Reconnect to Drive and Try Again";
            btn.onclick = () => window.location.href = "/auth/google-drive";
            // btn.onclick = connectToDrive;
            // return;
        } 
        if (data.uploaded.length > 0) {
            btn.innerText = "Uploaded!";
        }
    } catch (e) { 
        console.error("Error uploading videos to Drive:", e);
        alert("Upload failed.");
        btn.disabled = false;
        btn.innerText = "Upload to Drive";
    }
}


async function connectToDrive() {
    const btn = document.getElementById("googleDriveBtn");
    btn.disabled = true;
    btn.innerText = "Connecting...";
    try {
        const res = await fetch("/auth/google-drive");
        if (res.status === 200) {
            btn.innerText = "Connected! Upload to Drive aganin.";
        } else {
            btn.innerText = "Failed to connect. Try again.";
        }
    } catch (e) {
        btn.innerText = "Error connecting. Try again later.";
    }   
}