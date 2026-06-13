let currentMode = "compress";

const finishedTasks = {};
const MAX_PARALLEL = 4;

let isDriveConnected = false;
const driveActions = document.getElementById("drive-actions");
const googleDriveBtn = document.getElementById("googleDriveBtn");
let actions = null;

const imgCompBtn = document.getElementById("startImagesBtn");
let dropFotofilesProcessed = [];

document.addEventListener("DOMContentLoaded", () => {
    actions = document.getElementById("drive-actions");
});

// =========================
// CHECK GOOGLE DRIVE STATUS
// =========================

async function checkDriveStatus() {
    const res = await fetch("/auth/google-drive/status");
    const data = await res.json();
    console.log('checkDriveStatus---', res)
    isDriveConnected = data.connected;
    await updateDriveButton();
}

async function updateDriveButton() {
    const btn = document.getElementById("googleDriveBtn");
    // const text = document.getElementById("driveBtnText");
    
    if (isDriveConnected) {
        // text.innerText = "Upload selected to Drive";
        // actions.classList.remove("hidden");
        btn.classList.add("hidden");
        // btn.onclick = uploadSelectedToDrive;
    } else {
        // text.innerText = "Connect Google Drive";
        // actions.classList.remove("hidden");
        btn.classList.remove("hidden");
        btn.onclick = () => window.location.href = "/auth/google-drive";
    }
}

// =========================
// MODE
// =========================

// document.getElementById("convertWebpBtn").onclick = () => {
//     currentMode = "webp";
//     document.getElementById("uploadForm").requestSubmit();
// };

// =========================
// RENDER FILES
// =========================

function renderFiles(files) {

    dropFotofilesProcessed = files

    if (files.length) imgCompBtn.classList.remove("hidden");

    const container = document.getElementById("fileProgressContainer");

    container.innerHTML = "";

    for (let f of files) {

        if (!f.type.startsWith("image/")) {
            showWarning("warning_invalid_file_type", `„${f.name}”`);
            return;
        }

        console.log('renderFiles-----', f)

        const safeId = createSafeId(f.name);

        const url = f.type.startsWith("image/")
            ? URL.createObjectURL(f)
            : null;

        container.innerHTML += `
            <div class="file-block" id="file-${safeId}">
                <input type="checkbox" class="file-select" data-filename="${f.name}" id="check-${safeId}">
                ${url ? `<img class="file-thumb" src="${url}" alt="">` : ""}
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
    return btoa(unescape(encodeURIComponent(name)))
        .replace(/=/g, "");
}

function updateFileSizes(files) {

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

document.getElementById("files").onchange = (e) => {

    // const files = e.target.files;

    const dtFiles = e.target.files;
    console.log('Drop --- Processing dtFiles:', dtFiles);

    // --- LIMIT: max 20 plików ---
    if (dtFiles.length > 20 && !window.USER.is_admin) {
        showWarning("warning_too_many_files", `(${dtFiles.length} files)`);
        return;
    }

    // --- LIMIT: max 7 MB ---
    for (const f of dtFiles) {
        console.log('Drop --- Processing file:', f);
        console.log(window.USER.email);
        if (f.type.startsWith("image/")) {
            const sizeMB = f.size / 1024 / 1024;
            if (sizeMB > 7 && !window.USER.is_admin) {
                showWarning("warning_file_too_big", `„${f.name}” > 7 MB`);
                return;
            }
        }
    }

    renderFiles(dtFiles);

    updateFileSizes(dtFiles);
};

// =========================
// DROP ZONE
// =========================

const dropZone = document.getElementById("dropZone");

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




// dropZone.addEventListener("drop", (e) => {
//     e.preventDefault();
//     e.stopPropagation();

//     const closeBtn = document.getElementById("warningClose");

//     const dtFiles = e.dataTransfer.files;
//     console.log('Drop --- Processing dtFiles:', dtFiles);

    // // --- LIMIT: max 7 MB ---
    // for (const f of dtFiles) {
    //     console.log('Drop --- Processing file:', f);
    //     if (f.type.startsWith("image/")) {

    //         // --- LIMIT: max 20 plików ---
    //         if (dtFiles.length > 20) {
    //             showWarning("warning_too_many_files", `(${dtFiles.length} files)`);
    //             closeBtn.addEventListener("click", () => {
    //                 window.location.href = "/";
    //             });
    //             return;
    //         }

    //         const sizeMB = f.size / 1024 / 1024;
    //         if (sizeMB > 7) {
    //             showWarning("warning_file_too_big", `„${f.name}” > 7 MB`);
    //             closeBtn.addEventListener("click", () => {
    //                 window.location.href = "/";
    //             });
    //             return;
    //         }
    //     }
    // }

    // document.getElementById("files").files = dtFiles;

    // renderFiles(dtFiles);
    // updateFileSizes(dtFiles);

    // document.getElementById("fileProgressContainer").scrollIntoView({
    //     behavior: "smooth"
    // });
// });




// =========================
// SUBMIT is in video.js
// =========================


// =========================
// CONCURRENCY QUEUE
// =========================

async function processQueue(files) {

    const queue = [...files];

    console.log("processQueue-files", files)
    console.log("processQueue queue", queue)

    const workers = [];

    for (let i = 0; i < MAX_PARALLEL; i++) {
        workers.push(worker(queue));
    }

    await Promise.all(workers);

    checkGlobalCompletion();
}

async function worker(queue) {

    while (queue.length > 0) {

        const file = queue.shift();

        if (!file.type.startsWith("image/")) {
            console.warn(`Skipping unsupported file type: ${file.name}`);
            showWarning("warning_invalid_file_type", `„${file.name}”`);
            return;
        }

        if (!file) return;

        await processSingleFile(file);
    }
}

// =========================
// SINGLE FILE
// =========================

async function processSingleFile(file) {

    const filename = file.name;

    const safeId = createSafeId(filename);

    const formData = new FormData();

    formData.append("file", file);

    const endpoint =
        currentMode === "webp"
            ? "/compress/batch-webp"
            : "/compress/batch";

    try {

        const res = await fetch(endpoint, {
            method: "POST",
            body: formData,
        });

        if (!checkAuth(res)) {
            window.location.href = "/login";
        };

        const data = await res.json();

        await checkSingleFileStatus(
            data.task_id,
            filename,
            file.size
        );

    } catch (err) {

        console.error(err);

        updateErrorUI(safeId);
    }
}

// =========================
// STATUS POLLING
// =========================

async function checkSingleFileStatus(
    taskId,
    filename,
    originalSize
) {

    const safeId = createSafeId(filename);

    return new Promise((resolve) => {

        const interval = setInterval(async () => {

            try {

                const res = await fetch(
                    `/compress/status/${taskId}`
                );

                const data = await res.json();

                updateProgressUI(
                    safeId,
                    data.progress || 0,
                    false
                );

                if (data.status === "done") {

                    clearInterval(interval);

                    const compressedBytes =
                        data.compressed_size;

                    const reduction =
                        (
                            (
                                originalSize -
                                compressedBytes
                            ) /
                            originalSize
                        ) * 100;

                    const sizeDiv =
                        document.getElementById(
                            `size-${safeId}`
                        );

                    const originalMB = (originalSize / 1024 / 1024).toFixed(2); //+
                    const compressedMB = (compressedBytes / 1024 / 1024).toFixed(2);//+

                    sizeDiv.innerHTML = `
                        <span class="original-size">${originalMB} MB</span>
                        →
                        <span class="reduction-pct">-${reduction.toFixed(0)}%</span>
                        |
                        <span class="compressed-size">${compressedMB} MB</span>
                    `;

                    showDownloadButton(
                        safeId,
                        taskId,
                        filename
                    );

                    finishedTasks[filename] = taskId;

                    updateProgressUI(
                        safeId,
                        100,
                        true
                    );

                    // checkGlobalCompletion();

                    resolve();
                }

            } catch (err) {

                console.error(err);

                clearInterval(interval);

                updateErrorUI(safeId);

                resolve();
            }

        }, 2000);
    });
}

// =========================
// DOWNLOAD BUTTON
// =========================

function showDownloadButton(
    safeId,
    taskId,
    filename
) {

    const block =
        document.getElementById(`file-${safeId}`);

    const actionArea =
        block.querySelector(".file-b");

    const dlBtn = document.createElement("a");

    dlBtn.href = `/compress/file/${taskId}`;

    dlBtn.className = "btn-mini";

    // dlBtn.innerHTML = "Download";
    dlBtn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 3v12" stroke="#141414" stroke-width="2" stroke-linecap="round"/>
        <path d="M6 9l6 6 6-6" stroke="#141414" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M4 21h16" stroke="#141414" stroke-width="2" stroke-linecap="round"/>
        </svg>
        `;

    dlBtn.download = filename;

    actionArea.prepend(dlBtn);
}

// =========================
// ZIP
// =========================

function checkGlobalCompletion() {

    console.log('checkGlobalCompletion---actions', actions)

    if (actions) actions.classList.remove("hidden");

    const totalFiles =
        document.getElementById("files").files.length;
    console.log('checkGlobalCompletion---totalFiles', totalFiles)

    const completed =
        Object.keys(finishedTasks).length;
    console.log('checkGlobalCompletion---completed', completed)

    if (totalFiles !== completed) {
        console.log('checkGlobalCompletion---totalFiles !== completed')
        if ( dropFotofilesProcessed.length > 0 ) {
            createActionsBtns();
        }
        return;
    };

    createActionsBtns();

}

function createActionsBtns () {

    const statusDiv =
        document.getElementById("status");
    console.log('checkGlobalCompletion---statusDiv', statusDiv)

    const zipBtn = document.createElement("button");

    zipBtn.className = "btn success-btn";

    zipBtn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 3v12" stroke="#141414" stroke-width="2" stroke-linecap="round"/>
        <path d="M6 9l6 6 6-6" stroke="#141414" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M4 21h16" stroke="#141414" stroke-width="2" stroke-linecap="round"/>
        </svg> ZIP
        `;


    zipBtn.onclick = async () => {

        if (!checkAuth(res)) {
            window.location.href = "/login";
        };

        const ids = Object.values(finishedTasks);

        const query = ids.join(",");

        window.location.href =
            `/compress/download-multi?tasks=${query}`;
    };

    statusDiv.innerHTML = "";
    console.log('checkGlobalCompletion---statusDiv after', statusDiv)

    statusDiv.appendChild(actions);
    statusDiv.appendChild(zipBtn);
    const googleDriveBtnUpload = document.getElementById("googleDriveBtnUpload"); 
    googleDriveBtnUpload.onclick = uploadSelectedToDrive;
    // console.log('checkGlobalCompletion - actions after', actions)
    // console.log('checkGlobalCompletion - statusDiv', statusDiv)

}

// =========================
// UI
// =========================

// function updateProgressUI(
//     safeId,
//     value,
//     isFinal = false
// ) {

//     const block =
//         document.getElementById(`file-${safeId}`);

//     if (!block) return;

//     const fill =
//         block.querySelector(".progress-fill");

//     const label =
//         block.querySelector(".progress-label");

//     fill.style.width = value + "%";

//     label.textContent =
//         Math.floor(value) + "%";

//     if (isFinal) {
//         block.classList.add("success");
//     }
// }

function updateProgressUI(safeId, value, isFinal = false) {
    const block = document.getElementById(`file-${safeId}`);
    if (!block) return;

    const fill = block.querySelector(".progress-fill");
    const label = block.querySelector(".progress-label");

    if (fill) {
        fill.style.width = value + "%";
    }
    if (label) {
        label.textContent = Math.floor(value) + "%";
    }

    if (value > 0 && value < 100) {
        block.classList.add("active"); // Pulsowanie neonu podczas pracy
    }

    if (isFinal || value === 100) {
        block.classList.remove("active");
        block.classList.add("success"); // Flash na koniec
    }
}

function updateErrorUI(safeId) {

    const block =
        document.getElementById(`file-${safeId}`);

    if (!block) return;

    block.classList.add("error");
}




// =========================
// UPLOAD TO GOOGLE DRIVE
// =========================

// Obsługa "Wybierz wszystkie"
document.getElementById("selectAll").onchange = (e) => {
    document.querySelectorAll(".file-select").forEach(cb => cb.checked = e.target.checked);
};

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

    const btn = document.getElementById("googleDriveBtnUpload");
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
            // window.location.href = "/auth/google-drive";
            // return;
            btn.disabled = false;
            btn.innerText = "Reconnect to Drive and Try Again";
            btn.onclick = () => window.location.href = "/auth/google-drive";
            return
        }

        const data = await res.json();
        // alert(`Successfully uploaded ${data.uploaded.length} files to Google Drive!`);
        btn.innerText = "Upload completed";
    } catch (e) {
        alert("Upload failed.");
    } finally {
        btn.disabled = false;
        await updateDriveButton();
    }
}

// Wywołaj sprawdzenie statusu przy ładowaniu
checkDriveStatus();

// async function connectToDrive() {
//     const btn = document.getElementById("googleDriveBtn");
//     btn.disabled = true;
//     btn.innerText = "Connecting...";
//     try {
//         const res = await fetch("/auth/google-drive");
//         if (res.status === 200) {
//             btn.innerText = "Connected! Upload to Drive aganin.";
//         } else {
//             btn.innerText = "Failed to connect. Try again.";
//         }
//     } catch (e) {
//         btn.innerText = "Error connecting. Try again later.";
//     }   
// }

// =========================
// WARNING MODAL
// =========================
function showWarning(i18nKey, dynamicText = "") {
    const modal = document.getElementById("warningModal");
    const msgTooMany = document.getElementById("warningTooMany");
    const msgTooBig = document.getElementById("warningTooBig");
    const msgInvalidFileType = document.getElementById("warningInvalidFileType");
    const btn = document.getElementById("warningClose");

    // Reset widoczności
    msgTooMany.classList.add("hidden");
    msgTooBig.classList.add("hidden");
    msgInvalidFileType.classList.add("hidden");

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


window.processQueue = processQueue;
window.uploadSelectedToDrive = uploadSelectedToDrive;
window.showWarning = showWarning;
window.updateDriveButton = updateDriveButton;
window.actions = actions;
window.isDriveConnected = isDriveConnected;
window.renderFiles = renderFiles;
window.updateFileSizes = updateFileSizes;