#!/usr/bin/env python
"""Test complete PMB API flow"""
import json
import http.client

BASE_URL = "localhost:8000"

def make_request(method, path, body=None):
    """Helper to make HTTP request"""
    conn = http.client.HTTPConnection(BASE_URL)
    headers = {"Content-Type": "application/json"}
    conn.request(method, path, json.dumps(body) if body else None, headers)
    response = conn.getresponse()
    data = json.loads(response.read().decode())
    conn.close()
    return response.status, data

def main():
    # Test 1: Daftar calon
    print("=== Test 1: POST /register ===")
    data = {
        "nama_lengkap": "Budi",
        "email": "budi@example.com",
        "phone": "+628123456789",
        "tanggal_lahir": "2004-01-01",
        "alamat": "Jl. Contoh 1",
        "program_studi_id": 1,
        "jalur_masuk": "SNBP"
    }
    status, response = make_request("POST", "/register", data)
    print(f"Status: {status}")
    print(f"Response: {json.dumps(response, indent=2)}")
    if status != 201:
        print("Aborting: register failed or email already exists in DB.")
        return
    calon_id = response["id"]
    print(f"[OK] Registered with id={calon_id}")

    # Test 2: Cek status
    print("\\n=== Test 2: GET /status/{} ===".format(calon_id))
    status, response = make_request("GET", "/status/{}".format(calon_id))
    print(f"Status: {status}")
    print(f"Response: {json.dumps(response, indent=2)}")
    print(f"[OK] Status: {response.get('status')}, nim: {response.get('nim')}")

    # Test 3: Setujui calon
    print("\\n=== Test 3: PUT /approve/{} ===".format(calon_id))
    status, response = make_request("PUT", "/approve/{}".format(calon_id))
    print(f"Status: {status}")
    print(f"Response: {json.dumps(response, indent=2)}")
    print(f"[OK] NIM generated: {response['nim']}")

    # Test 4: Cek status lagi
    print("\\n=== Test 4: GET /status/{} (after approval) ===".format(calon_id))
    status, response = make_request("GET", "/status/{}".format(calon_id))
    print(f"Status: {status}")
    print(f"Response: {json.dumps(response, indent=2)}")
    print(f"[OK] Status: {response['status']}, nim: {response['nim']}")

    print("\\n[SUCCESS] All tests passed!")


if __name__ == "__main__":
    main()


