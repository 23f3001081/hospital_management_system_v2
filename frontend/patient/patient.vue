<template>
    <div class="patient-wrapper">
        <nav class="navbar shadow-sm custom-nav mb-4">
            <div class="container-fluid">
                <span class="navbar-brand h1 fw-bold mb-0 text-white">Patient Dashboard</span>
                <button class="btn btn-sm btn-logout-highlight fw-bold px-3 py-1 rounded-pill shadow-sm" @click="logout">Logout</button>
            </div>
        </nav>
        
        <div class="container mt-4">
            <!-- Alerts -->
            <transition name="fade">
                <div v-if="error" class="alert alert-soft-danger shadow-sm border-0">{{ error }}</div>
            </transition>
            <transition name="fade">
                <div v-if="success" class="alert alert-soft-success shadow-sm border-0">{{ success }}</div>
            </transition>
            
            <div class="row mt-4 g-4">
                <!-- Left Column -->
                <div class="col-md-6 mb-4">
                    
                    <!-- Update Profile Card -->
                    <div class="card shadow-sm border-0 soft-card mb-4">
                        <div class="card-header bg-transparent border-0 pt-4 pb-2">
                            <h5 class="mb-0 fw-bold text-soft-dark">Update Profile</h5>
                        </div>
                        <div class="card-body">
                            <form @submit.prevent="updateProfile">
                                <input type="text" class="form-control soft-input mb-3" v-model="profileForm.contact" placeholder="Update Phone Number">
                                <input type="text" class="form-control soft-input mb-3" v-model="profileForm.address" placeholder="Update Address">
                                <button class="btn btn-soft-primary w-100 fw-bold rounded-pill p-2 shadow-sm">Save Changes</button>
                            </form>
                        </div>
                    </div>
                    
                    <!-- Book Appointment Card -->
                    <div class="card shadow-sm border-0 soft-card mb-4">
                        <div class="card-header bg-transparent border-0 pt-4 pb-2">
                            <h5 class="mb-0 fw-bold text-soft-dark">Book an Appointment with Doctor</h5>
                        </div>
                        <div class="card-body">
                            <div class="input-group mb-4 shadow-sm rounded-pill overflow-hidden">
                                <input type="text" class="form-control border-0 px-4" v-model="searchQuery" placeholder="Search specialized doctors...">
                                <button class="btn btn-soft-primary px-4 fw-bold" @click="searchDoctors">Search</button>
                            </div>
                            
                            <!-- Search Results -->
                            <div class="search-results-container pe-2">
                                <div class="card border-0 mb-3 doctor-card shadow-sm" v-for="doc in searchResults" :key="doc.id">
                                    <div class="card-body p-3 d-flex justify-content-between align-items-center">
                                        <div>
                                            <h6 class="mb-1 fw-bold text-soft-dark">{{ doc.name }}</h6>
                                            <p class="mb-1 text-muted small">{{ doc.specialization }} Department</p>
                                            <span class="badge bg-soft-info text-info-dark rounded-pill">Availability: {{ doc.availability }} ({{ doc.time_availability }})</span>
                                        </div>
                                        <button class="btn btn-sm btn-soft-primary rounded-pill px-3 fw-bold shadow-sm" 
                                            @click="selectDoctor(doc)">Select</button>
                                    </div>
                                </div>
                                <div v-if="searchResults.length === 0" class="text-center text-muted py-3">
                                    No doctors found.
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Booking Form (Shows only if doctor selected) -->
                    <transition name="slide-up">
                        <div class="card border-0 shadow-sm mt-3 soft-card booking-card" v-if="targetDoctor">
                            <div class="card-header bg-transparent border-0 pt-4 pb-2 d-flex justify-content-between align-items-center">
                                <h5 class="mb-0 fw-bold text-soft-primary">Book Appointment with {{ targetDoctor.name }}</h5>
                                <button type="button" class="btn-close" aria-label="Close" @click="targetDoctor = null"></button>
                            </div>
                            <div class="card-body pt-0">
                                <div class="alert alert-soft-info border-0 rounded-3 mb-4 text-center">
                                    Doctor Availability:<br><b class="fs-6">{{ targetDoctor.availability }} | {{ targetDoctor.time_availability }}</b>
                                </div>
                                <form @submit.prevent="bookAppt">
                                    <label class="form-label text-muted fw-bold small">Select Date</label>
                                    <input type="date" class="form-control soft-input mb-3 px-3 py-2" v-model="bookForm.date" required>
                                    
                                    <label class="form-label text-muted fw-bold small">Mention Time</label>
                                    <input type="text" class="form-control soft-input mb-4 px-3 py-2" v-model="bookForm.time_slot" placeholder="e.g. 10:00 AM" required>
                                    
                                    <button class="btn btn-soft-primary w-100 fw-bold rounded-pill p-2 shadow-sm">Confirm Appointment</button>
                                </form>
                            </div>
                        </div>
                    </transition>
                    
                </div>
                
                <!-- Right Column -->
                <div class="col-md-6 mb-4">
                    <div class="card shadow-sm border-0 soft-card h-100 d-flex flex-column">
                        <div class="card-header bg-transparent border-0 pt-4 pb-2 d-flex justify-content-between align-items-center">
                            <h5 class="mb-0 fw-bold text-soft-dark">Your Medical Records</h5>
                            <button class="btn btn-sm btn-soft-danger rounded-pill px-3 fw-bold shadow-sm" @click="exportData">
                                Download
                            </button>
                        </div>
                        
                        <div class="card-body flex-grow-1 overflow-auto pe-2" style="max-height: 700px;">
                            <div v-if="history.length === 0" class="text-center text-muted py-5">
                                You have no medical records yet.
                            </div>
                            <!-- Record Items -->
                            <div class="card border-0 shadow-sm bg-white mb-3 record-card rounded-4" v-for="h in history" :key="h.id">
                                <div class="card-body p-4">
                                    <div class="d-flex justify-content-between align-items-start mb-3">
                                        <div>
                                            <h5 class="fw-bold text-soft-dark mb-1">{{ h.date }}</h5>
                                            <p class="text-muted mb-0 small">{{ h.time_slot }} • {{ h.doctor_name }}</p>
                                        </div>
                                        <span class="badge rounded-pill px-3 py-2" 
                                              :class="h.status === 'Completed' ? 'bg-soft-success text-success-dark' : (h.status === 'Cancelled' ? 'bg-soft-danger text-danger-dark' : 'bg-soft-primary text-primary-dark')">
                                            {{ h.status }}
                                        </span>
                                    </div>
                                    
                                    <div v-if="h.treatment" class="treatment-box p-3 rounded-3 mt-3">
                                        <p class="mb-2"><b class="text-soft-primary">Diagnosis:</b> <span class="text-secondary">{{ h.treatment.diagnosis }}</span></p>
                                        <p class="mb-0"><b class="text-soft-primary">Prescription:</b> 
                                            <span class="d-inline-block bg-white px-2 py-1 rounded text-secondary border mt-1 shadow-sm">{{ h.treatment.prescription }}</span>
                                        </p>
                                    </div>
                                    
                                    <div v-if="h.status === 'Booked'" class="mt-4 pt-3 border-top d-flex gap-2">
                                        <button class="btn btn-soft-warning flex-grow-1 rounded-pill fw-bold" @click="openReschedule(h)">Reschedule</button>
                                        <button class="btn btn-soft-danger flex-grow-1 rounded-pill fw-bold" @click="cancelAppt(h.id)">Cancel</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Reschedule Modal Overlay -->
            <transition name="fade">
                <div v-if="rescheduleData" class="reschedule-overlay d-flex align-items-center justify-content-center">
                    <div class="card border-0 shadow-lg soft-card p-2 reschedule-card rounded-4">
                        <div class="card-header bg-transparent border-0 pt-4 pb-2 d-flex justify-content-between align-items-center">
                            <h5 class="mb-0 fw-bold text-soft-dark">Reschedule Appointment</h5>
                            <button type="button" class="btn-close" @click="rescheduleData = null"></button>
                        </div>
                        <div class="card-body">
                            <p class="text-muted small mb-4">With {{ rescheduleData.doctor_name }}</p>
                            <form @submit.prevent="submitReschedule">
                                <label class="form-label fw-bold text-muted small">New Date</label>
                                <input type="date" class="form-control soft-input mb-3 py-2 px-3" v-model="rescheduleForm.date" required>
                                
                                <label class="form-label fw-bold text-muted small">New Time Slot</label>
                                <input type="text" class="form-control soft-input mb-4 py-2 px-3" v-model="rescheduleForm.time_slot" placeholder="e.g. 10:00 AM" required>
                                
                                <button type="submit" class="btn btn-soft-warning w-100 fw-bold rounded-pill p-2 shadow-sm">Confirm Changes</button>
                            </form>
                        </div>
                    </div>
                </div>
            </transition>
            
        </div>
    </div>
</template>

<script>
export default {
    data() {
        return {
            token: localStorage.getItem('access_token'),
            error: '', success: '',
            searchQuery: '', searchResults: [], targetDoctor: null, departments: [],
            bookForm: { date: '', time_slot: '' },
            profileForm: { contact: '', address: '' },
            history: [],
            rescheduleData: null, rescheduleForm: { date: '', time_slot: '' },
        }
    },
    methods: {
        authHeader() { return { 'Authorization': 'Bearer ' + this.token, 'Content-Type': 'application/json' }; },
        logout() { localStorage.clear(); window.location.href = '/index.html'; },
        
        selectDoctor(doc) {
            this.targetDoctor = doc;
        },
        
        async fetchHistory() {
            const res = await fetch('http://127.0.0.1:5000/api/patient/history', { headers: this.authHeader() });
            if (res.ok) this.history = await res.json();
        },
        async fetchDepartments() {
            const res = await fetch('http://127.0.0.1:5000/api/departments');
            if (res.ok) this.departments = await res.json();
        },
        showMsg(type, msg) {
            if (type === 'success') {
                this.success = msg;
                setTimeout(() => { if (this.success === msg) this.success = ''; }, 5000);
            } else {
                this.error = msg;
                setTimeout(() => { if (this.error === msg) this.error = ''; }, 5000);
            }
        },
        async searchDoctors() {
            this.error = '';
            const res = await fetch('http://127.0.0.1:5000/api/patient/doctors/search?q=' + this.searchQuery, { headers: this.authHeader() });
            if (res.ok) this.searchResults = await res.json();
        },
        async bookAppt() {
            const selectedDate = new Date(this.bookForm.date);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            if (selectedDate < today) {
                this.showMsg('error', "Sorry, you cannot book an appointment for a past date.");
                return;
            }

            const payload = { doctor_id: this.targetDoctor.id, ...this.bookForm };
            const res = await fetch('http://127.0.0.1:5000/api/patient/appointments/book', {
                method: 'POST', headers: this.authHeader(), body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (res.ok) {
                this.showMsg('success', "Booked successfully and Doctor has been alerted!");
                this.targetDoctor = null;
                this.bookForm = { date: '', time_slot: '' };
                this.fetchHistory(); 
            } else {
                this.showMsg('error', data.message);
            }
        },
        async exportData() {
            const res = await fetch('http://127.0.0.1:5000/api/patient/export-history', { method: 'POST', headers: this.authHeader() });
            if (res.ok) {
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'Patient_Medical_History_Report.csv';
                document.body.appendChild(a);
                a.click();
                a.remove();
                this.showMsg('success', "Medical Record compiled & downloaded successfully!");
            } else {
                this.showMsg('error', "Failed to download medical records.");
            }
        },
        async updateProfile() {
            const res = await fetch('http://127.0.0.1:5000/api/patient/profile', {
                method: 'PUT', headers: this.authHeader(), body: JSON.stringify(this.profileForm)
            });
            if (res.ok) { 
                this.showMsg('success', "Profile completely updated in the Database!"); 
                this.profileForm = { contact: '', address: '' }; 
            }
        },
        openReschedule(h) {
            this.rescheduleData = h;
            this.rescheduleForm.date = h.date;
            this.rescheduleForm.time_slot = h.time_slot;
            this.error = ''; this.success = '';
        },
        async submitReschedule() {
            const selectedDate = new Date(this.rescheduleForm.date);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            if (selectedDate < today) {
                this.showMsg('error', "Sorry, you cannot reschedule to a past date.");
                return;
            }

            const res = await fetch('http://127.0.0.1:5000/api/patient/appointment/' + this.rescheduleData.id, {
                method: 'PATCH',
                headers: this.authHeader(),
                body: JSON.stringify({
                    date: this.rescheduleForm.date,
                    time_slot: this.rescheduleForm.time_slot
                })
            });
            if (res.ok) {
                this.showMsg('success', "Appointment successfully rescheduled!");
                this.rescheduleData = null;
                this.fetchHistory();
            } else {
                const data = await res.json();
                this.showMsg('error', "Error: " + data.message);
            }
        },
        async cancelAppt(id) {
            if (confirm("Are you sure you want to cancel this appointment?")) {
                const res = await fetch('http://127.0.0.1:5000/api/patient/appointment/' + id, {
                    method: 'PATCH', headers: this.authHeader(), body: JSON.stringify({ status: 'Cancelled' })
                });
                if (res.ok) { this.showMsg('success', "Appointment instantly cancelled!"); this.fetchHistory(); }
            }
        }
    },
    mounted() {
        if (!this.token || localStorage.getItem('role') !== 'Patient') this.logout();
        else { this.fetchHistory(); this.fetchDepartments(); this.searchDoctors(); }
    }
}
</script>

<style scoped>
/* SOFT COLOR PALETTE AND DESIGN SYSTEM */
.patient-wrapper {
    min-height: 100vh;
    background-color: #f8fafb;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    color: #4a5568;
}

.custom-nav {
    background: linear-gradient(135deg, #a8d5e2, #b4e1d1); /* Soft powder blue to mint */
}
.text-soft-dark { color: #2d3748; }
.text-soft-primary { color: #5ea8a0; }

.soft-card {
    background-color: #ffffff;
    border-radius: 1.25rem;
}

/* Inputs */
.soft-input {
    background-color: #f1f5f9;
    border: 1px solid transparent;
    border-radius: 0.75rem;
    color: #4a5568;
    transition: all 0.2s ease;
}
.soft-input:focus {
    background-color: #ffffff;
    border-color: #a8d5e2;
    box-shadow: 0 0 0 4px rgba(168, 213, 226, 0.2);
    outline: none;
}

/* Custom Buttons - Soft UI */
.btn-soft-primary {
    background-color: #8fb9a8; /* soft sage green */
    color: white;
    border: none;
    transition: all 0.2s ease;
}
.btn-soft-primary:hover { background-color: #7ba694; color: white; transform: translateY(-1px); }

.btn-soft-danger {
    background-color: #ffb4a2; /* soft coral pink */
    color: #b74a3f;
    border: none;
    transition: all 0.2s ease;
}
.btn-soft-danger:hover { background-color: #ffa38d; color: #b74a3f; }

.btn-soft-warning {
    background-color: #ffcdb2; /* soft peach */
    color: #b36336;
    border: none;
    transition: all 0.2s ease;
}
.btn-soft-warning:hover { background-color: #ffbc9b; color: #b36336; }

/* Status Badges */
.bg-soft-success { background-color: #d1ebd1 !important; color: #438f43 !important; }
.bg-soft-danger { background-color: #ffe0da !important; color: #d65548 !important; }
.bg-soft-primary { background-color: #e4f3f0 !important; color: #5ea8a0 !important; }
.bg-soft-info { background-color: #dcf2f7 !important; color: #468c9c !important; }

/* Alerts */
.alert-soft-success { background-color: #d1ebd1; color: #438f43; border-radius: 1rem; }
.alert-soft-danger { background-color: #ffe0da; color: #d65548; border-radius: 1rem; }
.alert-soft-info { background-color: #eaf6fc; color: #629dbf; }

/* Treatment Box */
.treatment-box {
    background-color: #f7fafb;
    border-left: 4px solid #a8d5e2;
}

/* Animations */
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.slide-up-enter-active, .slide-up-leave-active { transition: all 0.3s ease; }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translateY(10px); }

/* Reschedule Overlay */
.reschedule-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-color: rgba(45, 55, 72, 0.4);
    z-index: 1050;
    backdrop-filter: blur(4px);
}
.reschedule-card {
    min-width: 350px;
    max-width: 450px;
    width: 100%;
}

/* Scrollbars */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
</style>
