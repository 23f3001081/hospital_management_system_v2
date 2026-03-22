import urllib.request
import urllib.error
import json

BASE_URL = "http://127.0.0.1:5000/api"

def make_request(method, url, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    req_body = json.dumps(data).encode("utf-8") if data else None
    
    req = urllib.request.Request(url, data=req_body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"Error ({e.code}): {e.read().decode('utf-8')}")
        return None

print("============== HMS API AUTOMATED TEST ==============")

# 1. Login as the default Admin
print("\n[1] Logging in as Admin (admin@hms.com / admin123)...")
admin_res = make_request("POST", f"{BASE_URL}/login", {"email": "admin@hms.com", "password": "admin123"})
if not admin_res:
    print("Failed to login! Make sure python init_db.py has been run.")
    exit(1)

admin_token = admin_res.get("access_token")
print("✅ Admin Login Successful! Token Received.")

# 2. Check Admin Dashboard Stats
print("\n[2] Checking Admin Dashboard Stats...")
dash_res = make_request("GET", f"{BASE_URL}/admin/dashboard", None, admin_token)
print(f"✅ Dashboard Data: {dash_res}")

# 3. Create a Doctor to see the random password generator
print("\n[3] Admin Creating a New Doctor (Dr. Demo)...")
doc_data = {
    "username": "DrDemo72",
    "email": "drdemo72@hms.com",
    "specialization": "Neurology",
    "department_name": "Neurology"
}
create_doc_res = make_request("POST", f"{BASE_URL}/admin/doctor", doc_data, admin_token)
new_password = create_doc_res.get("generated_password")
print(f"✅ Doctor Created Successfully!")
print(f"✅ Handoff Password Generated: {new_password}")

# 4. Login as the NEW Doctor using the generated password
print("\n[4] Logging in as the new Doctor using the generated password...")
doc_login_res = make_request("POST", f"{BASE_URL}/login", {"email": "drdemo72@hms.com", "password": new_password})
doc_token = doc_login_res.get("access_token")
print("✅ Doctor Login Successful! Token Received.")

# 5. Access the Doctor's Dashboard
print("\n[5] Accessing the Doctor's Dashboard (Upcoming Appointments)...")
doc_dash_res = make_request("GET", f"{BASE_URL}/doctor/dashboard", None, doc_token)
print(f"✅ Doctor's Upcoming Appointments: {doc_dash_res}")

print("\n================ TEST COMPLETE ===================")
