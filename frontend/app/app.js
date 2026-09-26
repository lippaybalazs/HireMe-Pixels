const API_URL = window.API_URL;

let currentUser = null;
let authProvider = null;
let csrfToken = null;
let isAdmin = false;

let boardWidth = 0;
let boardHeight = 0;
let board = [];

let selectedPixel = null;
let originalColor = null;

let currentMode = "select";

let pencilColor = localStorage.getItem("pencilColor") || "#ff0000";
let isPainting = false;
let paintingPixels = new Map();

let selected_user = null;


const boardElement = document.getElementById("board");

const dialogElement = document.getElementById("pixel-dialog");
const pixelDialogToggle = document.getElementById("pixel-dialog-toggle");

const positionElement = document.getElementById("pixel-position");
const userElement = document.getElementById("pixel-user");

const colorPicker = document.getElementById("color-picker");

const selectModeButton = document.getElementById("selectButton");

const editModeButton = document.getElementById("editButton");

const pencilModeButton = document.getElementById("pencilButton");

const loginToolbarButton = document.getElementById("login-toolbar-button");

const logoutToolbarButton = document.getElementById("logout-toolbar-button");

const loginDialogElement = document.getElementById("login-dialog");

const loginUsername = document.getElementById("login-username");

const loginPassword = document.getElementById("login-password");

const loginButton = document.getElementById("login-button");

const registerButton = document.getElementById("register-button");

const microsoftLoginButton = document.getElementById("microsoft-login-button");

const loadingOverlay = document.getElementById("loading-overlay");

const pixelInfo = document.getElementById("pixel-info");

const pencilColorButton = document.getElementById("pencil-color-button");

const pencilColorPicker = document.getElementById("pencil-color-picker");

const banUserButton = document.getElementById("ban-user-button");

/*
 * Authentication UI
 */

function showLoading() {
    loadingOverlay.classList.remove("hidden");
}

function hideLoading() {
    loadingOverlay.classList.add("hidden");
}

function showLoginDialog() {
    loginDialogElement.classList.remove("hidden");
    loginUsername.focus();
}

function hideLoginDialog() {
    loginDialogElement.classList.add("hidden");
}

function updateAuthUI() {
    if (currentUser) {
        loginToolbarButton.classList.add("hidden");
        logoutToolbarButton.classList.remove("hidden");

        editModeButton.disabled = false;
        editModeButton.title = "Edit";

        if (authProvider === "microsoft") {
            pencilModeButton.disabled = false;
            pencilModeButton.title = "Pencil";
        } else {
            pencilModeButton.disabled = true;
            pencilModeButton.title =
                "Pencil (log in with Microsoft to access)";
        }
    } else {
        loginToolbarButton.classList.remove("hidden");
        logoutToolbarButton.classList.add("hidden");

        editModeButton.disabled = true;
        editModeButton.title = "Edit (log in to access)";

        pencilModeButton.disabled = true;
        pencilModeButton.title =
            "Pencil (log in with Microsoft to access)";

        /*
         * A logged-out user cannot remain in edit mode.
         */
        if (currentMode != "select") {
            setMode("select");
        }
    }
}


/*
 * Authentication state
 */

async function loadCurrentUser() {
    const response = await fetch(`${API_URL}/auth/me/`, {
        credentials: "include",
    });

    if (!response.ok) {
        throw new Error(
            `Failed to load authentication state: ${response.status}`
        );
    }

    const data = await response.json();

    currentUser = data.authenticated
        ? data.username
        : null;

    csrfToken = data.authenticated
        ? data.csrf_token
        : null;

    isAdmin = data.authenticated
        ? data.is_admin
        : false;

    authProvider = data.authenticated
    ? data.auth_provider
    : null;

    updateAuthUI();
    updateBanButton();
}

function updateBanButton() {
    banUserButton.classList.toggle(
        "hidden",
        !isAdmin || currentMode != "select"
    );

    banUserButton.disabled =
        !selectedPixel ||
        !selected_user ||
        currentUser === selected_user;
}
/*
 * Board
 */

async function loadBoard() {
    const response = await fetch(`${API_URL}/pixels/`);

    if (!response.ok) {
        throw new Error(
            `Failed to load board: ${response.status}`
        );
    }

    const data = await response.json();

    boardWidth = data.width;
    boardHeight = data.height;
    board = data.pixels;

    renderBoard();
}

function startPainting(x, y) {
    if (authProvider !== "microsoft") {
        return;
    }

    isPainting = true;
    paintingPixels.clear();

    paintPixel(x, y);
}


function paintPixel(x, y) {
    const key = `${x},${y}`;

    // Record the original color only once per stroke.
    if (!paintingPixels.has(key)) {
        paintingPixels.set(key, {
            x,
            y,
            originalColor: board[y][x],
        });
    }

    // Update the local board immediately.
    board[y][x] = pencilColor;

    const pixel = getPixelElement(x, y);

    if (pixel) {
        pixel.style.backgroundColor = pencilColor;
    }
}


async function finishPainting() {
    if (!isPainting) {
        return;
    }

    isPainting = false;

    const stroke = [...paintingPixels.values()];
    paintingPixels.clear();

    if (stroke.length === 0) {
        return;
    }

    try {
        const response = await fetch(
            `${API_URL}/bulk_pixels/`,
            {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken,
                },
                body: JSON.stringify({
                    pixels: stroke.map(pixel => ({
                        x: pixel.x,
                        y: pixel.y,
                        color: pencilColor,
                    })),
                }),
            }
        );

        if (response.status === 401) {
            throw new Error("Your session has expired. Please log in again.");
        }

        if (response.status === 403) {
            throw new Error("Microsoft authentication is required.");
        }

        if (!response.ok) {
            const data = await response.json();

            throw new Error(
                data.error || "Failed to save painted pixels."
            );
        }

        const updatedPixels = await response.json();

        // Reconcile the local board with the server response.
        for (const pixel of updatedPixels) {
            board[pixel.y][pixel.x] = pixel.color;

            const element = getPixelElement(pixel.x, pixel.y);

            if (element) {
                element.style.backgroundColor = pixel.color;
            }
        }

    } catch (error) {
        console.error(error);

        // Restore the original colors if the stroke failed.
        for (const pixel of stroke) {
            board[pixel.y][pixel.x] = pixel.originalColor;

            const element = getPixelElement(pixel.x, pixel.y);

            if (element) {
                element.style.backgroundColor = pixel.originalColor;
            }
        }

        alert(error.message);
    }
}


document.addEventListener("mouseup", () => {
    finishPainting();
});

function renderBoard() {
    boardElement.innerHTML = "";

    boardElement.style.gridTemplateColumns =
        `repeat(${boardWidth}, 1fr)`;

    boardElement.style.gridTemplateRows =
        `repeat(${boardHeight}, 1fr)`;

    for (let y = 0; y < boardHeight; y++) {
        for (let x = 0; x < boardWidth; x++) {
            const pixel = document.createElement("button");

            pixel.className = "pixel";
            pixel.style.backgroundColor = board[y][x];

            pixel.dataset.x = x;
            pixel.dataset.y = y;

            pixel.addEventListener("click", () => {
                handlePixelClick(x, y);
            });

            pixel.addEventListener("mousedown", (event) => {
                if (event.button !== 0 || currentMode !== "pencil") {
                    return;
                }

                event.preventDefault();

                startPainting(x, y);
            });

            pixel.addEventListener("mouseenter", () => {
                if (isPainting && currentMode === "pencil") {
                    paintPixel(x, y);
                }
                if (currentMode === "pencil") {
                    pixel.classList.add("pencil-hover");
                }
            });

            pixel.addEventListener("mouseleave", () => {
                pixel.classList.remove("pencil-hover");
            });

            boardElement.appendChild(pixel);
        }
    }
}


/*
 * Modes
 */
function setMode(mode) {
    /*
     * Edit is unavailable while logged out.
     */
    if (mode === "edit" && !currentUser) {
        return;
    }

    if (mode === "pencil" && authProvider !== "microsoft") {
        return;
    }

    currentMode = mode;
    localStorage.setItem("selectedMode", mode);

    const cursor = {
        select: "default",
        edit: "pointer",
        pencil: "crosshair",
    }[mode];

    boardElement.style.setProperty(
        "--pixel-cursor",
        cursor
    );

    selectModeButton.classList.toggle(
        "active",
        mode === "select"
    );

    editModeButton.classList.toggle(
        "active",
        mode === "edit"
    );

    pencilModeButton.classList.toggle(
        "active",
        mode === "pencil"
    );

    pencilColorButton.classList.toggle(
        "hidden",
        mode !== "pencil"
    );

    pixelInfo.classList.toggle(
        "hidden",
        mode !== "select"
    );

    updateBanButton();
}


selectModeButton.addEventListener("click", () => {
    setMode("select");
});


editModeButton.addEventListener("click", () => {
    setMode("edit");
});


pencilModeButton.addEventListener("click", () => {
    setMode("pencil");
});


/*
 * Pixel interaction
 */

async function handlePixelClick(x, y) {
    if (currentMode === "select") {
        await selectPixel(x, y);
        return;
    }

    if (currentMode === "edit") {
        await editPixel(x, y);
        return;
    }
}


async function selectPixel(x, y) {
    if (
        selectedPixel &&
        selectedPixel.x === x &&
        selectedPixel.y === y
    ) {
        return;
    }

    selectedPixel = { x, y };
    originalColor = null;


    updateSelectedPixelBorder();

    try {
        const response = await fetch(
            `${API_URL}/pixel/?x=${x}&y=${y}`,
            {
                credentials: "include",
            }
        );

        if (!response.ok) {
            throw new Error(
                `Failed to load pixel: ${response.status}`
            );
        }

        const pixel = await response.json();
        
        showPixelData(pixel);
        updateBanButton();

    } catch (error) {
        console.error(error);
    }
}


async function editPixel(x, y) {
    /*
     * The button is disabled when logged out, but keep this
     * check here as an additional safeguard.
     */
    if (!currentUser) {
        showLoginDialog();
        return;
    }

    selectedPixel = { x, y };
    originalColor = board[y][x];

    updateSelectedPixelBorder();

    colorPicker.value = board[y][x];

    /*
     * Because this happens directly from the pixel click event,
     * the browser can open the native color picker.
     */
    colorPicker.click();
}

pencilColorButton.addEventListener("click", () => {
    pencilColorPicker.click();
});

pencilColorPicker.addEventListener("input", () => {
    pencilColor = pencilColorPicker.value;

    localStorage.setItem("pencilColor", pencilColor);

    pencilColorButton.style.backgroundColor = pencilColor;
});
/*
 * Save the selected pixel immediately after choosing a color.
 */

colorPicker.addEventListener("change", async () => {
    if (
        currentMode !== "edit" ||
        !selectedPixel ||
        !currentUser
    ) {
        return;
    }

    const color = colorPicker.value;

    await savePixel(
        selectedPixel.x,
        selectedPixel.y,
        color
    );
});

async function savePixel(x, y, color) {
    try {
        const response = await fetch(`${API_URL}/pixel/`, {
            method: "PUT",
            credentials: "include",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken,
            },
            body: JSON.stringify({
                x,
                y,
                color,
            }),
        });

        if (response.status === 401) {
            showLoginDialog();
            return;
        }

        if (!response.ok) {
            const error = await response.json();

            throw new Error(
                error.error || "Failed to update pixel."
            );
        }

        const pixel = await response.json();

        board[pixel.y][pixel.x] = pixel.color;

        originalColor = pixel.color;

        const boardPixel = getPixelElement(
            pixel.x,
            pixel.y
        );

        if (boardPixel) {
            boardPixel.style.backgroundColor = pixel.color;
        }

        /*
         * Keep the information area updated after editing.
         */
        showPixelData(pixel);
        updateBanButton();

    } catch (error) {
        console.error(error);

        alert(error.message);

        const boardPixel = getPixelElement(x, y);

        if (boardPixel) {
            boardPixel.style.backgroundColor = originalColor;
        }

        colorPicker.value = originalColor;
    }
}


/*
 * Pixel information
 */

function showPixelData(pixel) {
    if (pixel) {
        positionElement.textContent =
        `(${pixel.x} x ${pixel.y})`;

        userElement.textContent =
            pixel.display_name || pixel.user;

        selected_user = pixel.user;
    } else {
        positionElement.textContent = "";
        userElement.textContent = "";
        selected_user = null;
    }
    
}



/*
 * Pixel selection border
 */

function isDarkColor(hexColor) {
    const r = parseInt(
        hexColor.slice(1, 3),
        16
    );

    const g = parseInt(
        hexColor.slice(3, 5),
        16
    );

    const b = parseInt(
        hexColor.slice(5, 7),
        16
    );

    const luminance =
        0.299 * r +
        0.587 * g +
        0.114 * b;

    return luminance < 128;
}


function updateSelectedPixelBorder() {
    document
        .querySelectorAll(".pixel.selected")
        .forEach(pixel => {
            pixel.classList.remove("selected");
            pixel.style.removeProperty("--selection-color");
        });

    if (!selectedPixel) {
        return;
    }

    const pixel = getPixelElement(
        selectedPixel.x,
        selectedPixel.y
    );

    if (!pixel) {
        return;
    }

    pixel.classList.add("selected");

    const color =
        board[selectedPixel.y][selectedPixel.x];

    pixel.style.setProperty(
        "--selection-color",
        isDarkColor(color)
            ? "#DDDDDD"
            : "#000000"
    );
}


function getPixelElement(x, y) {
    return boardElement.querySelector(
        `.pixel[data-x="${x}"][data-y="${y}"]`
    );
}


/*
 * Toolbar collapse / expand
 */

pixelDialogToggle.addEventListener("click", () => {
    const collapsed =
        dialogElement.classList.toggle("collapsed");

    if (collapsed) {
        pixelDialogToggle.innerHTML = '<i class="fa-solid fa-arrow-up"></i>';
        pixelDialogToggle.setAttribute(
            "aria-label",
            "Show toolbar"
        );
    } else {
        pixelDialogToggle.innerHTML = '<i class="fa-solid fa-arrow-down"></i>';
        pixelDialogToggle.setAttribute(
            "aria-label",
            "Hide toolbar"
        );
    }
});


/*
 * Login
 */

loginToolbarButton.addEventListener("click", () => {
    showLoginDialog();
});


loginButton.addEventListener("click", async () => {
    showLoading();

    try {
        const response = await fetch(
            `${API_URL}/auth/login/`,
            {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    username: loginUsername.value,
                    password: loginPassword.value,
                }),
            }
        );

        const data = await response.json();

        if (!response.ok) {
            alert(data.error || "Login failed.");
            return;
        }

        window.location.reload();

    } catch (error) {
        console.error(error);
        alert("Login failed.");

    } finally {
        hideLoading();
    }
});


/*
 * Register
 */

registerButton.addEventListener("click", async () => {
    showLoading();

    try {
        const response = await fetch(
            `${API_URL}/auth/register/`,
            {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    username: loginUsername.value,
                    password: loginPassword.value,
                }),
            }
        );

        const data = await response.json();

        if (!response.ok) {
            alert(data.error || "Registration failed.");
            return;
        }

        window.location.reload();

    } catch (error) {
        console.error(error);
        alert("Registration failed.");

    } finally {
        hideLoading();
    }
});


/*
 * Microsoft login
 */

microsoftLoginButton.addEventListener("click", () => {
    showLoading();

    window.location.href =
        `${API_URL}/auth/microsoft/`;
});


/*
 * Logout
 */

logoutToolbarButton.addEventListener("click", async () => {
    showLoading();

    try {
        const response = await fetch(
            `${API_URL}/auth/logout/`,
            {
                method: "POST",
                credentials: "include",
                headers: {
                    "X-CSRFToken": csrfToken,
                },
            }
        );

        if (!response.ok) {
            const data = await response.json();

            throw new Error(
                data.error || "Logout failed."
            );
        }

        currentUser = null;
        authProvider = null;
        csrfToken = null;
        isAdmin = false;

        updateAuthUI();

        window.location.reload();

    } catch (error) {
        console.error(error);

        alert(
            error.message || "Logout failed."
        );

    } finally {
        hideLoading();
    }
});

/*
 * Ban user
 */

banUserButton.addEventListener("click", async () => {
    if (
        !isAdmin ||
        !selectedPixel ||
        !selected_user ||
        currentUser === selected_user
    ) {
        return;
    }

    try {
        const response = await fetch(
            `${API_URL}/auth/ban/`,
            {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken,
                },
                body: JSON.stringify({
                    username: selected_user,
                }),
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Failed to ban user."
            );
        }

        await loadBoard();

        selected_user = null;
        selectedPixel = null;
        updateBanButton();
        showPixelData(selectedPixel)
        

        alert(`User "${data.username}" has been banned.`);

    } catch (error) {
        console.error(error);

        alert(
            error.message || "Failed to ban user."
        );
    }
});

/*
 * Initialize
 */

async function initialize() {
    showLoading();

    try {
        pencilColorPicker.value = pencilColor;
        pencilColorButton.style.backgroundColor = pencilColor;

        await loadCurrentUser();
        await loadBoard();

        const savedMode = localStorage.getItem("selectedMode") || "select";
        setMode(savedMode);

    } catch (error) {
        console.error(error);

        boardElement.textContent =
            "Failed to load the pixel board.";
    } finally {
        hideLoading();
    }
}


initialize().catch(error => {
    console.error(error);

    boardElement.textContent =
        "Failed to load the pixel board.";
});