// let currentMode = "compress"; // or "webp"

// document.getElementById("convertWebpBtn").onclick = () => {
//     currentMode = "webp";
//     document.getElementById("uploadForm").requestSubmit();
// };


// // --- HELPERS ---
// function renderFiles(files) {
//     const container = document.getElementById("fileProgressContainer");
//     container.innerHTML = "";

//     for (let f of files) {

//         const url = f.type.startsWith("image/") ? URL.createObjectURL(f) : null;

//         container.innerHTML += `
//             <div class="file-block" id="file-${f.name}">
//                 ${url ? `<img class="file-thumb" src="${url}" alt="">` : ""}
//                 <div class="file-size" id="size-${f.name}"></div>

//                 <div class="file-b">
//                     <div class="file-name">${f.name}</div>

//                     <div class="progress-wrapper">

//                         <div class="progress-bar neon-bar" data-filename="${f.name}">
//                             <div class="progress-fill neon-fill" style="width:0%"></div>
//                         </div>

//                         <div class="progress-label">0%</div>
//                     </div>

//                 </div>
//             </div>
//         `;
//     }
// }

// // --- INPUT CHANGE ---
// document.getElementById("files").onchange = (e) => {
//     const files = e.target.files;
//     renderFiles(files);
//     updateFileSizes(files)
// };

// function updateFileSizes(files) {
//     for (let f of files) {
//         const sizeMB = (f.size / 1024 / 1024).toFixed(2);
//         const el = document.getElementById(`size-${f.name}`);
//         if (el) el.textContent = `${sizeMB} MB`;
//     }
// }

// // DROP ZONE

// const dropZone = document.getElementById("dropZone");

// // zapobiegamy domyślnym zachowaniom
// ["dragenter", "dragover", "dragleave", "drop"].forEach(ev =>
//     dropZone.addEventListener(ev, (e) => {
//         e.preventDefault();
//         e.stopPropagation();
//     })
// );

// // efekt neon glow przy przeciąganiu
// ["dragenter", "dragover"].forEach(ev =>
//     dropZone.addEventListener(ev, () => dropZone.classList.add("dragover"))
// );

// ["dragleave", "drop"].forEach(ev =>
//     dropZone.addEventListener(ev, () => dropZone.classList.remove("dragover"))
// );

// // obsługa upuszczania plików
// dropZone.addEventListener("drop", (e) => {
//     const dtFiles = e.dataTransfer.files;
//     document.getElementById("files").files = dtFiles;
//     renderFiles(dtFiles); // Twoja funkcja generująca listę plików
// });

// dropZone.addEventListener("drop", (e) => {
//     const dtFiles = e.dataTransfer.files;
//     document.getElementById("files").files = dtFiles;
//     renderFiles(dtFiles);
//     updateFileSizes(dtFiles);

//     document.getElementById("fileProgressContainer").scrollIntoView({
//         behavior: "smooth"
//     });
// });



// // --- RIPPLE ON CLICK ---
// document.addEventListener("click", (e) => {
//     const bar = e.target.closest(".progress-bar");
//     if (!bar) return;

//     const rect = bar.getBoundingClientRect();
//     const ripple = document.createElement("span");
//     ripple.className = "ripple";
//     const size = Math.max(rect.width, rect.height);
//     ripple.style.width = ripple.style.height = size + "px";
//     ripple.style.left = (e.clientX - rect.left - size / 2) + "px";
//     ripple.style.top = (e.clientY - rect.top - size / 2) + "px";

//     bar.appendChild(ripple);
//     setTimeout(() => ripple.remove(), 600);
// });


// // --- FORM SUBMIT ---
// document.getElementById("uploadForm").onsubmit = async (e) => {
//     e.preventDefault();

//     const files = document.getElementById("files").files;
//     const formData = new FormData();

//     const statusDiv = document.getElementById("status");
//     statusDiv.innerHTML = "Starting...";

//     const localProgress = {};

//     for (let f of files) {
//         formData.append("files", f);
//         localProgress[f.name] = 0;
//     }

//     const endpoint = currentMode === "webp"
//         ? "/compress/batch-webp"
//         : "/compress/batch";

//     const res = await fetch(endpoint, {
//         method: "POST",
//         body: formData
//     });

//     // const res = await fetch("/compress/batch", {
//     //     method: "POST",
//     //     body: formData
//     // });

//     const data = await res.json();
//     const taskId = data.task_id;

//     startLocalProgress(localProgress);
//     checkStatus(taskId, localProgress);
// };


// // --- AUTO PROGRESS (to 90%) ---
// function startLocalProgress(localProgress) {
//     setInterval(() => {
//         for (const filename in localProgress) {
//             if (localProgress[filename] < 90) {
//                 localProgress[filename] += 1.5;
//                 updateProgressUI(filename, Math.floor(localProgress[filename]));
//             }
//         }
//     }, 500);
// }


// // --- POLLING BACKEND ---
// async function checkStatus(taskId, localProgress) {
//     const statusDiv = document.getElementById("status");

//     const interval = setInterval(async () => {
//         const res = await fetch(`/compress/status/${taskId}`);
//         const data = await res.json();

//         statusDiv.innerHTML = `
//             <p>Status: ${data.status}</p>
//             <p>Overall: ${data.progress}%</p>
//         `;

//         if (data.file_progress) {
//             for (const [filename, prog] of Object.entries(data.file_progress)) {
//                 if (prog > localProgress[filename]) {
//                     localProgress[filename] = prog;
//                     updateProgressUI(filename, prog);
//                 }
//             }
//         }


//         if (data.status === "done") {
//             clearInterval(interval);

//             for (const filename in localProgress) {
//                 updateProgressUI(filename, 100);

//                 const block = document.getElementById(`file-${filename}`);
//                 if (block) block.classList.remove("active");

//                 // rozmiar oryginalny
//                 const sizeDiv = document.getElementById(`size-${filename}`);
//                 const originalMB = parseFloat(sizeDiv.textContent);

//                 // rozmiar po kompresji z backendu
//                 const compressedBytes = data.compressed_sizes[filename];
//                 const compressedMB = (compressedBytes / 1024 / 1024).toFixed(2);

//                 const reduction = (((originalMB - compressedMB) / originalMB) * 100).toFixed(0);

//                 sizeDiv.textContent = `${originalMB} MB → ${compressedMB} MB (${reduction}% ↓)`;
//             }

//             // tylko jeden przycisk
//             statusDiv.innerHTML = `
//                 <a class="btn" href="/compress/download/${taskId}">Download ZIP</a>
//             `;
//         }

//     }, 500);
// }


// // --- UPDATE UI + SUCCESS FLASH ---
// function updateProgressUI(filename, value, isFinal = false) {
//     const block = document.getElementById(`file-${filename}`);
//     if (!block) return;

//     const fill = block.querySelector(".progress-fill");
//     const label = block.querySelector(".progress-label");

//     fill.style.width = value + "%";
//     label.textContent = value + "%";

//     if (value === 100 || isFinal) {
//         block.classList.add("success");
//     }
// }






// ---------------------------------------------
// GLOBAL MODE (compress | webp)
// ---------------------------------------------
let currentMode = "compress";
let localProgressInterval = null;

document.getElementById("convertWebpBtn").onclick = () => {
    currentMode = "webp";
    document.getElementById("uploadForm").requestSubmit();
};

document.getElementById("uploadForm").onsubmit = () => {
    currentMode = "compress";
};

// ---------------------------------------------
// RENDER FILES
// ---------------------------------------------
function renderFiles(files) {
    const container = document.getElementById("fileProgressContainer");
    container.innerHTML = "";

    for (let f of files) {
        const url = f.type.startsWith("image/") ? URL.createObjectURL(f) : null;

        container.innerHTML += `
            <div class="file-block" id="file-${f.name}">
                ${url ? `<img class="file-thumb" src="${url}" alt="">` : ""}

                <div class="file-b">
                    <div class="file-name">${f.name}</div>
                    <div class="file-size" id="size-${f.name}"></div>

                    <div class="progress-wrapper">
                        <div class="progress-bar neon-bar" data-filename="${f.name}">
                            <div class="progress-fill neon-fill" style="width:0%"></div>
                        </div>
                        <div class="progress-label">0%</div>
                    </div>
                </div>
            </div>
        `;
    }
}

// ---------------------------------------------
// ORIGINAL FILE SIZES
// ---------------------------------------------
function updateFileSizes(files) {
    for (let f of files) {
        const sizeMB = (f.size / 1024 / 1024).toFixed(2);
        const el = document.getElementById(`size-${f.name}`);
        if (el) el.textContent = `${sizeMB} MB`;
    }
}

// ---------------------------------------------
// INPUT CHANGE
// ---------------------------------------------
document.getElementById("files").onchange = (e) => {
    const files = e.target.files;
    renderFiles(files);
    updateFileSizes(files);
};

// ---------------------------------------------
// DROP ZONE
// ---------------------------------------------
const dropZone = document.getElementById("dropZone");

["dragenter", "dragover", "dragleave", "drop"].forEach(ev =>
    dropZone.addEventListener(ev, (e) => {
        e.preventDefault();
        e.stopPropagation();
    })
);

["dragenter", "dragover"].forEach(ev =>
    dropZone.addEventListener(ev, () => dropZone.classList.add("dragover"))
);

["dragleave", "drop"].forEach(ev =>
    dropZone.addEventListener(ev, () => dropZone.classList.remove("dragover"))
);

dropZone.addEventListener("drop", (e) => {
    const dtFiles = e.dataTransfer.files;
    document.getElementById("files").files = dtFiles;
    renderFiles(dtFiles);
    updateFileSizes(dtFiles);

    document.getElementById("fileProgressContainer").scrollIntoView({
        behavior: "smooth"
    });
});

// ---------------------------------------------
// RIPPLE EFFECT
// ---------------------------------------------
document.addEventListener("click", (e) => {
    const bar = e.target.closest(".progress-bar");
    if (!bar) return;

    const rect = bar.getBoundingClientRect();
    const ripple = document.createElement("span");
    ripple.className = "ripple";
    const size = Math.max(rect.width, rect.height);
    ripple.style.width = ripple.style.height = size + "px";
    ripple.style.left = (e.clientX - rect.left - size / 2) + "px";
    ripple.style.top = (e.clientY - rect.top - size / 2) + "px";

    bar.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
});

// ---------------------------------------------
// FORM SUBMIT
// ---------------------------------------------
document.getElementById("uploadForm").onsubmit = async (e) => {
    e.preventDefault();

    const files = document.getElementById("files").files;
    const formData = new FormData();

    const statusDiv = document.getElementById("status");
    statusDiv.innerHTML = "Starting...";

    const localProgress = {};

    for (let f of files) {
        formData.append("files", f);
        localProgress[f.name] = 0;
    }

    const endpoint = currentMode === "webp"
        ? "/compress/batch-webp"
        : "/compress/batch";

    const res = await fetch(endpoint, {
        method: "POST",
        body: formData
    });

    const data = await res.json();
    const taskId = data.task_id;

    startLocalProgress(localProgress);
    checkStatus(taskId, localProgress);
};

// ---------------------------------------------
// AUTO PROGRESS (to 90%)
// ---------------------------------------------
function startLocalProgress(localProgress) {
    
    // 🔥 start animacji muszli
    startShellSpin();


    localProgressInterval = setInterval(() => {
        for (const filename in localProgress) {
            if (localProgress[filename] < 90) {
                localProgress[filename] += 1.5;
                updateProgressUI(filename, Math.floor(localProgress[filename]));
            }
        }
    }, 500);
}

// ---------------------------------------------
// POLLING BACKEND
// ---------------------------------------------
async function checkStatus(taskId, localProgress) {
    const statusDiv = document.getElementById("status");

    const interval = setInterval(async () => {
        const res = await fetch(`/compress/status/${taskId}`);
        const data = await res.json();

        statusDiv.innerHTML = `
            <p>Status: ${data.status}</p>
            <p>Overall: ${data.progress}%</p>
        `;

        if (data.file_progress) {
            for (const [filename, prog] of Object.entries(data.file_progress)) {
                updateProgressUI(filename, prog);
            }
        }

        if (data.status === "done") {
            clearInterval(localProgressInterval);

            // Wyłączamy animację muszli
            stopShellSpin();

            for (const originalName in data.name_map) {
                const newName = data.name_map[originalName];

                updateProgressUI(originalName, 100);

                const block = document.getElementById(`file-${originalName}`);
                if (block) block.classList.remove("active");

                const sizeDiv = document.getElementById(`size-${originalName}`);
                const originalMB = parseFloat(sizeDiv.textContent);

                const compressedBytes = data.compressed_sizes[newName];
                const compressedMB = (compressedBytes / 1024 / 1024).toFixed(2);

                const reduction = (((originalMB - compressedMB) / originalMB) * 100).toFixed(0);

                sizeDiv.textContent = `${originalMB} MB → ${compressedMB} MB (${reduction}% ↓)`;
            }

            statusDiv.innerHTML = `
                <a class="btn" href="/compress/download/${taskId}">Download ZIP</a>
            `;
        }

    }, 500);
}

// ---------------------------------------------
// UPDATE UI + SUCCESS FLASH
// ---------------------------------------------
function updateProgressUI(filename, value, isFinal = false) {
    const block = document.getElementById(`file-${filename}`);
    if (!block) return;

    const fill = block.querySelector(".progress-fill");
    const label = block.querySelector(".progress-label");

    fill.style.width = value + "%";
    label.textContent = value + "%";

    if (value === 100 || isFinal) {
        block.classList.add("success");
    }
}
