const { createApp } = Vue;
createApp({
    data() {
        return {
            currentTab: 'overview',
            token: localStorage.getItem('access_token'),
            error: '', success: '',
            stats: { total_patients: 0, total_doctors: 0, total_appointments: 0 },
            newDoc: { username: '', email: '', password: '', specialization: '', department_name: '', availability: '' },
            appointments: [],
            doctors: [],
            appointmentFilter: 'Booked',
            searchDocQuery: '', docSearchResults: [],
            searchPatQuery: '', patSearchResults: []
        }
    },
    methods: {
        // Helper function
        authHeader() { return { 'Authorization': 'Bearer ' + this.token, 'Content-Type': 'application/json' }; },

        logout() { localStorage.clear(); window.location.href = 'index.html'; },

        async fetchData() {
            try {
                // Pull dashboard API
                const res1 = await fetch('http://127.0.0.1:5000/api/admin/dashboard', { headers: this.authHeader() });
                this.stats = await res1.json();


                const res2 = await fetch('http://127.0.0.1:5000/api/admin/appointments', { headers: this.authHeader() });
                this.appointments = await res2.json();

                // Fetching Doctors for the CRUD table
                const res3 = await fetch('http://127.0.0.1:5000/api/admin/doctors', { headers: this.authHeader() });
                this.doctors = await res3.json();
            } catch (e) { this.error = "Error loading python responses."; }
        },
        async addDoctor() {
            try {
                const payload = {
                    username: this.newDoc.username,
                    email: this.newDoc.email,
                    password: this.newDoc.password,
                    specialization: this.newDoc.specialization,
                    department_name: this.newDoc.department_name,
                    availability: this.newDoc.availability
                };
                const res = await fetch('http://127.0.0.1:5000/api/admin/doctor', {
                    method: 'POST', headers: this.authHeader(), body: JSON.stringify(payload)
                });
                const data = await res.json();
                // Alert the Admin visually and reset the form
                if (res.ok) {
                    this.success = "Success! Give the doctor this temporary password: " + data.generated_password;
                    alert("DOCTOR SAVED SUCCESSFULLY!\n\nEmail: " + this.newDoc.email + "\nTemporary Password: " + data.generated_password);
                    this.newDoc = { username: '', email: '', specialization: '', department_name: '', availability: '' };
                    this.fetchData();
                }
                else if (res.status === 401) {
                    alert("SESSION EXPIRED: Your security token timed out. You will be logged out now. Please log in again.");
                    this.logout();
                }
                else {
                    this.error = data.message || data.msg || "Server rejection";
                    alert("ERROR SAVING DOCTOR: " + this.error);
                }
            } catch (e) {
                this.error = "Failed to run POST.";
                alert("NETWORK ERROR: Cannot reach Python Server.");
            }
            window.scrollTo({ top: 0, behavior: 'smooth' });
        },
        async updateDoctor(doc_id, name, spec, avail) {
            try {
                const res = await fetch('http://127.0.0.1:5000/api/admin/doctor/' + doc_id, {
                    method: 'PUT', headers: this.authHeader(), body: JSON.stringify({ name: name, specialization: spec, availability: avail })
                });
                if (res.ok) { this.success = "Doctor profile instantly updated via DB!"; this.fetchData(); }
                else { const data = await res.json(); this.error = data.message; }
            } catch (e) { this.error = "Network error during PUT request."; }
        },
        async searchDoctors() {
            if (!this.searchDocQuery) return;
            const res = await fetch('http://127.0.0.1:5000/api/admin/doctors/search?q=' + this.searchDocQuery, { headers: this.authHeader() });
            if (res.ok) this.docSearchResults = await res.json();
        },
        async searchPatients() {
            if (!this.searchPatQuery) return;
            const res = await fetch('http://127.0.0.1:5000/api/admin/patients/search?q=' + this.searchPatQuery, { headers: this.authHeader() });
            if (res.ok) this.patSearchResults = await res.json();
        },
        async updatePatient(p) {
            try {
                const res = await fetch('http://127.0.0.1:5000/api/admin/patient/' + p.id, {
                    method: 'PUT', headers: this.authHeader(), body: JSON.stringify({ name: p.name, contact: p.contact, address: p.address })
                });
                if (res.ok) { this.success = "Patient profile instantly updated via DB!"; }
                else { const data = await res.json(); this.error = data.message; }
            } catch (e) { this.error = "Network error during PUT request."; }
        },
        async removeUser(user_id) {
            if (confirm("DANGER: Permanently revoke this doctor's auth and delete their hospital profile? This cannot be undone.")) {
                const res = await fetch('http://127.0.0.1:5000/api/admin/user/' + user_id, { method: 'DELETE', headers: this.authHeader() });
                if (res.ok) { this.success = "Doctor completely erased from the hospital network."; this.fetchData(); }
                else { const data = await res.json(); this.error = data.message; }
            }
        },
        async deleteAppt(id) {
            if (confirm("Permanently erase this booking from the system?")) {
                await fetch('http://127.0.0.1:5000/api/admin/appointment/' + id, { method: 'DELETE', headers: this.authHeader() });
                this.fetchData(); // reload
            }
        },
        async updateAppointmentStatus(id, status) {
            const res = await fetch('http://127.0.0.1:5000/api/appointments/' + id + '/status', {
                method: 'PATCH', headers: this.authHeader(), body: JSON.stringify({ status: status })
            });
            if (res.ok) {
                this.success = 'Appointment status updated successfully!';
                this.fetchData();
            } else {
                const data = await res.json();
                this.error = data.message || 'Failed to update appointment status';
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
        // JWT Role enforcement on frontend before rendering
        if (!this.token || localStorage.getItem('role') !== 'Admin') this.logout();
        else this.fetchData();
    }
}).mount('#app');
