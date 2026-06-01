let currentMode = "compress";

const finishedTasks = {};
const MAX_PARALLEL = 4;

// =========================
// MODE
// =========================

document.getElementById("convertWebpBtn").onclick = () => {
    currentMode = "webp";
    document.getElementById("uploadForm").requestSubmit();
};

// =========================
// RENDER FILES
// =========================

function renderFiles(files) {

    const container = document.getElementById("fileProgressContainer");

    container.innerHTML = "";

    for (let f of files) {

        const safeId = createSafeId(f.name);

        const url = f.type.startsWith("image/")
            ? URL.createObjectURL(f)
            : null;

        container.innerHTML += `
            <div class="file-block" id="file-${safeId}">

                ${url
                    ? `<img class="file-thumb" src="${url}" alt="">`
                    : ""
                }

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

    const files = e.target.files;

    renderFiles(files);

    updateFileSizes(files);
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

//     const dtFiles = e.dataTransfer.files;

//     document.getElementById("files").files = dtFiles;

//     renderFiles(dtFiles);

//     updateFileSizes(dtFiles);

//     document.getElementById("fileProgressContainer")
//         .scrollIntoView({
//             behavior: "smooth"
//         });
// });


dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    e.stopPropagation();

    const dtFiles = e.dataTransfer.files;

    // --- LIMIT: max 20 plików ---
    if (dtFiles.length > 20) {
        showWarning("warning_too_many_files", `(${dtFiles.length} files)`);
        return;
    }

    // --- LIMIT: max 7 MB ---
    for (const f of dtFiles) {
        const sizeMB = f.size / 1024 / 1024;
        if (sizeMB > 7) {
            showWarning("warning_file_too_big", `„${f.name}” > 7 MB`);
            return;
        }
    }

    document.getElementById("files").files = dtFiles;

    renderFiles(dtFiles);
    updateFileSizes(dtFiles);

    document.getElementById("fileProgressContainer").scrollIntoView({
        behavior: "smooth"
    });
});




// =========================
// SUBMIT
// =========================

document.getElementById("uploadForm").onsubmit = async (e) => {

    e.preventDefault();

    const files = Array.from(
        document.getElementById("files").files
    );

    if (!files.length) return;

    document.getElementById("status").innerHTML =
        `<p class="neon-text">Processing ${files.length} files...</p>`;

    await processQueue(files);
};

// =========================
// CONCURRENCY QUEUE
// =========================

async function processQueue(files) {

    const queue = [...files];

    const workers = [];

    for (let i = 0; i < MAX_PARALLEL; i++) {
        workers.push(worker(queue));
    }

    await Promise.all(workers);
}

async function worker(queue) {

    while (queue.length > 0) {

        const file = queue.shift();

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
            body: formData
        });

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
                    data.progress || 0
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

                    // sizeDiv.innerHTML = `
                    //     <span class="reduction-pct">
                    //         -${reduction.toFixed(0)}%
                    //     </span>
                    //     |
                    //     ${(compressedBytes / 1024 / 1024).toFixed(2)} MB
                    // `;

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

                    checkGlobalCompletion();

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

// function showDownloadButton(
//     safeId,
//     taskId,
//     filename
// ) {

//     const block =
//         document.getElementById(`file-${safeId}`);

//     const actionArea =
//         block.querySelector(".file-b");

//     const dlBtn = document.createElement("a");

//     dlBtn.href = `/compress/file/${taskId}`;

//     dlBtn.className = "btn-mini";

//     dlBtn.innerHTML = "Download";

//     dlBtn.download = filename;

//     actionArea.prepend(dlBtn);
// }

function showDownloadButton(safeId, taskId, filename) {
    const block = document.getElementById(`file-${safeId}`);
    const actionArea = block.querySelector(".file-b");

    const dlBtn = document.createElement("button");
    dlBtn.className = "btn-mini";
    dlBtn.innerHTML = "Download";

    dlBtn.onclick = () => {
        const url = `/compress/file/${taskId}`;
        shareFileFromUrl(url, filename);
    };

    actionArea.prepend(dlBtn);
}



// =========================
// SHARE (Web Share API with fallback) for mobile
// =========================
async function shareFileFromUrl(url, filename) {
    try {
        const res = await fetch(url);
        const blob = await res.blob();
        const file = new File([blob], filename, { type: blob.type });

        if (navigator.canShare && navigator.canShare({ files: [file] })) {
            await navigator.share({
                files: [file],
                title: "Skompresowany plik",
                text: "Twoje zdjęcie jest gotowe"
            });
        } else {
            // fallback: normalne pobieranie
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            a.click();
        }
    } catch (err) {
        console.error("Share failed:", err);
    }
}


// =========================
// ZIP
// =========================

function checkGlobalCompletion() {

    const totalFiles =
        document.getElementById("files").files.length;

    const completed =
        Object.keys(finishedTasks).length;

    if (totalFiles !== completed) return;

    const statusDiv =
        document.getElementById("status");

    const zipBtn = document.createElement("button");

    zipBtn.className = "btn success-btn";

    zipBtn.innerHTML = "Download All as ZIP";

    zipBtn.onclick = async () => {

        const ids = Object.values(finishedTasks);

        const query = ids.join(",");

        window.location.href =
            `/compress/download-multi?tasks=${query}`;
    };

    statusDiv.innerHTML = "";

    statusDiv.appendChild(zipBtn);
}

// =========================
// UI
// =========================

function updateProgressUI(
    safeId,
    value,
    isFinal = false
) {

    const block =
        document.getElementById(`file-${safeId}`);

    if (!block) return;

    const fill =
        block.querySelector(".progress-fill");

    const label =
        block.querySelector(".progress-label");

    fill.style.width = value + "%";

    label.textContent =
        Math.floor(value) + "%";

    if (isFinal) {
        block.classList.add("success");
    }
}

function updateErrorUI(safeId) {

    const block =
        document.getElementById(`file-${safeId}`);

    if (!block) return;

    block.classList.add("error");
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





// function connectGoogleDrive() {
//     window.location.href = "/auth/google-drive";
// }


// function openPicker(oauthToken) {
//     gapi.load("picker", () => {
//         const picker = new google.picker.PickerBuilder()
//             .addView(google.picker.ViewId.DOCS_IMAGES)
//             .setOAuthToken(oauthToken)
//             .setDeveloperKey("TWÓJ_API_KEY")
//             .setCallback(pickerCallback)
//             .build();
//         picker.setVisible(true);
//     });
// }
