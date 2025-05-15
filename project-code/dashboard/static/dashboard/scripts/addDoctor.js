
var nonRelatedDoctors = [] 

function addDoctorView(){
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function() {
        if (xhr.readyState !== 4) return
        populateDoctors(xhr)
    }
    xhr.open("GET", `/api/get-doctors/${username}`, true)
    xhr.send()
}

function populateDoctors(xhr) {
    nonRelatedDoctors = JSON.parse(xhr.responseText)["non_related_doctors"]
    const doctorListElement = document.getElementById("doctor-list");
    if (nonRelatedDoctors.length === 0){
        doctorListElement.innerHTML = `
                <br>No doctors found
        `;
        return
    }
    doctorListElement.innerHTML = "";
    nonRelatedDoctors.forEach(doctor => {
        const doctorElement = document.createElement("tr");
        doctorElement.innerHTML = `
            <th scope="row">1</th>
            <td><a target="_blank" href="/doctorProfile/${doctor.id}/">${doctor.first_name} ${doctor.last_name}</a></td>
            <td>
                <button type="button" class="btn btn-primary" onclick="addDoctorToPatient('${doctor.id}')">Add</button>
            </td>
        `;
        doctorListElement.appendChild(doctorElement);
    })   
}

function addDoctorToPatient(doctorId){
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function () {
        if (xhr.readyState !== 4) return
        location.reload()
    }
    xhr.open("POST", "/api/addDoctorToPatient/", true)
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    xhr.send(`patient_username=${username}&doctor_id=${doctorId}&csrfmiddlewaretoken=${getCSRFToken()}`)
}