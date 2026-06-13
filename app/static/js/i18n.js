// ------------------------------
// CONFIG
// ------------------------------
const DEFAULT_LANG = "en";
const SUPPORTED_LANGS = ["en", "pl", "de"];

// ------------------------------
// DETECT LANGUAGE
// ------------------------------
function detectLanguage() {
    const saved = localStorage.getItem("lang");
    if (saved && SUPPORTED_LANGS.includes(saved)) return saved;

    const browser = navigator.language.slice(0, 2);
    if (SUPPORTED_LANGS.includes(browser)) return browser;

    // zapisujemy język regionu, żeby móc do niego wrócić
    localStorage.setItem("regionLang", browser);

    return DEFAULT_LANG;
}

let currentLang = detectLanguage();

// ------------------------------
// LOAD TRANSLATIONS
// ------------------------------
async function loadTranslations(lang) {
    try {
        const res = await fetch(`/static/i18n/${lang}.json`);
        return await res.json();
    } catch (e) {
        // console.warn("Missing translation file, using fallback EN");
        const res = await fetch(`/static/i18n/en.json`);
        return await res.json();
    }
}

// ------------------------------
// APPLY TRANSLATIONS
// ------------------------------
async function translatePage() {
    const dict = await loadTranslations(currentLang);

    document.querySelectorAll("[data-i18n]").forEach(el => {
        const key = el.getAttribute("data-i18n");
        if (dict[key]) el.innerText = dict[key];
    });
}

translatePage();

// ------------------------------
// LANGUAGE SWITCHER
// ------------------------------
// function setLang(lang) {
//     localStorage.setItem("lang", lang);
//     location.reload();
// }


// function setLang(lang) {
//     if (lang === "en") {
//         // przełączamy na oryginał
//         localStorage.setItem("lang", "en");
//     } else if (lang === "region") {
//         // wracamy do języka regionu
//         const region = localStorage.getItem("regionLang") || "en";
//         localStorage.setItem("lang", region);
//         translatePage();
//     } else {
//         // normalne ustawienie języka
//         localStorage.setItem("lang", lang);
//     }

//     location.reload();
// }

function setLang(lang) {

    // console.log("regionLang", localStorage.getItem("regionLang"))
    if (lang === "en") {
        // przełączamy na oryginał
        localStorage.setItem("lang", "en");
    } else if (lang === "region") {
        // wracamy do języka regionu
        const region = localStorage.getItem("regionLang") || "en";
        localStorage.setItem("lang", region);
        translatePage();
    } else {
        // normalne ustawienie języka
        localStorage.setItem("lang", lang);
    }

    location.reload();
}
