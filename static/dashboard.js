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

    const errorBox = document.getElementById("edit-error");
    if (errorBox) errorBox.textContent = "";

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
        addEditDate(date.date_type, date.input_value);
    });
}

function closeEditModal() {
    document.getElementById("editModal").style.display = "none";

    const errorBox = document.getElementById("edit-error");
    if (errorBox) errorBox.textContent = "";
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
            <option value="applied" ${type === "applied" ? "selected" : ""}>Applied</option>
            <option value="stage1" ${type === "stage1" ? "selected" : ""}>Stage 1</option>
            <option value="stage2" ${type === "stage2" ? "selected" : ""}>Stage 2</option>
            <option value="interview" ${type === "interview" ? "selected" : ""}>Interview</option>
            <option value="deadline" ${type === "deadline" ? "selected" : ""}>Deadline</option>
            <option value="offer" ${type === "offer" ? "selected" : ""}>Offer</option>
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

setTimeout(function(){

    document.querySelectorAll(".flash-message").forEach(function(msg){

        msg.classList.add("hide");

        setTimeout(function(){
            msg.remove();
        },500);

    });

},3000);

document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("editForm");
    const errorBox = document.getElementById("edit-error");

    if (!editForm) return;

    editForm.addEventListener("submit", function (e) {


        errorBox.textContent = "";

        const rows = document.querySelectorAll("#edit-dates-container .date-row");


        let dates = {
            applied: [],
            stage1: [],
            stage2: [],
            interview: [],
            offer: [],
            deadline: []
        };

        rows.forEach(row => {

            const type = row.querySelector('select[name="date_type[]"]')?.value;
            const value = row.querySelector('input[name="date_value[]"]')?.value;

            if (!type || !value) return;

            dates[type].push(new Date(value));
        });

        function getDate(arr) {
            return arr.length ? arr[0] : null;
        }

        const applied = getDate(dates.applied);
        const stage1 = getDate(dates.stage1);
        const stage2 = getDate(dates.stage2);
        const interview = getDate(dates.interview);
        const offer = getDate(dates.offer);

        if (stage1 && applied && stage1 < applied) {
            e.preventDefault();
            errorBox.textContent = "Stage 1 cannot be earlier than Applied.";
            return;
        }

        if (stage2 && stage1 && stage2 < stage1) {
            e.preventDefault();
            errorBox.textContent = "Stage 2 cannot be earlier than Stage 1.";
            return;
        }

        if (stage2 && applied && stage2 < applied) {
            e.preventDefault();
            errorBox.textContent = "Stage 2 cannot be earlier than Applied.";
            return;
        }

        if (interview && stage2 && interview < stage2) {
            e.preventDefault();
            errorBox.textContent = "Interview cannot be earlier than Stage 2.";
            return;
        }

        if (interview && stage1 && interview < stage1) {
            e.preventDefault();
            errorBox.textContent = "Interview cannot be earlier than Stage 1.";
            return;
        }

        if (interview && applied && interview < applied) {
            e.preventDefault();
            errorBox.textContent = "Interview cannot be earlier than Applied.";
            return;
        }

        if (offer && interview && offer < interview) {
            e.preventDefault();
            errorBox.textContent = "Offer cannot be earlier than Interview.";
            return;
        }

        if (offer && stage1 && offer < stage1) {
            e.preventDefault();
            errorBox.textContent = "Offer cannot be earlier than Stage 1.";
            return;
        }

        if (offer && stage2 && offer < stage2) {
            e.preventDefault();
            errorBox.textContent = "Offer cannot be earlier than Stage 2.";
            return;
        }

        if (offer && applied && offer < applied) {
            e.preventDefault();
            errorBox.textContent = "Offer cannot be earlier than Applied.";
            return;
        }
    });
});