# Hospital Management System (HMS) v2

A dynamic, full-stack Hospital Management platform designed to streamline medical administration. This system features three distinct Role-Based Access portals: an **Admin Dashboard** for creating doctors and analyzing hospital statistics, a **Doctor Dashboard** for managing appointments and charting patient treatments, and a **Patient Dashboard** for booking schedules and downloading CSV medical histories.

## 🚀 Technical Stack
- **Backend:** Python, Flask (RESTful API), SQLite (Primary DB), Redis (Caching & Job Broker)
- **Frontend:** Vue 3 (SFC Loader), Bootstrap 5, Vanilla CSS
- **Async Execution:** Celery (Worker & Beat)

## 🛠️ Project Setup

### 1. Requirements
Ensure you have **Redis** installed and running on your system (Default port `6379`).

### 2. Installation
1. Clone the repository.
2. Initialize a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Database Initialization
Run the initialization script to set up the SQLite database and create the default Admin account.
```bash
cd backend
python init_db.py
```
**Admin Credentials:**
- Email: `admin@hms.com`
- Password: `admin123`

## 🏃 Running the Application
To run the full system, you need to open **four terminal windows**:

1. **Redis Server**: Start your local Redis instance.
2. **Flask Backend**:
   ```bash
   cd backend
   python app.py
   ```
3. **Celery Worker**:
   ```bash
   cd backend
   celery -A app.celery_app worker --loglevel=info --pool=solo
   ```
4. **Celery Beat**:
   ```bash
   cd backend
   celery -A app.celery_app beat --loglevel=info
   ```

## 📂 Project Structure
- `backend/`: Flask application, models, and background tasks.
- `frontend/`: Vue.js components and HTML entry points.
- `static_url_path`: Configured to serve `frontend/` from the root.

---
Built with modern web standards and Agentic AI assistance.