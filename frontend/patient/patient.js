const { createApp } = Vue;

createApp({
    data() {
        return {
            token: localStorage.getItem('access_token'),
            error: '', success: '',
            searchQuery: '', searchResults: [], targetDoctor: null, departments: [],
            bookForm: { date: '', time_slot: '' },
            profileForm: { contact: '', address: '' },
            history: [], showPayment: false,
            rescheduleData: null, rescheduleForm: { date: '', time_slot: '' }
        }
    },
    methods: {
        authHeader() { return { 'Authorization': 'Bearer ' + this.token, 'Content-Type': 'application/json' }; },
        logout() { localStorage.clear(); window.location.href = 'index.html'; },
        async fetchHistory() {
            // Fetch the medical data mapping from the secure python route
            const res = await fetch('http://127.0.0.1:5000/api/patient/history', { headers: this.authHeader() });
            if (res.ok) this.history = await res.json();
        },
        async fetchDepartments() {
            const res = await fetch('http://127.0.0.1:5000/api/departments'); // public route
            if (res.ok) this.departments = await res.json();
        },
        async searchDoctors() {
            this.error = '';
            // The URL query string hitting the python search endpoint
            const res = await fetch('http://127.0.0.1:5000/api/patient/doctors/search?q=' + this.searchQuery, { headers: this.authHeader() });
            if (res.ok) this.searchResults = await res.json();
        },
        async bookAppt() {
            const payload = { doctor_id: this.targetDoctor, ...this.bookForm };
            const res = await fetch('http://127.0.0.1:5000/api/patient/appointments/book', {
                method: 'POST', headers: this.authHeader(), body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (res.ok) {
                this.success = "Booked successfully and Doctor has been alerted!";
                this.targetDoctor = null;
                this.fetchHistory(); // Reload visual data
            } else {
                this.error = data.message; // 400 Bad Request error if Time Slot exists!
            }
        },
        openPayment() { this.showPayment = true; },
        processPayment() {
            this.success = "Dummy transaction passed! Your balance is now $0.";
            this.showPayment = false;
        },
        async exportData() {
            // Call the python route. Because the python route uses `export_treatment_csv.delay()`, 
            // this Javascript fetch finishes instantly!
            const res = await fetch('http://127.0.0.1:5000/api/patient/export-history', { method: 'POST', headers: this.authHeader() });
            if (res.ok) this.success = "Success! The Celery worker is currently compiling your CSV document in the background. It will show up in the python exports/ folder momentarily!";
        },
        async updateProfile() {
            const res = await fetch('http://127.0.0.1:5000/api/patient/profile', {
                method: 'PUT', headers: this.authHeader(), body: JSON.stringify(this.profileForm)
            });
            if (res.ok) { this.success = "Profile completely updated in the Database!"; this.profileForm = { contact: '', address: '' }; }
        },
        openReschedule(h) {
            this.rescheduleData = h;
            this.rescheduleForm.date = h.date;
            this.rescheduleForm.time_slot = h.time_slot;
            this.error = ''; this.success = '';
        },
        async submitReschedule() {
            const res = await fetch('http://127.0.0.1:5000/api/patient/appointment/' + this.rescheduleData.id, {
                method: 'PATCH',
                headers: this.authHeader(),
                body: JSON.stringify({
                    date: this.rescheduleForm.date,
                    time_slot: this.rescheduleForm.time_slot
                })
            });
            if (res.ok) {
                this.success = "Appointment successfully rescheduled!";
                this.rescheduleData = null;
                this.fetchHistory();
            } else {
                const data = await res.json();
                this.error = "Error: " + data.message;
            }
        },
        async cancelAppt(id) {
            if (confirm("Are you sure you want to cancel this appointment?")) {
                const res = await fetch('http://127.0.0.1:5000/api/patient/appointment/' + id, {
                    method: 'PATCH', headers: this.authHeader(), body: JSON.stringify({ status: 'Cancelled' })
                });
                if (res.ok) { this.success = "Appointment instantly cancelled!"; this.fetchHistory(); }
            }
        }
    },
    mounted() {
        // Force user back to index.html if they try to access this without a JWT token!
        if (!this.token || localStorage.getItem('role') !== 'Patient') this.logout();
        else { this.fetchHistory(); this.fetchDepartments(); this.searchDoctors(); }
    }
}).mount('#app');
