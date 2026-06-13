function checkAuth(response) {

    // console.log('checkAuth*******', response.status)
    // 302 → backend próbuje przekierować na /login_page
    if (response.status === 302 || response.redirected) {
        alert("Sesja wygasła. Zaloguj się ponownie.");
        window.location.href = "/login_page";
        return false;
    }

    // 401 → backend mówi "niezalogowany"
    if (response.status === 401) {
        alert("Sesja wygasła. Zaloguj się ponownie.");
        window.location.href = "/login_page";
        return false;
    }

    // 403 → brak uprawnień
    if (response.status === 403) {
        alert("Brak uprawnień.");
        return false;
    }

    return true;
}
