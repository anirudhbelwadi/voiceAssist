
function sendConditionToServer(conditionName, conditionSeverity, conditionDate) {
    let xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function () {
        if (xhr.readyState !== 4) return;
        if (xhr.status === 200) {
            addConditionToList(conditionName, conditionSeverity, conditionDate);
            showSuccessToast("Condition added successfully.");
        } else {
            showErrorToast("Failed to add condition. Please try again.");
        }
    };
    xhr.open("POST", "/api/addCondition/", true);
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhr.send(`condition_name=${conditionName}&condition_severity=${conditionSeverity}&condition_date=${conditionDate}&csrfmiddlewaretoken=${getCSRFToken()}&patient_id=${patientId}`);
}

function addConditionToList(conditionName, conditionSeverity, conditionDate) {
    const conditionList = document.getElementById("health-conditions");
    const noConditionMessage = document.getElementById("no-condition");
    noConditionMessage ? noConditionMessage.remove() : null;
    const conditionRow = document.createElement("tr");
    conditionRow.innerHTML = `
            <td>${conditionName}</td>
            <td>${conditionSeverity}</td>
            <td>${conditionDate}</td>
            `;
    conditionList.appendChild(conditionRow);

    document.getElementById("conditionName").value = "";
    document.getElementById("conditionSeverity").value = "";
    document.getElementById("conditionDate").value = "";
}

function addCondition() {
    const conditionName = document.getElementById("conditionName").value;
    const conditionSeverity = document.getElementById("conditionSeverity").value;
    const conditionDate = document.getElementById("conditionDate").value;
    if (conditionName && conditionSeverity && conditionDate) {
        sendConditionToServer(conditionName, conditionSeverity, conditionDate);
    } else {
        showErrorToast("Please fill in all fields.")
    }
}

function sendMedicationToServer(medicationName, medicationFrequency) {
    let xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function () {
        if (xhr.readyState !== 4) return;
        if (xhr.status === 200) {
            addMedicationToList(medicationName, medicationFrequency);
            showSuccessToast("Medication added successfully.");
        } else {
            showErrorToast("Failed to add medication. Please try again.");
        }
    };
    xhr.open("POST", "/api/addMedication/", true);
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhr.send(`medication_name=${medicationName}&medication_frequency=${medicationFrequency}&csrfmiddlewaretoken=${getCSRFToken()}&patient_id=${patientId}`);
}

function addMedicationToList(medicationName, medicationFrequency) {
    const medicationList = document.getElementById("medications");
    const noMedicationMessage = document.getElementById("no-medication");
    noMedicationMessage ? noMedicationMessage.remove() : null;
    const medicationRow = document.createElement("tr");
    medicationRow.innerHTML = `
            <td>${medicationName}</td>
            <td>${medicationFrequency}</td>
            `;
    medicationList.appendChild(medicationRow);

    document.getElementById("medicationName").value = "";
    document.getElementById("medicationFrequency").value = "";
}

function addMedication() {
    const medicationName = document.getElementById("medicationName").value;
    const medicationFrequency = document.getElementById("medicationFrequency").value;
    if (medicationName && medicationFrequency) {
        sendMedicationToServer(medicationName, medicationFrequency);
    } else {
        showErrorToast("Please fill in all fields.")
    }
}