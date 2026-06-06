const form = document.getElementById("registerForm");

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirm_password").value;
    const result = document.getElementById("result");

    if (password !== confirmPassword) {
        result.innerText = "Passwords do not match";
        return;
    }

    try {
        const response = await fetch("/auth/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email, password }),
            redirect: "manual"   // KLUCZOWE
        });

        // 🔥 Jeśli rejestracja OK → backend zwraca 200 → my robimy redirect
        if (response.status === 200 || response.status === 201) {
            window.location.href = "/login_page";
            return;
        }

        // 🔥 Jeśli błąd → backend zwraca JSON z detail
        if (response.status >= 400) {
            const data = await response.json();
            result.innerText = data.detail || "Registration failed";
            return;
        }

        result.innerText = "Unexpected response";

    } catch (error) {
        result.innerText = "Network error";
    }
});





// API VERSION ONLY

// const form = document.getElementById("registerForm");

// form.addEventListener("submit", async (e)=>{

//     e.preventDefault();

//     const email = document.getElementById("email").value;

//     const password = document.getElementById("password").value;

//     const result = document.getElementById("result");

//     try{

//         const response = await fetch(`/auth/register`,{
//             method:"POST",
//             headers:{
//                 "Content-Type":"application/json"
//             },
//             body:JSON.stringify({
//                 email,
//                 password
//             })
//         });

//         const data = await response.json();
//         window.location.href = "/auth/login";

//         // result.innerText = JSON.stringify(data,null,2);

//     }catch(error){

//         result.innerText = error;

//     }

// });