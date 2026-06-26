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
            <option value="applied">Applied</option>
            <option value="stage1">Stage 1</option>
            <option value="stage2">Stage 2</option>
            <option value="interview">Interview</option>
            <option value="deadline">Deadline</option>
            <option value="offer">Offer</option>
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

setTimeout(function(){

    document.querySelectorAll(".flash-message").forEach(function(msg){

        msg.classList.add("hide");

        setTimeout(function(){
            msg.remove();
        },500);

    });

},3000);