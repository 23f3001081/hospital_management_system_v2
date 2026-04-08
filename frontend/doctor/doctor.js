const { createApp } = Vue;
createApp({
    data() {
        return {
            token: localStorage.getItem('access_token'),
            error: '', success: '', availability: '', time_availability: '',
            appointments: [], activeApptId: null,
            treatment: { diagnosis: '', prescription: '', notes: '' },
            patients: [], selectedPatient: null, patientHistory: []
        }
    },
    methods: {
        authHeader() { return { 'Authorization': 'Bearer ' + this.token, 'Content-Type': 'application/json' }; },
        logout() { localStorage.clear(); window.location.href = 'index.html'; },
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
            // Gets exactly the next 7 days from Python
            const res = await fetch('http://127.0.0.1:5000/api/doctor/dashboard', { headers: this.authHeader() });
            if (res.ok) this.appointments = await res.json();
            
            const res2 = await fetch('http://127.0.0.1:5000/api/doctor/profile', { headers: this.authHeader() });
            if (res2.ok) {
                const profile = await res2.json();
                this.availability = profile.availability;
                this.time_availability = profile.time_availability;
            }
            this.fetchPatients();
        },
        async updateAvailability() {
            // Calls the PUT route you just wrote
            const res = await fetch('http://127.0.0.1:5000/api/doctor/availability', {
                method: 'PUT', headers: this.authHeader(), body: JSON.stringify({ availability: this.availability })
            });
            if (res.ok) { this.showMsg('success', "Your availability is now live to all patients!"); this.availability = ''; }
        },
        openTreatmentForm(id) {
            this.activeApptId = id;
            this.success = ''; // Clear old success text
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
                this.fetchData(); // Rerender table so it changes from Booked to Completed
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
}).mount('#app');
