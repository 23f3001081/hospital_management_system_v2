<template>
    <div>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container-fluid">
                <span class="navbar-brand mb-0 h1">Admin Dashboard</span>
                <div class="navbar-nav ms-auto mb-2 mb-lg-0 align-items-center">
                    <a class="nav-link" href="#" @click.prevent="currentTab='overview'"
                        :class="{active: currentTab==='overview'}">Dashboard</a>
                    <a class="nav-link" href="#" @click.prevent="currentTab='doctors'"
                        :class="{active: currentTab==='doctors'}">Doctor</a>
                    <a class="nav-link" href="#" @click.prevent="currentTab='patients'"
                        :class="{active: currentTab==='patients'}">Patient</a>
                    <button class="btn btn-sm btn-logout-highlight ms-3 px-3 fw-bold" @click="logout">Logout</button>
                </div>
            </div>
        </nav>

        <div class="container mt-4">
            <div v-if="error" class="alert alert-danger">{{ error }}</div>
            <div v-if="success" class="alert alert-success">{{ success }}</div>

            <h3 v-show="currentTab === 'overview'">Overview</h3>
            <div class="row mb-4" v-show="currentTab === 'overview'">
                <div class="col-md-4">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5>Total Patients</h5>
                            <p class="fs-2">{{ stats.total_patients }}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5>Total Doctors</h5>
                            <p class="fs-2">{{ stats.total_doctors }}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5>Total Appointments</h5>
                            <p class="fs-2">{{ stats.total_appointments }}</p>
                        </div>
                    </div>
                </div>
            </div>


            <div class="card mb-4" v-show="currentTab === 'doctors'">
                <div class="card-header bg-primary text-white">Create New Doctor Account</div>
                <div class="card-body">
                    <form @submit.prevent="addDoctor">
                        <div class="row g-3">
                            <div class="col-md-4"><input type="text" class="form-control" v-model="newDoc.username"
                                    placeholder="Doctor Name" required></div>
                            <div class="col-md-4"><input type="email" class="form-control" v-model="newDoc.email"
                                    placeholder="Email Address" required></div>
                            <div class="col-md-4"><input type="password" class="form-control" v-model="newDoc.password"
                                    placeholder="Password" required></div>
                            
                            <div class="col-md-4">
                                <select class="form-select" v-model="newDoc.department_name" required>
                                    <option value="" disabled selected>Select Department</option>
                                    <option value="General Medicine">General Medicine</option>
                                    <option value="Cardiology">Cardiology</option>
                                    <option value="Neurology">Neurology</option>
                                    <option value="Dermatology">Dermatology</option>
                                    <option value="Pediatrics">Pediatrics</option>
                                    <option value="Dentistry">Dentistry</option>
                                </select>
                            </div>
                            <div class="col-md-4">
                                <select class="form-select" v-model="newDoc.availability" required>
                                    <option value="" disabled selected>Availability</option>
                                    <option value="Monday">Monday</option>
                                    <option value="Tuesday">Tuesday</option>
                                    <option value="Wednesday">Wednesday</option>
                                    <option value="Thursday">Thursday</option>
                                    <option value="Friday">Friday</option>
                                    <option value="Saturday">Saturday</option>
                                    <option value="Sunday">Sunday</option>
                                    <option value="Everyday">Everyday (7 Days)</option>
                                </select>
                            </div>
                            <div class="col-md-4">
                                <input type="text" class="form-control" v-model="newDoc.time_availability"
                                    placeholder="10:00 AM - 09:00 PM" required>
                            </div>
                            
                            <div class="col-md-12"><button type="submit" class="btn btn-primary w-100">Save Doctor
                                    Profile</button></div>
                        </div>
                    </form>
                </div>
            </div>

            <!-- Doctors Table -->
            <div class="card mb-4 shadow-sm" v-show="currentTab === 'doctors'">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0">Manage Doctors</h5>
                </div>
                <div class="card-body p-0 table-responsive">
                    <table class="table table-bordered table-striped bg-white mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Doc ID</th>
                                <th>Name</th>
                                <th>Department</th>
                                <th>Availability</th>
                                <th>Time Availability</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="doc in doctors" :key="doc.id">
                                <td>{{ doc.id }}</td>
                                <td>
                                    <template v-if="doc.isEditing">
                                        <input type="text" class="form-control form-control-sm mb-1" v-model="doc.name">
                                        <small class="text-muted">User ID: {{ doc.user_id }}</small>
                                    </template>
                                    <template v-else>
                                        {{ doc.name }}
                                        <br><small class="text-muted">User ID: {{ doc.user_id }}</small>
                                    </template>
                                </td>
                                <td>{{ doc.department }}</td>
                                <td>
                                    <template v-if="doc.isEditing">
                                        <select class="form-select form-select-sm" v-model="doc.availability">
                                            <option value="" disabled>Select Day</option>
                                            <option value="Monday">Monday</option>
                                            <option value="Tuesday">Tuesday</option>
                                            <option value="Wednesday">Wednesday</option>
                                            <option value="Thursday">Thursday</option>
                                            <option value="Friday">Friday</option>
                                            <option value="Saturday">Saturday</option>
                                            <option value="Sunday">Sunday</option>
                                            <option value="Everyday">Everyday</option>
                                        </select>
                                    </template>
                                    <template v-else>
                                        {{ doc.availability || 'Not Set' }}
                                    </template>
                                </td>
                                <td>
                                    <template v-if="doc.isEditing">
                                        <input type="text" class="form-control form-control-sm" v-model="doc.time_availability">
                                    </template>
                                    <template v-else>
                                        {{ doc.time_availability || 'Not Set' }}
                                    </template>
                                </td>
                                <td class="d-flex flex-column gap-2">
                                    <button v-if="!doc.isEditing" class="btn btn-sm btn-primary" @click="doc.isEditing = true">Edit Profile</button>
                                    <button v-if="doc.isEditing" class="btn btn-sm btn-success"
                                        @click="doc.isEditing = false; updateDoctor(doc.id, doc.name, doc.department, doc.availability, doc.time_availability)">Save Profile</button>
                                    <button v-if="doc.isEditing" class="btn btn-sm btn-secondary" @click="doc.isEditing = false">Cancel</button>
                                    <button class="btn btn-sm btn-danger" @click="removeUser(doc.user_id)">Remove Profile</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="row mb-4 mt-4">
                <div class="col-md-12 mb-4" v-show="currentTab === 'doctors'">
                    <div class="card shadow-sm border-0">
                        <div class="card-header bg-primary text-white"><h5 class="mb-0">Search Doctor</h5></div>
                        <div class="card-body">
                            <div class="input-group">
                                <input type="text" class="form-control" v-model="searchDocQuery"
                                    placeholder="Search Doctor...">
                                <button class="btn btn-primary" @click="searchDoctors">Search</button>
                            </div>
                            <ul class="list-group mt-3" v-if="docSearchResults.length">
                                <li class="list-group-item d-flex justify-content-between align-items-center" v-for="d in docSearchResults" :key="d.id">
                                    <div><strong>{{ d.name }}</strong> - {{ d.specialization }}</div>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>

                <div class="col-md-12 mb-4" v-show="currentTab === 'patients'">
                    <div class="card shadow-sm border-0 mb-4">
                        <div class="card-header bg-primary text-white"><h5 class="mb-0">Search Patients</h5></div> 
                        <div class="card-body">
                            <div class="input-group mb-3">
                                <input type="text" class="form-control" v-model="searchPatQuery"
                                    placeholder="Search Patients">
                                <button class="btn btn-primary" @click="searchPatients">Search</button>
                            </div>
                            <ul class="list-group" v-if="patSearchResults.length">
                                <li class="list-group-item bg-light" v-for="p in patSearchResults" :key="p.id">
                                    <div class="d-flex align-items-center gap-2">
                                        <input type="text" class="form-control" v-model="p.name"
                                            placeholder="Name">
                                        <input type="text" class="form-control" v-model="p.contact"
                                            placeholder="Contact">
                                        <input type="text" class="form-control" v-model="p.address"
                                            placeholder="Address">
                                        <div class="d-flex flex-column gap-2">
                                            <button class="btn btn-sm btn-success px-4 fw-bold" @click="updatePatient(p)">Save</button>
                                            <button class="btn btn-sm btn-danger px-4 fw-bold" @click="removeUser(p.user_id)">Remove</button>
                                        </div>
                                    </div>
                                </li>
                            </ul>
                        </div>
                    </div>

                    <!--PATIENTS TABLE -->
                    <div class="card shadow-sm border-0">
                        <div class="card-header bg-primary text-white"><h5 class="mb-0">All Registered Patients</h5></div>
                        <div class="card-body p-0 table-responsive">
                            <table class="table table-striped table-hover bg-white mb-0">
                                <thead class="table-light">
                                    <tr>
                                        <th>PID</th>
                                        <th>Name</th>
                                        <th>Email</th>
                                        <th>Contact</th>
                                        <th>Address</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-for="pat in patients" :key="pat.id">
                                        <td>{{ pat.id }}</td>
                                        <td>
                                            <input type="text" class="form-control form-control-sm" v-model="pat.name">
                                        </td>
                                        <td>{{ pat.email }}</td>
                                        <td>
                                            <input type="text" class="form-control form-control-sm" v-model="pat.contact">
                                        </td>
                                        <td>
                                            <input type="text" class="form-control form-control-sm" v-model="pat.address">
                                        </td>
                                        <td class="d-flex flex-column gap-2">
                                            <button class="btn btn-sm btn-success w-100 fw-bold" @click="updatePatient(pat)">Save</button>
                                            <button class="btn btn-sm btn-danger w-100 fw-bold" @click="removeUser(pat.user_id)">Remove</button>
                                        </td>
                                    </tr>
                                    <tr v-if="patients.length === 0">
                                        <td colspan="6" class="text-center text-muted py-3">No patients registered.</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- View Appointments  -->
            <div class="card mb-4 shadow-sm border-0" v-show="currentTab === 'overview'">
                <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center rounded-top-4">
                    <h5 class="mb-0 fw-bold">Hospital Appointments Overview</h5>
                    <div class="d-flex gap-3 align-items-center">
                        <label class="mb-0 fw-bold small">Filter Status:</label>
                        <select class="form-select form-select-sm w-auto border-0 shadow-sm" v-model="appointmentFilter">
                            <option value="All">All Appointments</option>
                            <option value="Booked">Booked</option>
                            <option value="Completed">Completed</option>
                            <option value="Cancelled">Cancelled</option>
                        </select>
                    </div>
                </div>
                <div class="card-body p-0 table-responsive">
                    <table class="table table-striped table-hover bg-white mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>ID</th>
                                <th>Doctor</th>
                                <th>Patient</th>
                                <th>Date</th>
                                <th>Time</th>
                                <th>Status</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="appt in filteredAppointments" :key="appt.id">
                                <td>{{ appt.id }}</td>
                                <td><strong>{{ appt.doctor }}</strong></td>
                                <td>{{ appt.patient }}</td>
                                <td>{{ appt.date }}</td>
                                <td><span class="badge bg-secondary">{{ appt.time_slot }}</span></td>
                                <td>
                                    <span class="badge" :class="{'bg-success': appt.status === 'Completed', 'bg-warning text-dark': appt.status === 'Cancelled', 'bg-primary': appt.status === 'Booked'}">
                                        {{ appt.status }}
                                    </span>
                                </td>
                                <td class="d-flex flex-column gap-2">

                                    <button v-if="appt.status !== 'Cancelled'" class="btn btn-sm btn-outline-warning fw-bold text-dark"
                                        @click="updateAppointmentStatus(appt.id, 'Cancelled')">Cancel Appointment</button>
                                    <button class="btn btn-sm btn-danger fw-bold" @click="deleteAppt(appt.id)">Remove Record</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    data() {
        return {
            currentTab: 'overview',
            token: localStorage.getItem('access_token'),
            error: '', success: '',
            stats: { total_patients: 0, total_doctors: 0, total_appointments: 0 },
            newDoc: { username: '', email: '', password: '', specialization: '', department_name: '', availability: '', time_availability: '' },
            appointments: [],
            doctors: [],
            appointmentFilter: 'Booked',
            searchDocQuery: '', docSearchResults: [],
            searchPatQuery: '', patSearchResults: [],
            patients: []
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
            try {
                const res1 = await fetch('http://127.0.0.1:5000/api/admin/dashboard', { headers: this.authHeader() });
                this.stats = await res1.json();

                const res2 = await fetch('http://127.0.0.1:5000/api/admin/appointments', { headers: this.authHeader() });
                this.appointments = await res2.json();

                const res3 = await fetch('http://127.0.0.1:5000/api/admin/doctors', { headers: this.authHeader() });
                this.doctors = await res3.json();

                const res4 = await fetch('http://127.0.0.1:5000/api/admin/patients', { headers: this.authHeader() });
                this.patients = await res4.json();
            } catch (e) { this.showMsg('error', "Loading data..."); } 
        },
        async addDoctor() {
            try {
                const payload = {
                    username: this.newDoc.username,
                    email: this.newDoc.email,
                    password: this.newDoc.password,
                    specialization: this.newDoc.department_name || 'General',
                    department_name: this.newDoc.department_name,
                    availability: this.newDoc.availability,
                    time_availability: this.newDoc.time_availability
                };
                const res = await fetch('http://127.0.0.1:5000/api/admin/doctor', {
                    method: 'POST', headers: this.authHeader(), body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok) {
                    this.showMsg("Password for Doctor: " + data.generated_password); 
                    alert("DOCTOR SAVED SUCCESSFULLY!\n\nEmail: " + this.newDoc.email + "\nPassword: " + data.generated_password);
                    this.newDoc = { username: '', email: '', password: '', department_name: '', availability: '', time_availability: '' };
                    this.fetchData();
                }
                else if (res.status === 401) {
                    alert("SESSION EXPIRED:You will be logged out now. Please log in again.");
                    this.logout();
                }
                else {
                    this.showMsg('error', data.message || data.msg || "Server rejection");
                    alert("ERROR SAVING DOCTOR: " + (data.message || data.msg || "Server rejection"));
                }
            } catch (e) {
                this.showMsg('error', "Failed to run POST.");
                alert("NETWORK ERROR: Cannot reach Server.");
            }
            window.scrollTo({ top: 0, behavior: 'smooth' });
        },
        async updateDoctor(doc_id, name, spec, avail, time_avail) {
            try {
                const res = await fetch('http://127.0.0.1:5000/api/admin/doctor/' + doc_id, {
                    method: 'PUT', headers: this.authHeader(), body: JSON.stringify({ name: name, specialization: spec, availability: avail, time_availability: time_avail })
                });
                if (res.ok) { this.showMsg("Doctor profile updated!"); this.fetchData(); }
                else { const data = await res.json(); this.showMsg('error', data.message); }
            } catch (e) { this.showMsg('error', "Network error."); }
        },
        async searchDoctors() {
            if (!this.searchDocQuery) return;
            const res = await fetch('http://127.0.0.1:5000/api/admin/doctors/search?q=' + this.searchDocQuery, { headers: this.authHeader() });
            if (res.ok) {
                this.docSearchResults = await res.json();
                if (this.docSearchResults.length === 0) {
                    alert('No doctor found');
                }
            }
        },
        async searchPatients() {
            if (!this.searchPatQuery) return;
            const res = await fetch('http://127.0.0.1:5000/api/admin/patients/search?q=' + this.searchPatQuery, { headers: this.authHeader() });
            if (res.ok) {
                this.patSearchResults = await res.json();
                if (this.patSearchResults.length === 0) {
                    alert('Patient not found');
                }
            }
        },
        async updatePatient(p) {
            try {
                const res = await fetch('http://127.0.0.1:5000/api/admin/patient/' + p.id, {
                    method: 'PUT', headers: this.authHeader(), body: JSON.stringify({ name: p.name, contact: p.contact, address: p.address })
                });
                if (res.ok) { this.showMsg('success',"Patient profile updated."); }
                else { const data = await res.json(); this.showMsg('error', data.message); }
            } catch (e) { this.showMsg('error', "Network error"); }
        },
        async removeUser(user_id) {
            if (confirm("DANGER: Permanently remove this doctor's profile?")) {
                const res = await fetch('http://127.0.0.1:5000/api/admin/user/' + user_id, { method: 'DELETE', headers: this.authHeader() });
                if (res.ok) { this.showMsg("Doctor removed from the hospital records."); this.fetchData(); }
                else { const data = await res.json(); this.showMsg('error', data.message); }
            }
        },
        async deleteAppt(id) {
            if (confirm("Erase this booking?")) {
                await fetch('http://127.0.0.1:5000/api/admin/appointment/' + id, { method: 'DELETE', headers: this.authHeader() });
                this.fetchData(); 
            }
        },
        async updateAppointmentStatus(id, status) {
            const res = await fetch('http://127.0.0.1:5000/api/appointments/' + id + '/status', {
                method: 'PATCH', headers: this.authHeader(), body: JSON.stringify({ status: status })
            });
            if (res.ok) {
                this.showMsg('Appointment updated successfully!');
                this.fetchData();
            } else {
                const data = await res.json();
                this.showMsg('error', data.message || 'Failed to update appointment');
            }
        }
    },
    computed: {
        filteredAppointments() {
            if (this.appointmentFilter === 'All') return this.appointments;
            return this.appointments.filter(a => a.status === this.appointmentFilter);
        }
    },
    mounted() {
        if (!this.token || localStorage.getItem('role') !== 'Admin') this.logout();
        else this.fetchData();
    }
}
</script>
