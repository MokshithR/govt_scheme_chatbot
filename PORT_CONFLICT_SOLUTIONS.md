# ⚠️ Port Conflict & Database Connection Issues

This document explains the **port 5432 conflict** between Windows PostgreSQL and Docker PostgreSQL, and provides solutions.

---

## The Problem

When both **Windows PostgreSQL** and **Docker PostgreSQL** run simultaneously on port 5432:

1. **Only one process can actually bind to port 5432**
2. The OS assigns the port to whichever service started first
3. Django connects to whichever PostgreSQL instance is listening on port 5432
4. **Connection behavior becomes unpredictable**

### Current Situation

**Diagnosis Results:**
```powershell
netstat -ano | findstr :5432
  TCP    0.0.0.0:5432           0.0.0.0:0              LISTENING       6636
  TCP    0.0.0.0:5432           0.0.0.0:0              LISTENING       21212
```

- **PID 6636**: Windows PostgreSQL (service `postgresql-x64-18`)
- **PID 21212**: Docker PostgreSQL (container `pgvector`)

**Verification:**
- Password `mok123` works → Connected to **Windows PostgreSQL**
- Extensions: `plpgsql`, `pg_trgm` → **NO pgvector** (Windows PostgreSQL)
- Password `postgres` should work → **Docker PostgreSQL** (has pgvector)

**Conclusion:** Django is currently connecting to **Windows PostgreSQL** which does NOT have the pgvector extension. Vector search will **FAIL**.

---

## Why This Happens

### Boot Order Matters

The first service to start "wins" port 5432:

**Scenario A: Windows PostgreSQL starts first**
```
1. Windows boots → postgresql-x64-18 service auto-starts → binds to port 5432
2. Docker Desktop starts → pgvector container starts → FAILS to bind port 5432
3. Docker container shows "running" but port mapping is broken
4. Django connects to Windows PostgreSQL
```

**Scenario B: Docker starts first**
```
1. Windows boots → Docker Desktop auto-starts → pgvector binds to port 5432
2. Windows PostgreSQL service tries to start → FAILS to bind port 5432
3. Service stops or enters error state
4. Django connects to Docker PostgreSQL ✓
```

### Verification Commands

```powershell
# Check which process owns port 5432
netstat -ano | findstr :5432

# If PID 6636 is shown:
Get-Process -Id 6636
# Output: postgres (Windows PostgreSQL)

# If PID 21212 is shown:
Get-Process -Id 21212
# Output: com.docker.backend.exe or similar
```

---

## Solutions

Choose ONE of the following solutions:

---

### ✅ Solution 1: Stop Windows PostgreSQL (Recommended)

**Best for:** Production deployment, permanent migration to Docker

**Steps:**

1. **Run PowerShell as Administrator**
   - Right-click PowerShell → "Run as Administrator"

2. **Execute the stop script**
   ```powershell
   cd C:\Users\MOKSHITH\govt_voice_chatbot_Bhavish
   .\stop_windows_postgres.ps1
   ```

3. **Or manually:**
   ```powershell
   # Stop the service
   Stop-Service -Name postgresql-x64-18 -Force
   
   # Disable auto-start
   Set-Service -Name postgresql-x64-18 -StartupType Disabled
   
   # Verify it's stopped
   Get-Service postgresql-x64-18
   ```

4. **Restart Docker container**
   ```powershell
   docker restart pgvector
   ```

5. **Verify port 5432 is now owned by Docker**
   ```powershell
   netstat -ano | findstr :5432
   # Should show only ONE PID (Docker process)
   ```

6. **Test connection**
   ```powershell
   python test_docker_postgres_connection.py
   ```

**✓ Pros:**
- Permanent solution
- No configuration changes needed
- Port 5432 free for Docker
- No confusion about which database is active

**✗ Cons:**
- Cannot use Windows PostgreSQL anymore (must use Docker)
- Requires Administrator privileges

---

### 🔄 Solution 2: Change Docker Port Mapping

**Best for:** Development environments, need to keep Windows PostgreSQL running

**Steps:**

1. **Stop and remove existing container**
   ```powershell
   docker stop pgvector
   docker rm pgvector
   ```

2. **Create new container on port 5433**
   ```powershell
   docker run -d \
     --name pgvector \
     -p 5433:5432 \
     -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_DB=govt_schemes \
     -v pgvector_data:/var/lib/postgresql/data \
     ankane/pgvector:pg16
   ```

3. **Update `.env` file**
   ```env
   POSTGRES_HOST=127.0.0.1
   POSTGRES_PORT=5433
   POSTGRES_DB=govt_schemes
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   ```

4. **Restore database backup (if needed)**
   ```powershell
   docker exec -i pgvector psql -U postgres -d govt_schemes < backup.sql
   ```

5. **Restart Django**
   ```powershell
   python manage.py runserver
   ```

**✓ Pros:**
- Both PostgreSQL instances can run simultaneously
- No need to stop Windows PostgreSQL
- Easy rollback

**✗ Cons:**
- Non-standard port (5433 instead of 5432)
- Must remember to specify port in all commands
- Potential for confusion about which database is active

---

### ⚙️ Solution 3: Use Different Hosts

**Best for:** Advanced users, need complete isolation

**Steps:**

1. **Stop Docker container**
   ```powershell
   docker stop pgvector
   docker rm pgvector
   ```

2. **Create container with specific network**
   ```powershell
   docker network create pg-network
   
   docker run -d \
     --name pgvector \
     --network pg-network \
     -p 127.0.0.1:5432:5432 \
     -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_DB=govt_schemes \
     ankane/pgvector:pg16
   ```

3. **Update `.env`**
   ```env
   POSTGRES_HOST=127.0.0.1
   POSTGRES_PORT=5432
   ```

4. **Ensure Windows PostgreSQL binds to different interface**
   - Edit `C:\Program Files\PostgreSQL\18\data\postgresql.conf`
   - Set: `listen_addresses = '192.168.1.100'` (use your LAN IP)
   - Restart Windows PostgreSQL

**✓ Pros:**
- Both services on port 5432 (different interfaces)
- Network isolation

**✗ Cons:**
- Complex configuration
- Requires editing PostgreSQL config files
- Hard to troubleshoot

---

### 🔌 Solution 4: Conditional Service Startup

**Best for:** Dual-boot development scenarios

**Create a startup script: `start_docker_postgres.bat`**

```batch
@echo off
echo Stopping Windows PostgreSQL...
net stop postgresql-x64-18

echo Starting Docker PostgreSQL...
docker start pgvector

echo Waiting for database to be ready...
timeout /t 5 /nobreak

echo Testing connection...
python test_docker_postgres_connection.py

pause
```

**Create a restore script: `restore_windows_postgres.bat`**

```batch
@echo off
echo Stopping Docker PostgreSQL...
docker stop pgvector

echo Starting Windows PostgreSQL...
net start postgresql-x64-18

echo Windows PostgreSQL restored
pause
```

**✓ Pros:**
- Quick switching between databases
- One-click operation
- No permanent changes

**✗ Cons:**
- Must remember to run script before Django
- Requires Administrator privileges
- Services don't auto-start

---

## Verification After Any Solution

Run these commands to verify your solution worked:

### 1. Check Port Ownership

```powershell
netstat -ano | findstr :5432
```

**Expected:** Only ONE process ID listed (either Docker or Windows, not both)

### 2. Run Connection Test

```powershell
python test_docker_postgres_connection.py
```

**Expected Output:**
```
Test 4: Checking pgvector extension...
  ✓ pgvector extension installed (version 0.8.1)
```

**✗ If you see:**
```
Test 4: Checking pgvector extension...
  ✗ pgvector extension NOT FOUND!
  This means you're connected to the WRONG database!
```
→ You're still connected to Windows PostgreSQL. Try Solution 1.

### 3. Check Extensions

```powershell
docker exec -it pgvector psql -U postgres -d govt_schemes -c "SELECT extname FROM pg_extension;"
```

**Expected:**
```
 extname  
----------
 plpgsql
 pg_trgm
 vector
```

### 4. Test Vector Search

```powershell
# Start Django
python manage.py runserver

# In another terminal:
curl -X POST http://localhost:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"farmer loan scheme"}'
```

**Expected:** JSON response with `results` array containing schemes

**✗ If you get:**
```
operator does not exist: vector <=>
```
→ Still connected to database without pgvector

---

## Common Mistakes

### ❌ Mistake 1: Changing `.env` but not stopping Windows PostgreSQL

```
# User updates .env with POSTGRES_PASSWORD=postgres
# But Windows PostgreSQL is still running on port 5432
# Django connects to Windows PostgreSQL anyway (ignores .env password)
```

**Fix:** Stop Windows PostgreSQL first, THEN update `.env`

---

### ❌ Mistake 2: Assuming Docker port mapping works when Windows service is running

```
# User checks: docker ps
# Container shows: 0.0.0.0:5432->5432/tcp
# User assumes container is accessible on port 5432
# But Windows PostgreSQL already owns the port!
```

**Fix:** Verify with `netstat`, not just `docker ps`

---

### ❌ Mistake 3: Changing password in `.env` but not restarting Django

```
# User edits .env file
# Django is still running with old environment variables
# Old password cached in memory
```

**Fix:** Always restart Django after changing `.env`:
```powershell
# Press Ctrl+C to stop Django
python manage.py runserver  # Start again
```

---

### ❌ Mistake 4: Testing connection with wrong credentials

```powershell
# User tests:
docker exec -it pgvector psql -U postgres -d govt_schemes

# This always works (connects INSIDE container)
# But Django connects from OUTSIDE (via port 5432)
# These are different connection paths!
```

**Fix:** Test with `python test_docker_postgres_connection.py` to simulate Django's connection

---

## Debugging Workflow

If vector search still doesn't work, follow this debugging checklist:

### Step 1: Identify which PostgreSQL Django connects to

```powershell
# Method A: Check extensions
python -c "import psycopg2; conn = psycopg2.connect(dbname='govt_schemes', user='postgres', password='postgres', host='127.0.0.1', port='5432'); cur = conn.cursor(); cur.execute('SELECT extname FROM pg_extension'); print([r[0] for r in cur.fetchall()])"
```

**If output includes `'vector'`:** Connected to Docker ✓  
**If output is `['plpgsql', 'pg_trgm']`:** Connected to Windows ✗

### Step 2: Check which service is on port 5432

```powershell
netstat -ano | findstr :5432 | findstr LISTENING
```

Get the PID, then:

```powershell
Get-Process -Id <PID> | Select-Object Name, Path
```

**If Name is `postgres`:** Windows PostgreSQL  
**If Name is `com.docker.backend.exe` or `Docker Desktop`:** Docker PostgreSQL

### Step 3: Verify service status

```powershell
# Windows PostgreSQL
Get-Service postgresql-x64-18

# Docker PostgreSQL
docker ps | findstr pgvector
```

**Both should NOT be running simultaneously!**

### Step 4: Force correct connection

```powershell
# Stop Windows PostgreSQL
Stop-Service postgresql-x64-18 -Force

# Restart Docker
docker restart pgvector

# Wait 5 seconds
Start-Sleep -Seconds 5

# Test
python test_docker_postgres_connection.py
```

---

## Emergency Rollback

If you need to urgently rollback to Windows PostgreSQL:

```powershell
# 1. Stop Docker
docker stop pgvector

# 2. Start Windows PostgreSQL
Start-Service postgresql-x64-18

# 3. Update .env
# Change POSTGRES_PASSWORD back to 'mok123'

# 4. Restart Django
python manage.py runserver
```

**Note:** Vector search will NOT work in Windows PostgreSQL (no pgvector extension).

---

## Best Practice: Docker-Only Setup

For production or permanent development setup:

1. **Disable Windows PostgreSQL**
   ```powershell
   Set-Service postgresql-x64-18 -StartupType Disabled
   ```

2. **Set Docker Desktop to auto-start**
   - Settings → General → "Start Docker Desktop when you log in" ✓

3. **Add Docker container to auto-start**
   ```powershell
   docker update --restart unless-stopped pgvector
   ```

4. **Create health check script: `check_db.ps1`**
   ```powershell
   $status = docker ps --filter "name=pgvector" --filter "status=running" -q
   if ($status) {
       Write-Host "✓ Database is running" -ForegroundColor Green
       python test_docker_postgres_connection.py
   } else {
       Write-Host "✗ Database is NOT running" -ForegroundColor Red
       Write-Host "Starting database..." -ForegroundColor Yellow
       docker start pgvector
       Start-Sleep -Seconds 5
       python test_docker_postgres_connection.py
   }
   ```

5. **Add to Windows startup**
   - Create shortcut to `check_db.ps1`
   - Place in: `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp`

---

## Summary: Recommended Solution

**For your specific situation:**

1. ✅ **Use Solution 1** (Stop Windows PostgreSQL)
   - Run `.\stop_windows_postgres.ps1` as Administrator
   - Permanent fix, no configuration changes needed

2. ⚠️ **Why not Solution 2?**
   - Changing ports adds complexity
   - Non-standard port (5433) breaks conventions
   - Must update all tooling

3. ⚠️ **Why not Solution 3/4?**
   - Overly complex for single-developer setup
   - Hard to maintain
   - Easy to forget which database is active

**Final verification:**
```powershell
# Should show only Docker process
netstat -ano | findstr :5432

# Should show ✓ pgvector extension
python test_docker_postgres_connection.py

# Should return schemes
python manage.py runserver
# Then test: POST to http://localhost:8000/api/search/
```

---

**READY TO PROCEED?** Run `.\stop_windows_postgres.ps1` as Administrator!
