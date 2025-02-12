async function chooseFolder() {
    let folder = await eel.choose_folder()();
    if (folder) {
        document.getElementById('folderPath').value = folder;
    }
}

async function startScraping() {
    let folderPath = document.getElementById('folderPath').value;
    let pages = document.getElementById('pages').value;
    let stars = document.getElementById('stars').value;

    eel.start_scraping(folderPath, pages, stars);
}

eel.expose(update_status);
function update_status(msg) {
    let statusBox = document.getElementById('status');
    statusBox.value += msg + "\n";
    statusBox.scrollTop = statusBox.scrollHeight;
}

eel.expose(update_progress);
function update_progress(value) {
    document.getElementById('progressBar').value = value;
}

eel.expose(show_message);
function show_message(type, msg) {
    alert(msg);
}
