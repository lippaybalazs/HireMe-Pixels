const API_URL = "http://127.0.0.1:8000/api";

let boardWidth = 0;
let boardHeight = 0;
let board = [];

let selectedPixel = null;
let originalColor = null;


const boardElement = document.getElementById("board");
const dialogElement = document.getElementById("pixel-dialog");

const positionElement = document.getElementById("pixel-position");
const userElement = document.getElementById("pixel-user");
const timeElement = document.getElementById("pixel-time");

const colorPicker = document.getElementById("color-picker");
const saveButton = document.getElementById("save-button");


async function loadBoard() {
    const response = await fetch(`${API_URL}/pixels/`);

    if (!response.ok) {
        throw new Error(`Failed to load board: ${response.status}`);
    }

    const data = await response.json();

    boardWidth = data.width;
    boardHeight = data.height;
    board = data.pixels;

    renderBoard();
}


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
                selectPixel(x, y);
            });

            boardElement.appendChild(pixel);
        }
    }
}


async function selectPixel(x, y) {
    if (selectedPixel && selectedPixel.x === x && selectedPixel.y === y) {
        return;
    }

    /*
     * Throw away any unsaved color change on the previously
     * selected pixel.
     */
    if (selectedPixel && originalColor !== null) {
        const previousPixel = getPixelElement(
            selectedPixel.x,
            selectedPixel.y
        );

        if (previousPixel) {
            previousPixel.style.backgroundColor = originalColor;
        }
    }

    selectedPixel = { x, y };
    originalColor = null;

    updateSelectedPixelBorder();

    try {
        const response = await fetch(
            `${API_URL}/pixel/?x=${x}&y=${y}`
        );

        if (!response.ok) {
            throw new Error(
                `Failed to load pixel: ${response.status}`
            );
        }

        const pixel = await response.json();

        showPixelDialog(pixel);
    } catch (error) {
        console.error(error);
    }
}

function isDarkColor(hexColor) {
    const r = parseInt(hexColor.slice(1, 3), 16);
    const g = parseInt(hexColor.slice(3, 5), 16);
    const b = parseInt(hexColor.slice(5, 7), 16);

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

    const color = board[selectedPixel.y][selectedPixel.x];

    pixel.style.setProperty(
        "--selection-color",
        isDarkColor(color) ? "#DDDDDD" : "#000000"
    );
}


function getPixelElement(x, y) {
    return boardElement.querySelector(
        `.pixel[data-x="${x}"][data-y="${y}"]`
    );
}


function showPixelDialog(pixel) {
    positionElement.textContent =
        `(${pixel.x}, ${pixel.y})`;

    userElement.textContent =
        pixel.user;

    timeElement.textContent =
        formatDate(pixel.changed_at);

    colorPicker.value = pixel.color;

    originalColor = pixel.color;

    saveButton.disabled = true;

    dialogElement.classList.remove("hidden");
}


function formatDate(timestamp) {
    return new Date(timestamp).toLocaleString();
}


colorPicker.addEventListener("input", () => {
    if (!selectedPixel || originalColor === null) {
        return;
    }

    const newColor = colorPicker.value;

    const pixel = getPixelElement(
        selectedPixel.x,
        selectedPixel.y
    );

    if (pixel) {
        pixel.style.backgroundColor = newColor;
    }

    saveButton.disabled = (
        newColor.toUpperCase() === originalColor.toUpperCase()
    );
});


saveButton.addEventListener("click", async () => {
    if (!selectedPixel || originalColor === null) {
        return;
    }

    const color = colorPicker.value;
    const user = getUserName();

    if (!user) {
        return;
    }

    saveButton.disabled = true;

    try {
        const response = await fetch(`${API_URL}/pixel/`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                x: selectedPixel.x,
                y: selectedPixel.y,
                color: color,
                user: user,
            }),
        });

        if (!response.ok) {
            const error = await response.json();

            throw new Error(
                error.error || "Failed to update pixel."
            );
        }

        const pixel = await response.json();

        board[pixel.y][pixel.x] = pixel.color;

        showPixelDialog(pixel);

    } catch (error) {
        console.error(error);

        alert(error.message);

        const pixel = getPixelElement(
            selectedPixel.x,
            selectedPixel.y
        );

        if (pixel) {
            pixel.style.backgroundColor = originalColor;
        }

        colorPicker.value = originalColor;
        saveButton.disabled = true;
    }
});


function getUserName() {
    let user = localStorage.getItem("hireme-pixels-user");

    if (!user) {
        user = prompt("Enter your name:");

        if (!user) {
            return null;
        }

        user = user.trim();

        if (!user) {
            return null;
        }

        localStorage.setItem(
            "hireme-pixels-user",
            user
        );
    }

    return user;
}


loadBoard().catch(error => {
    console.error(error);

    boardElement.textContent =
        "Failed to load the pixel board.";
});