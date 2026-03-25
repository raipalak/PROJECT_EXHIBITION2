const API_URL = 'http://localhost:5001/api/appointments';

let doctors = [];
let selectedDoctor = null;

async function fetchDoctors(search = '') {
    try {
        const res = await fetch(`${API_URL}/doctors?search=${search}`);
        const data = await res.json();
        if (Array.isArray(data)) {
            doctors = data;
            renderDoctors(data);
        }
    } catch (err) {
        console.error('Error fetching doctors:', err);
    }
}

function renderDoctors(list) {
    const container = document.getElementById('doctorList');
    container.innerHTML = '';
    
    list.forEach(doc => {
        const div = document.createElement('div');
        div.className = 'doctor-card';
        div.innerHTML = `
            <h3>${doc.name}</h3>
            <p><strong>Specialty:</strong> ${doc.specialty}</p>
            <p><strong>Experience:</strong> ${doc.experience} Years</p>
            <button class="btn-book" onclick="openBookingModal('${doc.id || doc._id}', '${doc.name}', '${doc.specialty}')">Book Now</button>
        `;
        container.appendChild(div);
    });
}

function openBookingModal(id, name, specialty) {
    selectedDoctor = { id, name, specialty };
    document.getElementById('modalDoctorName').innerText = `Book with ${name}`;
    document.getElementById('modalSpecialtyText').innerText = specialty;
    document.getElementById('bookingModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('bookingModal').style.display = 'none';
    selectedDoctor = null;
}

async function confirmBooking() {
    const patientName = document.getElementById('patientName').value;
    const time = document.getElementById('timeSlot').value;
    const date = new Date().toISOString().slice(0, 10); // Today's date

    if (!patientName) {
        alert('Please enter patient name');
        return;
    }

    const payload = {
        doctorId: selectedDoctor.id,
        doctorName: selectedDoctor.name,
        specialty: selectedDoctor.specialty,
        patientName,
        time,
        date
    };

    try {
        const res = await fetch(`${API_URL}/book`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok) {
            alert('Your appointment is confirmed!');
            closeModal();
            fetchAppointments();
        } else {
            alert(data.msg || 'Booking failed');
        }
    } catch (err) {
        console.error('Error booking:', err);
    }
}

async function fetchAppointments() {
    try {
        const res = await fetch(`${API_URL}/my`);
        const data = await res.json();
        if (Array.isArray(data)) {
            renderAppointments(data);
        }
    } catch (err) {
        console.error('Error fetching appointments:', err);
    }
}

function renderAppointments(list) {
    const container = document.getElementById('appointmentsList');
    container.innerHTML = '';

    if (list.length === 0) {
        container.innerHTML = '<p style="color:#64748b;">No upcoming appointments.</p>';
        return;
    }

    list.forEach(appt => {
        const div = document.createElement('div');
        div.className = 'appt-card';
        div.innerHTML = `
            <div>
                <strong>${appt.doctorName}</strong> (${appt.specialty})<br>
                <span style="font-size:0.85rem; color:#64748b;">${appt.date} at ${appt.time} | Patient: ${appt.patientName}</span>
            </div>
            <button class="cancel-btn" onclick="cancelAppointment('${appt.id || appt._id}')">Cancel</button>
        `;
        container.appendChild(div);
    });
}

async function cancelAppointment(id) {
    if (!confirm('Are you sure you want to cancel this appointment?')) return;
    try {
        const res = await fetch(`${API_URL}/${id}`, { method: 'DELETE' });
        if (res.ok) {
            fetchAppointments();
        }
    } catch (err) {
        console.error('Error cancelling:', err);
    }
}

let searchTimeout;
function debounceSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        const val = document.getElementById('searchInput').value;
        fetchDoctors(val);
    }, 400);
}

// Initial Load
fetchDoctors();
fetchAppointments();
