#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:8000"

print("\n" + "="*70)
print("TEST 1: REGISTER NEW APPLICANT")
print("="*70)

data = {
    "nama_lengkap": "Budi Santoso",
    "email": "budi.santoso@example.com",
    "phone": "081234567890",
    "tanggal_lahir": "2005-01-15",
    "alamat": "Jalan Merdeka No. 123",
    "program_studi_id": 1,
    "jalur_masuk_id": 1
}

response = requests.post(f"{BASE_URL}/api/pmb/register", json=data)
print(f"Status: {response.status_code}")
result = response.json()
print(json.dumps(result, indent=2, default=str))

if response.status_code == 201:
    calon_id = result["id"]
    print(f"[OK] Calon ID: {calon_id}")

# TEST 2: Duplicate email
print("\n" + "="*70)
print("TEST 2: TRY DUPLICATE EMAIL (Should fail with 409)")
print("="*70)

response = requests.post(f"{BASE_URL}/api/pmb/register", json=data)
print(f"Status: {response.status_code}")
if response.status_code == 409:
    print("[OK] Duplicate email properly rejected")

# TEST 3: Get status before approval
print("\n" + "="*70)
print("TEST 3: GET STATUS (Should be PENDING)")
print("="*70)

response = requests.get(f"{BASE_URL}/api/pmb/status/{calon_id}")
print(f"Status: {response.status_code}")
result = response.json()
print(f"Calon Status: {result['status']}")
print(f"NIM: {result['nim']}")

# TEST 4: Approve and generate NIM
print("\n" + "="*70)
print("TEST 4: APPROVE & GENERATE NIM")
print("="*70)

approve_data = {"keterangan": "Lulus seleksi masuk"}
response = requests.put(f"{BASE_URL}/api/pmb/approve/{calon_id}", json=approve_data)
print(f"Status: {response.status_code}")
result = response.json()
print(json.dumps(result, indent=2, default=str))

if response.status_code == 200:
    nim = result["nim"]
    print(f"[OK] NIM generated: {nim}")

# TEST 5: Approve idempotent
print("\n" + "="*70)
print("TEST 5: APPROVE AGAIN (Should return same NIM)")
print("="*70)

response2 = requests.put(f"{BASE_URL}/api/pmb/approve/{calon_id}", json=approve_data)
print(f"Status: {response2.status_code}")
result2 = response2.json()
nim2 = result2["nim"]

if nim == nim2:
    print(f"[OK] Idempotent check passed: {nim2}")
else:
    print(f"[ERROR] Different NIMs: {nim} vs {nim2}")

# TEST 6: Get statistics
print("\n" + "="*70)
print("TEST 6: GET STATISTICS")
print("="*70)

response = requests.get(f"{BASE_URL}/api/pmb/stats")
print(f"Status: {response.status_code}")
stats = response.json()
print(json.dumps(stats, indent=2, default=str))

# TEST 7: List applicants
print("\n" + "="*70)
print("TEST 7: LIST APPLICANTS")
print("="*70)

response = requests.get(f"{BASE_URL}/api/pmb/list?status=approved&skip=0&limit=10")
print(f"Status: {response.status_code}")
data = response.json()
print(f"Found {len(data)} approved applicants")
for item in data[:2]:
    print(f"  - {item['nama_lengkap']} ({item['nim']})")

print("\n" + "="*70)
print("ALL API TESTS COMPLETED")
print("="*70)
