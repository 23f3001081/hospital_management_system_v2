<template>
    <div>
        <nav class="navbar navbar-dark bg-primary shadow-sm mb-4">
            <div class="container-fluid">
                <span class="navbar-brand text-white fw-bold h1 mt-1">
                    {{ doctorName }} | <small class="fw-normal">{{ specialization }} Department</small>
                </span>
                <button class="btn btn-sm btn-logout-highlight px-3 fw-bold shadow-sm" @click="logout">Logout</button>
            </div>
        </nav>

        <div class="container mt-4">
            <div v-if="error" class="alert alert-danger">{{ error }}</div>
            <div v-if="success" class="alert alert-success">{{ success }}</div>

            <!-- Page Title -->
            <div class="mb-4 mt-3">
                <h4 class="text-secondary fw-bold"></h4>
            </div>

            <!-- Easy Availability Update Form -->
            <div class="card mb-4 shadow-sm border-0">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0">Availability</h5>
                </div>
                <div class="card-body">
                    <div class="alert alert-info d-flex align-items-center">
                        <div class="me-auto">
                            <strong>Working Days:</strong> {{ availability || 'Not Set' }} <br>
                            <strong>Working Hours:</strong> {{ time_availability || 'Not Set' }}
                            <div class="small mt-1 text-muted"></div>
                        </div>
                    </div>
                    <form @submit.prevent="updateAvailability" class="mt-3">
                        <label class="form-label fw-bold">Update Working Day</label>
                        <div class="d-flex gap-2">
                            <select class="form-select w-50" v-model="availability" required>
                                <option value="" disabled selected>Select availability </option>
                                <option value="Monday">Monday</option>
                                <option value="Tuesday">Tuesday</option>
                                <option value="Wednesday">Wednesday</option>
                                <option value="Thursday">Thursday</option>
                                <option value="Friday">Friday</option>
                                <option value="Saturday">Saturday</option>
                                <option value="Sunday">Sunday</option>
                                <option value="Everyday">Everyday</option>
                            </select>
                            <button class="btn btn-primary px-4">Update Day</button>
                        </div>
                    </form>
                </div>
            </div>

            <!-- Very simple table structure -->
            <div class="card shadow-sm border-0 mb-4">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0">Patient Appointments</h5>
                </div>
                <div class="card-body p-0 table-responsive">
                    <table class="table table-striped table-hover bg-white mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Appt ID</th>
                                <th>Patient Name</th>
                                <th>Visit Date</th>
                                <th>Visit Time</th>
                                <th>Current Status</th>
                                <th>Update Profile</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="appt in appointments" :key="appt.id">
                                <td>{{ appt.id }}</td>
                                <td>{{ appt.patient_name }}</td>
                                <td><b>{{ appt.date }}</b></td>
                                <td><span class="badge bg-secondary">{{ appt.time_slot }}</span></td>
                                <td>
                                    <span class="badge"
                                        :class="{'bg-success': appt.status === 'Completed', 'bg-warning text-dark': appt.status === 'Cancelled', 'bg-primary': appt.status === 'Booked'}">
                                        {{ appt.status }}
                                    </span>
                                </td>
                                <td class="d-flex flex-column gap-2">
                                    <button v-if="appt.status === 'Booked'"
                                        class="btn btn-sm btn-outline-primary fw-bold"
                                        @click="openTreatmentForm(appt)">Complete & Prescribe</button>
                                    <button v-if="appt.status === 'Booked'"
                                        class="btn btn-sm btn-outline-danger fw-bold"
                                        @click="cancelAppt(appt.id)">Cancel Appointment</button>
                                </td>
                            </tr>
                            <tr v-if="appointments.length === 0">
                                <td colspan="6" class="text-center text-muted py-3">No upcoming appointments!</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Treatment Form Card (Only shows when button gives it an ID) -->
            <div class="card border-0 mb-4 shadow-sm" v-if="activeApptId">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0 fw-bold">Prescribing for {{ activePatientName }}</h5>
                </div>
                <div class="card-body">
                    <form @submit.prevent="saveTreatment">
                        <div class="mb-3">
                            <label class="form-label">Medical Diagnosis</label>
                            <input type="text" class="form-control" v-model="treatment.diagnosis"
                                placeholder="What is wrong?" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Medical Prescription</label>
                            <input type="text" class="form-control" v-model="treatment.prescription"
                                placeholder="What medicine?" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Extra Notes (Optional)</label>
                            <textarea class="form-control" v-model="treatment.notes"></textarea>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Save & Mark
                            Completed</button>
                    </form>
                </div>
            </div>

            <div class="card shadow-sm border-0 mb-4">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0">Patients Medical History</h5>
                </div>
                <div class="card-body">
                    <ul class="list-group" v-if="patients.length > 0">
                        <li class="list-group-item d-flex justify-content-between align-items-center bg-light"
                            v-for="pat in patients" :key="pat.patient_id">
                            <span><strong>{{ pat.name }}</strong> <span class="text-muted">(Contact: {{ pat.contact
                                    }})</span></span>
                            <button class="btn btn-sm btn-primary px-3" @click="viewPatientHistory(pat)">View
                                History</button>
                        </li>
                    </ul>
                    <div v-else class="text-center text-muted py-2">
                        No patients assigned currently.
                    </div>
                </div>
            </div>

            <div class="card border-0 mb-4 shadow-sm" v-if="selectedPatient">
                <div class="card-header bg-info-dark text-white">
                    <h5 class="mb-0"> Medical History for {{ selectedPatient.name }}</h5>
                </div>
                <div class="card-body bg-light">
                    <ul class="list-group shadow-sm">
                        <li class="list-group-item p-3 mb-2 border-0 rounded" v-for="h in patientHistory" :key="h.id">
                            <div class="row align-items-center border-bottom pb-2 mb-3 bg-white p-2 rounded shadow-sm">
                                <div class="col text-center">
                                    <span class="text-muted small d-block text-uppercase fw-bold">Date</span>
                                    <span class="fw-bold">{{ h.date }}</span>
                                </div>
                                <div class="col text-center border-start border-end">
                                    <span class="text-muted small d-block text-uppercase fw-bold">Time</span>
                                    <span class="badge bg-secondary">{{ h.time_slot }}</span>
                                </div>
                                <div class="col text-center">
                                    <span class="text-muted small d-block text-uppercase fw-bold">Status</span>
                                    <span class="badge" :class="{'bg-success': h.status === 'Completed', 'bg-warning text-dark': h.status === 'Cancelled', 'bg-primary': h.status === 'Booked'}">{{ h.status }}</span>
                                </div>
                            </div>
                            
                            <div v-if="h.treatment" class="text-muted border p-3 rounded bg-white shadow-sm">
                                <strong class="text-info">Diagnosis:</strong> {{ h.treatment.diagnosis }}<br>
                                <strong class="text-info mt-2 d-inline-block">Prescription:</strong> {{ h.treatment.prescription }}<br>
                                <strong class="text-info mt-2 d-inline-block">Notes:</strong> {{ h.treatment.notes }}
                            </div>
                            <button v-if="h.treatment || h.status === 'Completed'"
                                class="btn btn-sm btn-outline-warning mt-3 fw-bold shadow-sm" @click="editHistory(h)">Edit Notes</button>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    data() {
        return {
            token: localStorage.getItem('access_token'),
            error: '', success: '', availability: '', time_availability: '',
            doctorName: '', specialization: '',
            appointments: [], activeApptId: null, activePatientName: '',
            treatment: { diagnosis: '', prescription: '', notes: '' },
            patients: [], selectedPatient: null, patientHistory: []
        }
    },
    methods: {
        authHeader() { return { 'Authorization': 'Bearer ' + this.token, 'Content-Type': 'application/json' }; },
        logout() { localStorage.clear(); window.location.href = '/index.html'; },
        showMsg(type, msg) {
            if (type === 'success') {
                this.success = msg;
                setTimeout(() => { if (this.success === msg) this.success = ''; }, 5000);
            } else {
                this.error = msg;
                setTimeout(() => { if (this.error === msg) this.error = ''; }, 5000);
            }
        },
        async fetchData() {
            const res = await fetch('http://127.0.0.1:5000/api/doctor/dashboard', { headers: this.authHeader() });
            if (res.ok) this.appointments = await res.json();
            
            const res2 = await fetch('http://127.0.0.1:5000/api/doctor/profile', { headers: this.authHeader() });
            if (res2.ok) {
                const profile = await res2.json();
                this.doctorName = profile.name;
                this.specialization = profile.specialization;
                this.availability = profile.availability;
                this.time_availability = profile.time_availability;
            }
            this.fetchPatients();
        },
        async updateAvailability() {
            const res = await fetch('http://127.0.0.1:5000/api/doctor/availability', {
                method: 'PUT', headers: this.authHeader(), body: JSON.stringify({ availability: this.availability })
            });
            if (res.ok) { this.showMsg('success', "Your availability is now live to all patients!"); this.availability = ''; }
        },
        openTreatmentForm(appt) {
            this.activeApptId = appt.id;
            this.activePatientName = appt.patient_name;
            this.success = '';
        },
        async saveTreatment() {
            const payload = { appointment_id: this.activeApptId, ...this.treatment };
            const res = await fetch('http://127.0.0.1:5000/api/doctor/treatment', {
                method: 'POST', headers: this.authHeader(), body: JSON.stringify(payload)
            });
            if (res.ok) {
                this.showMsg('success', "Medical record encrypted and saved!");
                this.activeApptId = null;
                this.treatment = { diagnosis: '', prescription: '', notes: '' };
                this.fetchData();
                if (this.selectedPatient) this.viewPatientHistory(this.selectedPatient);
            } else {
                const data = await res.json();
                this.showMsg('error', data.message);
            }
        },
        async fetchPatients() {
            const res = await fetch('http://127.0.0.1:5000/api/doctor/patients', { headers: this.authHeader() });
            if (res.ok) this.patients = await res.json();
        },
        async cancelAppt(id) {
            if (confirm("Are you sure you want to cancel this appointment?")) {
                const res = await fetch('http://127.0.0.1:5000/api/doctor/appointment/' + id, {
                    method: 'PATCH', headers: this.authHeader(), body: JSON.stringify({ status: 'Cancelled' })
                });
                if (res.ok) { this.showMsg('success', "Appointment instantly cancelled!"); this.fetchData(); }
                else { const data = await res.json(); this.showMsg('error', data.message); }
            }
        },
        async viewPatientHistory(pat) {
            this.selectedPatient = pat;
            const res = await fetch('http://127.0.0.1:5000/api/patient/' + pat.patient_id + '/history', { headers: this.authHeader() });
            if (res.ok) {
                const data = await res.json();
                this.patientHistory = data.history;
            }
        },
        editHistory(h) {
            this.activeApptId = h.id;
            this.activePatientName = this.selectedPatient ? this.selectedPatient.name : 'Unknown';
            this.treatment = {
                diagnosis: h.treatment ? h.treatment.diagnosis : '',
                prescription: h.treatment ? h.treatment.prescription : '',
                notes: h.treatment ? h.treatment.notes : ''
            };
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    },
    mounted() {
        if (!this.token || localStorage.getItem('role') !== 'Doctor') this.logout();
        else this.fetchData();
    }
}
</script>
