// FILE: static/js/batch.js

document.getElementById("uploadForm").onsubmit = async (e) => {
    e.preventDefault();

    const files = document.getElementById("files").files;
    const formData = new FormData();

    for (let f of files) {
        formData.append("files", f);
    }

    const res = await fetch("/compress/batch", {
        method: "POST",
        body: formData
    });

    const data = await res.json();
    const taskId = data.task_id;

    checkStatus(taskId);
};

async function checkStatus(taskId) {
    const statusDiv = document.getElementById("status");

    const interval = setInterval(async () => {
        const res = await fetch(`/compress/status/${taskId}`);
        const data = await res.json();

        statusDiv.innerHTML = `
            <p>Status: ${data.status}</p>
            <p>Progress: ${data.progress}%</p>
        `;

        if (data.status === "done") {
            clearInterval(interval);
            statusDiv.innerHTML += `
                <a href="/compress/download/${taskId}">Download ZIP</a>
            `;
        }
    }, 1000);
}
