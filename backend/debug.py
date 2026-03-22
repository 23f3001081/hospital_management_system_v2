import urllib.request
import json

def test_add_doctor():
    # 1. Login
    login_req = urllib.request.Request(
        'http://127.0.0.1:5000/api/login',
        data=json.dumps({'email': 'admin@hms.com', 'password': 'admin123'}).encode('utf8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        login_res = urllib.request.urlopen(login_req)
        token = json.loads(login_res.read())['access_token']
        print(f"Login success! Token: {token[:10]}...")
    except urllib.error.HTTPError as e:
        print(f"Login failed: {e.code} {e.read()}")
        return

    # 2. Add doctor
    doc_req = urllib.request.Request(
        'http://127.0.0.1:5000/api/admin/doctor',
        data=json.dumps({'username': 'testdoctor5', 'email': 'test5@hms.com', 'department_name': 'Cardiology', 'specialization': 'General Physician'}).encode('utf8'),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
    )
    try:
        doc_res = urllib.request.urlopen(doc_req)
        print("Success:", doc_res.read().decode('utf8'))
    except urllib.error.HTTPError as e:
        print("Error HTTP Code:", e.code)
        print("Error Body:", e.read().decode('utf8'))

test_add_doctor()
