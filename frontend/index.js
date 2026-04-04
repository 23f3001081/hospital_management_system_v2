const { createApp } = Vue;
createApp({
    data() { return {
        view: 'login', error: '', success: '',
        loginForm: { email: '', password: '' },
        registerForm: { username: '', email: '', password: '', contact: '', address: '' }
    }},
    methods: {
        async login() {
            try {
                const res = await fetch('http://127.0.0.1:5000/api/login', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(this.loginForm)
                });
                const data = await res.json();
                
                if (res.ok) {
                    localStorage.setItem('access_token', data.access_token);
                    localStorage.setItem('role', data.role);
                    this.success = 'Login Successful!';
                    setTimeout(() => {
                        if (data.role === 'Admin') window.location.href = 'admin_dashboard.html';
                        if (data.role === 'Doctor') window.location.href = 'doctor_dashboard.html';
                        if (data.role === 'Patient') window.location.href = 'patient_dashboard.html';
                    }, 500);
                } else { this.error = data.message; }
            } catch { this.error = 'Network Error'; }
        },
        async register() {
            try {
                const res = await fetch('http://127.0.0.1:5000/api/register', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(this.registerForm)
                });
                if (res.ok) { this.success = 'Registered! Please log in.'; this.view = 'login'; }
                else { const data = await res.json(); this.error = data.message; }
            } catch { this.error = 'Network Error'; }
        }
    }
}).mount('#app');
