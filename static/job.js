document.addEventListener("DOMContentLoaded", function () {

    const popup = document.getElementById("popupForm");
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("overlay");

    window.openPopup = function () {
        popup?.classList.add("show");

        sidebar?.classList.remove("active");
        overlay?.classList.remove("active");
    }

    window.closePopup = function () {
        popup?.classList.remove("show");

        sidebar?.classList.remove("active");
        overlay?.classList.remove("active");
    }

    popup.addEventListener("click", function (event) {
        if (event.target === popup) {
            closePopup();
        }
    });

    window.toggleSidebar = function () {
        sidebar.classList.toggle("active");
        overlay.classList.toggle("active");
    }

});

function addDate() {
    const container = document.getElementById("dates-container");

    const div = document.createElement("div");
    div.classList.add("date-row");

    div.innerHTML = `
        <select name="date_type[]">
            <option value="Applied">Applied</option>
            <option value="Interview">Interview</option>
            <option value="Deadline">Deadline</option>
            <option value="Offer">Offer</option>
        </select>

        <input type="datetime-local" name="date_value[]">

        <button type="button" onclick="removeDate(this)" class="icon-btn">
            <i class="bxf bx-x-square bx-sm"></i>
        </button>
    `;

    container.appendChild(div);
}

function removeDate(button) {
    button.parentElement.remove();
}