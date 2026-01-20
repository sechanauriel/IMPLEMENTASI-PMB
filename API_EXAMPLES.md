"""
API Usage Examples dan Demo

Gunakan file ini untuk testing API dengan curl atau Postman
"""

# =============================================
# 1. MASTER DATA SETUP
# =============================================

# Create Program Studi
curl -X POST http://localhost:8000/api/master/program-studi \
  -H "Content-Type: application/json" \
  -d '{
    "kode": "001",
    "nama": "Teknik Informatika",
    "fakultas": "Teknik"
  }'

# Create Jalur Masuk
curl -X POST http://localhost:8000/api/master/jalur-masuk \
  -H "Content-Type: application/json" \
  -d '{
    "kode": "SNBP",
    "nama": "Seleksi Nasional Berbasis Prestasi",
    "deskripsi": "Jalur SNBP untuk calon mahasiswa berprestasi"
  }'

# =============================================
# 2. REGISTER CALON MAHASISWA
# =============================================

# Register dengan email unik
curl -X POST http://localhost:8000/api/pmb/register \
  -H "Content-Type: application/json" \
  -d '{
    "nama_lengkap": "Ahmad Hidayat",
    "email": "ahmad.hidayat@email.com",
    "phone": "082123456789",
    "tanggal_lahir": "2005-01-15",
    "alamat": "Jl. Merdeka No. 10, Jakarta",
    "program_studi_id": 1,
    "jalur_masuk_id": 1
  }'

# Try register dengan email duplicate (should fail with 409)
curl -X POST http://localhost:8000/api/pmb/register \
  -H "Content-Type: application/json" \
  -d '{
    "nama_lengkap": "Budi Santoso",
    "email": "ahmad.hidayat@email.com",
    "phone": "081234567890",
    "tanggal_lahir": "2005-02-20",
    "alamat": "Jl. Sudirman, Jakarta",
    "program_studi_id": 1,
    "jalur_masuk_id": 1
  }'

# Register dengan phone format +62
curl -X POST http://localhost:8000/api/pmb/register \
  -H "Content-Type: application/json" \
  -d '{
    "nama_lengkap": "Citra Dewi",
    "email": "citra.dewi@email.com",
    "phone": "+6281234567890",
    "tanggal_lahir": "2005-03-10",
    "alamat": "Jl. Ahmad Yani, Bandung",
    "program_studi_id": 1,
    "jalur_masuk_id": 2
  }'

# =============================================
# 3. CHECK STATUS
# =============================================

# Check status calon dengan ID 1
curl -X GET http://localhost:8000/api/pmb/status/1

# =============================================
# 4. APPROVE DAN GENERATE NIM
# =============================================

# Approve calon dengan ID 1 (akan generate NIM otomatis)
curl -X PUT http://localhost:8000/api/pmb/approve/1 \
  -H "Content-Type: application/json" \
  -d '{}'

# Approve lagi untuk test idempotency (should return same NIM)
curl -X PUT http://localhost:8000/api/pmb/approve/1 \
  -H "Content-Type: application/json" \
  -d '{}'

# =============================================
# 5. LIST & FILTER
# =============================================

# List all calon (default limit 100)
curl -X GET "http://localhost:8000/api/pmb/list"

# List pending calon
curl -X GET "http://localhost:8000/api/pmb/list?status=pending"

# List approved calon
curl -X GET "http://localhost:8000/api/pmb/list?status=approved"

# List dengan pagination
curl -X GET "http://localhost:8000/api/pmb/list?skip=0&limit=10"

# Filter by program studi
curl -X GET "http://localhost:8000/api/pmb/list?program_studi_id=1"

# =============================================
# 6. STATISTICS
# =============================================

# Get dashboard statistics
curl -X GET http://localhost:8000/api/pmb/stats

# =============================================
# 7. REJECT
# =============================================

# Reject calon dengan ID 2
curl -X POST http://localhost:8000/api/pmb/reject/2

# =============================================
# 8. SWAGGER DOCUMENTATION
# =============================================

# Access interactive API documentation
http://localhost:8000/docs

# Access alternative documentation (ReDoc)
http://localhost:8000/redoc

# =============================================
# PYTHON REQUESTS EXAMPLES
# =============================================

import requests

BASE_URL = "http://localhost:8000"

# 1. Register
response = requests.post(
    f"{BASE_URL}/api/pmb/register",
    json={
        "nama_lengkap": "Eka Putra",
        "email": "eka.putra@email.com",
        "phone": "082345678901",
        "tanggal_lahir": "2005-04-12",
        "alamat": "Jl. Diponegoro, Surabaya",
        "program_studi_id": 1,
        "jalur_masuk_id": 1
    }
)
calon_id = response.json()["id"]
print(f"Registered with ID: {calon_id}")

# 2. Check status
response = requests.get(f"{BASE_URL}/api/pmb/status/{calon_id}")
print(f"Status: {response.json()['status']}")
print(f"NIM: {response.json()['nim']}")

# 3. Approve
response = requests.put(
    f"{BASE_URL}/api/pmb/approve/{calon_id}",
    json={}
)
nim = response.json()["nim"]
print(f"Approved! NIM: {nim}")

# 4. Get stats
response = requests.get(f"{BASE_URL}/api/pmb/stats")
stats = response.json()
print(f"Total: {stats['total_pendaftar']}")
print(f"Pending: {stats['pending']}")
print(f"Approved: {stats['approved']}")

# =============================================
# TESTING NOTES
# =============================================

"""
1. Phone Format Testing:
   - Valid: 082123456789 (10 digits after 0)
   - Valid: 081234567890 (11 digits)
   - Valid: +6281234567890
   - Invalid: 12345 (too short)
   - Invalid: 6281234567890 (missing + or 0)

2. Email Testing:
   - Valid: user@example.com
   - Valid: user.name@domain.co.id
   - Invalid: user@.com
   - Invalid: @example.com

3. NIM Format:
   - Expected: YYYY[KODE_PRODI][SEQUENTIAL]
   - Example: 2025001-0001
   - Pattern: 4 digits (year) + 3 digits (prodi) + - + 4 digits (sequence)

4. Status Flow:
   - Register → status: "pending", nim: null
   - Approve → status: "approved", nim: "2025001-0001"
   - Reject → status: "rejected", nim: null

5. Idempotency Test:
   - Approve same calon twice
   - Should return same NIM (no duplicate)
"""
