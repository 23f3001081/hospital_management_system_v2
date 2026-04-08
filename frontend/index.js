const { createApp } = Vue;
createApp({
    data() { return {
        view: 'login', error: '', success: '',
        loginForm: { email: '', password: '' },
        registerForm: { username: '', email: '', password: '', contact: '', address: '' }
    }},
    methods: {
        showMsg(type, msg) {
            if (type === 'success') {
                this.success = msg;
                setTimeout(() => { if (this.success === msg) this.success = ''; }, 5000);
            } else {
                this.error = msg;
                setTimeout(() => { if (this.error === msg) this.error = ''; }, 5000);
            }
        },
        async login() {
            try {
                const res = await fetch('http://127.0.0.1:5000/api/login', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(this.loginForm)
                });
                const data = await res.json();
                
                if (res.ok) {
                    localStorage.setItem('access_token', data.access_token);
                    localStorage.setItem('role', data.role);
                    this.showMsg('success', 'Login Successful!');
                    setTimeout(() => {
                        if (data.role === 'Admin') window.location.href = 'admin_dashboard.html';
                        if (data.role === 'Doctor') window.location.href = 'doctor_dashboard.html';
                        if (data.role === 'Patient') window.location.href = 'patient_dashboard.html';
                    }, 500);
                } else { this.showMsg('error', data.message); }
            } catch { this.showMsg('error', 'Network Error'); }
        },
        async register() {
            try {
                const res = await fetch('http://127.0.0.1:5000/api/register', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(this.registerForm)
                });
                if (res.ok) { this.showMsg('success', 'Registered! Please log in.'); this.view = 'login'; }
                else { const data = await res.json(); this.showMsg('error', data.message); }
            } catch { this.showMsg('error', 'Network Error'); }
        }
    }
}).mount('#app');
