function openTab(evt, tabName) {
    let contents = document.getElementsByClassName("tab-content");
    let buttons = document.getElementsByClassName("tab-btn");

    for (let i = 0; i < contents.length; i++) {
        contents[i].classList.remove("active");
    }

    for (let i = 0; i < buttons.length; i++) {
        buttons[i].classList.remove("active");
    }

    document.getElementById(tabName).classList.add("active");
    evt.currentTarget.classList.add("active");
}


document.addEventListener("DOMContentLoaded", function () {

    const popup = document.getElementById("popupForm");
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("overlay");

    window.openPopup = function () {
        popup.classList.add("show");

        if (sidebar) sidebar.classList.remove("active");
        if (overlay) overlay.classList.remove("active");
    }

    window.closePopup = function () {
        popup.classList.remove("show");
        sidebar.classList.remove("active");
        overlay.classList.remove("active");
    }

    if (popup) {
        popup.addEventListener("click", function (event) {
            if (event.target === popup) {
                closePopup();
            }
        });
    }
});


function openEditFromButton(btn) {

    const id = btn.dataset.id;
    const company = btn.dataset.company;
    const position = btn.dataset.position;
    const location = btn.dataset.location;
    const status = btn.dataset.status;
    const type = btn.dataset.type;
    const dates = JSON.parse(btn.dataset.dates || "[]");

    openEditModal(id, company, position, location, status, type, dates);
}

function openEditModal(id, company, position, location, status, type, dates) {

    document.getElementById("editModal").style.display = "block";

    document.getElementById("edit_id").value = id;
    document.getElementById("edit_company").value = company;
    document.getElementById("edit_position").value = position;
    document.getElementById("edit_location").value = location;
    document.getElementById("edit_status").value = status;
    document.getElementById("edit_type").value = type;

    document.getElementById("editForm").action = "/edit_job/" + id;

    const container = document.getElementById("edit-dates-container");
    container.innerHTML = "";

    if (!Array.isArray(dates)) {
        dates = [];
    }

    dates.forEach(date => {
        addEditDate(date.date_type, date.date_value?.slice(0, 16));
    });
}

function closeEditModal() {
    document.getElementById("editModal").style.display = "none";
}

function outsideClick(event) {
    const modal = document.getElementById("editModal");

    if (event.target === modal) {
        closeEditModal();
    }
}

function addEditDate(type = "", value = "") {

    const container = document.getElementById("edit-dates-container");

    const div = document.createElement("div");

    div.classList.add("date-row");

    div.innerHTML = `
        <select name="date_type[]">

            <option value="Applied" ${type === "Applied" ? "selected" : ""}>Applied</option>

            <option value="Interview" ${type === "Interview" ? "selected" : ""}>Interview</option>

            <option value="Deadline" ${type === "Deadline" ? "selected" : ""}>Deadline</option>

            <option value="Offer" ${type === "Offer" ? "selected" : ""}>Offer</option>

        </select>

        <input type="datetime-local" name="date_value[]" value="${value || ''}">

        <button type="button" onclick="removeDate(this)" class="remove-date-btn">
            <i class="bxf bx-x-square bx-sm"></i>
        </button>
    `;

    container.appendChild(div);
}

function removeDate(button) {
    button.parentElement.remove();
}