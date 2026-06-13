const form = document.getElementById("forgotForm");

form.addEventListener("submit", async (e) => {

    e.preventDefault();

    const email = document.getElementById("email").value;
    const result = document.getElementById("result");

    result.innerText = "";

    try {

        const response = await fetch("/auth/forgot-password", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email })
        });

        let data = {};

        try {
            data = await response.json();
        } catch {
            data = {};
        }

        if (!response.ok) {

            result.innerText =
                data.detail || "Something went wrong";

            return;
        }

        result.innerText =
            "If account exists, reset link was sent.";

        form.reset();

    } catch (err) {

        // console.error(err);

        result.innerText = "Network error";
    }

});