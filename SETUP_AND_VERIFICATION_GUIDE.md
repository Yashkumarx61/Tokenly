# Tokenly POS — Windows VPS CI/CD & Automated Rollback Guide

This guide provides step-by-step instructions for configuring the dedicated **GitHub Actions Self-Hosted Runner** on Windows Server 2022, configuring repository secrets, and running a simulated deployment failure to test the bulletproof **automated rollback engine** in action.

---

## 1. Prerequisites & Windows VPS Requirements

Ensure the target Windows VPS meets the following requirements:
1. **OS:** Windows Server 2022 / Windows 10/11 Professional or Enterprise.
2. **Container Engine:**
   - Docker Desktop with WSL2 backend **OR**
   - Docker Engine / Mirantis Container Runtime natively on Windows Server.
   - Verify Docker CLI and Docker Compose are accessible via PowerShell:
     ```powershell
     docker --version
     docker compose version
     ```
3. **PowerShell Version:** PowerShell 5.1+ or PowerShell Core 7+.
4. **Git:** Installed and available in the system PATH.
5. **Port Accessibility:** Port `5000` (or `80`/`443` if using reverse proxy like IIS or NGINX) open in Windows Defender Firewall:
   ```powershell
   New-NetFirewallRule -DisplayName "Tokenly POS Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
   ```

---

## 2. GitHub Actions Self-Hosted Runner Installation

To allow GitHub Actions to trigger deployment scripts directly on the Windows VPS without exposing SSH ports:

### Step 2.1: Register New Runner in GitHub Repository
1. Navigate to your GitHub Repository: `Settings` -> `Actions` -> `Runners` -> `New self-hosted runner`.
2. Select **Windows** as the runner OS.
3. Open an **Administrator PowerShell** prompt on the Windows VPS and execute:

```powershell
# Create a dedicated directory for the runner
New-Item -Path "C:\actions-runner" -ItemType Directory -Force
Set-Location "C:\actions-runner"

# Download the latest runner package (replace version as provided by GitHub UI)
Invoke-WebRequest -Uri https://github.com/actions/runner/releases/download/v2.319.1/actions-runner-win-x64-2.319.1.zip -OutFile runner.zip

# Extract archive
Expand-Archive -Path runner.zip -DestinationPath . -Force
Remove-Item runner.zip
```

### Step 2.2: Configure Runner
Run the configuration script with your repository token:
```powershell
.\config.cmd --url https://github.com/YOUR_GITHUB_ORGANIZATION/YOUR_REPO --token YOUR_REGISTRATION_TOKEN --name "WindowsVPS-POS-Runner" --work "_work" --labels "self-hosted,Windows,X64,vps-prod" --unattended
```

### Step 2.3: Install as Windows Service
Install and start the runner service so it automatically executes in the background and starts up with Windows:
```powershell
.\env.cmd
.\run.cmd --install
Start-Service "actions.runner.YOUR_GITHUB_ORGANIZATION-YOUR_REPO.WindowsVPS-POS-Runner"
Get-Service "actions.runner*"
```

---

## 3. GitHub Repository Secrets & Environment Variables

Configure the following secrets under **Settings** -> **Secrets and variables** -> **Actions** -> **Repository Secrets**:

| Secret Name | Description / Value |
| :--- | :--- |
| `GHCR_TOKEN` | GitHub Personal Access Token (PAT) with `read:packages` and `write:packages` scope (or use `${{ secrets.GITHUB_TOKEN }}`). |
| `SLACK_WEBHOOK_URL` | *(Optional)* Slack Incoming Webhook URL for real-time deployment status notifications. |
| `DISCORD_WEBHOOK_URL`| *(Optional)* Discord Webhook URL for alerting on deployment failure/rollback. |

---

## 4. How the Automated Rollback Engine Works

```
                        +----------------------------+
                        |  GitHub Actions CD Stage   |
                        +----------------------------+
                                      |
                                      v
                        +----------------------------+
                        | Run deploy-with-rollback.ps1|
                        +----------------------------+
                                      |
       +------------------------------+------------------------------+
       |                                                             |
       v                                                             v
+-----------------------------+               +-----------------------------------+
| Record $PreviousStableTag   |               | Health Poll Loop (/healthz)       |
| in current_stable_version   |               | (20 attempts x 3 sec interval)    |
+-----------------------------+               +-----------------------------------+
       |                                                             |
       |                                       +---------------------+---------------------+
       |                                       |                                           |
       |                                       v (PASS)                                    v (FAIL / HTTP 5xx / Timeout)
       |                        +----------------------------+              +-------------------------------------+
       |                        | Mark $TargetTag as Stable  |              | Trigger Fallback Rollback Routine   |
       |                        | Housekeeping (docker prune)|              | Repoint to $PreviousStableTag       |
       |                        | Exit Code 0 (CD PASS)      |              | docker-compose up -d                |
       |                        +----------------------------+              | Export logs -> failure_logs.log     |
       |                                                                    | Exit Code 1 (CD FAIL)               |
       |                                                                    +-------------------------------------+
```

---

## 5. Simulating a Deployment Failure & Verifying Automatic Rollback

To test that the pipeline automatically catches broken releases and rolls back without manual intervention:

### Phase 1: Deploy Initial Stable Version
1. Push a healthy commit to `main`.
2. Confirm the workflow succeeds in GitHub Actions.
3. Check `current_stable_version.txt` on the server:
   ```powershell
   Get-Content C:\Tokenly\current_stable_version.txt
   ```
   *(It will contain the git SHA of the successful commit)*.

### Phase 2: Inject a Synthetic Fault
Modify `app.py` to break the health check:
```python
# Temporary code edit in app.py to simulate app crash/fault
@app.route('/healthz', methods=['GET'])
def health_check():
    return jsonify({"status": "unhealthy", "error": "Database connection string invalid"}), 500
```

### Phase 3: Push Faulty Code & Observe Pipeline Execution
1. Commit and push the broken code to `main`:
   ```bash
   git commit -am "test: breaking health check endpoint for rollback verification"
   git push origin main
   ```
2. Monitor the GitHub Actions run under the **Actions** tab.
3. **Observed Execution Log:**
   - Stage 1 (CI) passes.
   - Stage 2 (CD) pulls the faulty image and launches the container via `docker-compose.prod.yml`.
   - The PowerShell health check polling loop executes:
     ```
     [HEALTH CHECK] Attempt 1/20: HTTP Status 500... Waiting 3 seconds.
     ...
     [HEALTH CHECK] Attempt 20/20: HTTP Status 500... Waiting 3 seconds.
     [CRITICAL ERROR] Post-deployment health check failed after 60 seconds!
     [ROLLBACK ENGINE] Initiating automatic fallback rollback...
     [ROLLBACK ENGINE] Reverting docker-compose.prod.yml to previous stable tag: a1b2c3d4...
     [ROLLBACK ENGINE] Restarting container with previous stable image...
     [ROLLBACK ENGINE] Verifying rolled-back container health status...
     [SUCCESS] Rollback completed! Previous stable container is healthy.
     [DIAGNOSTICS] Saved failure container logs to failure_container_logs.log.
     ```
   - The script exits with `Code 1`.
   - GitHub Actions registers step failure, triggers artifact upload of `failure_container_logs.log`, and dispatches failure notifications.
   - **Result:** The Tokenly POS application on Windows VPS remains online and operational running the previous stable Docker image!
