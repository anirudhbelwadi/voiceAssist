function removeDoctor(doctorId) {
    if (confirm("Are you sure you want to remove this doctor?")) {
        let xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function () {
            if (xhr.readyState !== 4) return;
            if (xhr.status === 200) {
                removeDoctorFromList(doctorId);
                showSuccessToast("Doctor removed successfully.");
            } else {
                showErrorToast("Failed to remove doctor. Please try again.");
            }
        };
        xhr.open("POST", "/api/removeDoctor/", true);
        xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        xhr.send(`doctor_id=${doctorId}&csrfmiddlewaretoken=${getCSRFToken()}&patient_id=${patientId}`);
    }
}

function removeDoctorFromList(doctorId) {
    const doctorRow = document.getElementById(`doctor-${doctorId}`);
    if (doctorRow) {
        doctorRow.remove();
    }
}