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

document.addEventListener("DOMContentLoaded", function () {

    console.log("job.js loaded");

    const form = document.getElementById("jobForm");
    const errorBox = document.getElementById("date-error");

    if (!form) {
        console.log("Form not found!");
        return;
    }

    form.addEventListener("submit", function (e) {


        errorBox.textContent = "";

        const rows = document.querySelectorAll("#popupForm .date-row");


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
            errorBox.textContent = "❌ Stage 1 cannot be earlier than Applied.";
            return;
        }

        if (stage2 && stage1 && stage2 < stage1) {
            e.preventDefault();
            errorBox.textContent = "❌ Stage 2 cannot be earlier than Stage 1.";
            return;
        }

        if (stage2 && applied && stage2 < applied) {
            e.preventDefault();
            errorBox.textContent = "❌ Stage 2 cannot be earlier than Applied.";
            return;
        }

        if (interview && stage2 && interview < stage2) {
            e.preventDefault();
            errorBox.textContent = "❌ Interview cannot be earlier than Stage 2.";
            return;
        }

        if (interview && stage1 && interview < stage1) {
            e.preventDefault();
            errorBox.textContent = "❌ Interview cannot be earlier than Stage 1.";
            return;
        }

        if (interview && applied && interview < applied) {
            e.preventDefault();
            errorBox.textContent = "❌ Interview cannot be earlier than Applied.";
            return;
        }

        if (offer && interview && offer < interview) {
            e.preventDefault();
            errorBox.textContent = "❌ Offer cannot be earlier than Interview.";
            return;
        }

        if (offer && stage1 && offer < stage1) {
            e.preventDefault();
            errorBox.textContent = "❌ Offer cannot be earlier than Stage 1.";
            return;
        }

        if (offer && stage2 && offer < stage2) {
            e.preventDefault();
            errorBox.textContent = "❌ Offer cannot be earlier than Stage 2.";
            return;
        }

        if (offer && applied && offer < applied) {
            e.preventDefault();
            errorBox.textContent = "❌ Offer cannot be earlier than Applied.";
            return;
        }
    });
});