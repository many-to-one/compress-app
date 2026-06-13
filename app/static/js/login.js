const form = document.getElementById("loginForm");

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const result = document.getElementById("result");

    try {
        const response = await fetch("/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email,
                password
            })
        });

        const data = await response.json();

        if (!response.ok) {
            result.innerText = data.detail || "Login failed";
            return;
        }

        window.location.href = "/";

    } catch (error) {
        // console.error(error);
        result.innerText = "Network error";
    }
});


async function loginWithGoogle() {
    window.location.href = "/auth/google";
}







// FOR API ONLY

// const form = document.getElementById("loginForm");

// form.addEventListener("submit", async (e)=>{

//     e.preventDefault();

//     const email = document.getElementById("email").value;

//     const password = document.getElementById("password").value;

//     const result = document.getElementById("result");

//     try{

//         const formData = new URLSearchParams();

//         formData.append("username", email);
//         formData.append("password", password);

//         const response = await fetch(`/auth/login`,{
//             method:"POST",
//             headers:{
//                 "Content-Type":"application/x-www-form-urlencoded"
//             },
//             body:formData
//         });

//         const data = await response.json();

//         if(data.access_token){

//             window.location.href = "/";

//             localStorage.setItem(
//                 "access_token",
//                 data.access_token
//             );

//         }else{

//             result.innerText = JSON.stringify(data,null,2);

//         }

//     }catch(error){

//         result.innerText = error;

//     }

// });


// // LOGOUT

// function logout() {
//     localStorage.removeItem("token");

//     fetch("/auth/logout", { method: "POST" });

//     window.location.href = "/auth/login";
// }
