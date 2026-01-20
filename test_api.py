#!/usr/bin/env python3
"""
API Testing Script for PMB System
Tests all 6 main endpoints with various scenarios
"""

import requests
import json
from datetime import date

BASE_URL = "http://localhost:8000"

def print_response(title, response):
    """Pretty print API response"""
    print(f"\n{'='*70}")
    print(f"[TEST] {title}")
    print(f"{'='*70}")
    print(f"Status: {response.status_code}")
    try:
        print(f"Response:")
        print(json.dumps(response.json(), indent=2, default=str))
    except:
        print(f"Response: {response.text}")

def test_api():
    """Test all API endpoints"""
    
    # ===== TEST 1: Register Calon =====
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
    print_response("Register - Success", response)
    
    if response.status_code == 201:
        calon_id = response.json()["id"]
        print(f"[OK] Calon registered with ID: {calon_id}")
    else:
        print("❌ Registration failed!")
        return
    
    # ===== TEST 2: Duplicate Email =====
    print("\n" + "="*70)
    print("TEST 2: TRY DUPLICATE EMAIL (Should fail with 409)")
    print("="*70)
    
    response = requests.post(f"{BASE_URL}/api/pmb/register", json=data)
    print_response("Register - Duplicate Email", response)
    
    if response.status_code == 409:
        print("✅ Duplicate email properly rejected")
    
    # ===== TEST 3: Invalid Phone Format =====
    print("\n" + "="*70)
    print("TEST 3: INVALID PHONE FORMAT (Should fail with 400)")
    print("="*70)
    
    invalid_data = data.copy()
    invalid_data["email"] = "invalid.phone@example.com"
    invalid_data["phone"] = "123456789"  # Invalid format
    
    response = requests.post(f"{BASE_URL}/api/pmb/register", json=invalid_data)
    print_response("Register - Invalid Phone", response)
    
    if response.status_code == 400:
        print("✅ Invalid phone format properly rejected")
    
    # ===== TEST 4: Register Another Calon =====
    print("\n" + "="*70)
    print("TEST 4: REGISTER SECOND APPLICANT (for testing approval)")
    print("="*70)
    
    data2 = {
        "nama_lengkap": "Siti Nurhaliza",
        "email": "siti.nurhaliza@example.com",
        "phone": "082123456789",
        "tanggal_lahir": "2004-05-20",
        "alamat": "Jalan Ahmad Yani No. 456",
        "program_studi_id": 2,
        "jalur_masuk_id": 2
    }
    
    response = requests.post(f"{BASE_URL}/api/pmb/register", json=data2)
    print_response("Register - Second Applicant", response)
    
    if response.status_code == 201:
        calon_id_2 = response.json()["id"]
        print(f"✅ Second calon registered with ID: {calon_id_2}")
    
    # ===== TEST 5: Get Status Before Approval =====
    print("\n" + "="*70)
    print("TEST 5: GET STATUS (Should be PENDING)")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/api/pmb/status/{calon_id}")
    print_response("Get Status - Pending", response)
    
    if response.status_code == 200 and response.json()["status"] == "pending":
        print("✅ Status correctly shows PENDING")
    
    # ===== TEST 6: Approve and Generate NIM =====
    print("\n" + "="*70)
    print("TEST 6: APPROVE & GENERATE NIM")
    print("="*70)
    
    approve_data = {"keterangan": "Lulus seleksi masuk"}
    response = requests.put(f"{BASE_URL}/api/pmb/approve/{calon_id}", json=approve_data)
    print_response("Approve - Generate NIM", response)
    
    if response.status_code == 200:
        nim = response.json()["nim"]
        print(f"✅ NIM generated: {nim}")
        # Validate NIM format: YYYY[KODE]-XXXX
        if nim.startswith("2025") and "-" in nim:
            print(f"✅ NIM format valid: {nim}")
    
    # ===== TEST 7: Approve Idempotent =====
    print("\n" + "="*70)
    print("TEST 7: APPROVE AGAIN (Should return same NIM - Idempotent)")
    print("="*70)
    
    response2 = requests.put(f"{BASE_URL}/api/pmb/approve/{calon_id}", json=approve_data)
    print_response("Approve - Idempotent", response2)
    
    if response2.status_code == 200:
        nim2 = response2.json()["nim"]
        if nim == nim2:
            print(f"✅ Idempotent check passed: {nim2}")
        else:
            print("❌ Different NIM generated!")
    
    # ===== TEST 8: Get Status After Approval =====
    print("\n" + "="*70)
    print("TEST 8: GET STATUS (Should be APPROVED with NIM)")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/api/pmb/status/{calon_id}")
    print_response("Get Status - Approved", response)
    
    if response.status_code == 200:
        status_info = response.json()
        if status_info["status"] == "approved" and status_info["nim"]:
            print(f"✅ Status shows APPROVED with NIM: {status_info['nim']}")
    
    # ===== TEST 9: Approve Second Calon =====
    print("\n" + "="*70)
    print("TEST 9: APPROVE SECOND CALON (Different NIM sequence)")
    print("="*70)
    
    response = requests.put(f"{BASE_URL}/api/pmb/approve/{calon_id_2}", json=approve_data)
    print_response("Approve - Second Calon", response)
    
    if response.status_code == 200:
        nim2 = response.json()["nim"]
        print(f"✅ Second NIM generated: {nim2}")
    
    # ===== TEST 10: List Applicants =====
    print("\n" + "="*70)
    print("TEST 10: LIST APPLICANTS (with filters)")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/api/pmb/list?status=approved&skip=0&limit=10")
    print_response("List Applicants - Approved Only", response)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {len(data)} approved applicants")
    
    # ===== TEST 11: Get Statistics =====
    print("\n" + "="*70)
    print("TEST 11: GET STATISTICS")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/api/pmb/stats")
    print_response("Statistics", response)
    
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Approved: {stats['total_approved']}, Pending: {stats['total_pending']}")
    
    # ===== TEST 12: Reject Applicant =====
    print("\n" + "="*70)
    print("TEST 12: REJECT APPLICANT")
    print("="*70)
    
    # Register a new one to reject
    data3 = {
        "nama_lengkap": "Ahmad Wijaya",
        "email": "ahmad.wijaya@example.com",
        "phone": "085678901234",
        "tanggal_lahir": "2006-03-10",
        "alamat": "Jalan Sudirman No. 789",
        "program_studi_id": 3,
        "jalur_masuk_id": 3
    }
    
    response = requests.post(f"{BASE_URL}/api/pmb/register", json=data3)
    if response.status_code == 201:
        calon_id_3 = response.json()["id"]
        
        # Reject it
        response = requests.post(f"{BASE_URL}/api/pmb/reject/{calon_id_3}", json={})
        print_response("Reject - Success", response)
        
        if response.status_code == 200 and response.json()["status"] == "rejected":
            print("✅ Applicant successfully rejected")
    
    # ===== TEST 13: Test Not Found =====
    print("\n" + "="*70)
    print("TEST 13: TEST 404 NOT FOUND")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/api/pmb/status/99999")
    print_response("Get Status - Not Found", response)
    
    if response.status_code == 404:
        print("✅ Properly returns 404 for non-existent calon")
    
    # ===== SUMMARY =====
    print("\n" + "="*70)
    print("✅ ALL API TESTS COMPLETED")
    print("="*70)

if __name__ == "__main__":
    test_api()
