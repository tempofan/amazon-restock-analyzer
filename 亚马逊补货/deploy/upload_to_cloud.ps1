# PowerShell Upload Script for Cloud Proxy Server
# Upload cloud proxy files to cloud server

param(
    [Parameter(Mandatory=$false)]
    [string]$User = "ubuntu",
    
    [Parameter(Mandatory=$false)]
    [string]$Server = "175.178.183.96"
)

Write-Host "Upload Cloud Proxy Server Files" -ForegroundColor Green
Write-Host "=" * 50

# Check if required files exist
$files = @(
    "deploy\cloud_proxy_server.py",
    "deploy\quick_deploy_cloud_proxy.sh"
)

foreach ($file in $files) {
    if (-not (Test-Path $file)) {
        Write-Host "File not found: $file" -ForegroundColor Red
        exit 1
    }
}

Write-Host "All required files exist" -ForegroundColor Green

# Display upload configuration
Write-Host ""
Write-Host "Upload Configuration:" -ForegroundColor Yellow
Write-Host "- User: $User"
Write-Host "- Server: $Server"  
Write-Host "- Target Directory: ~/"

# Upload commands
$scpCommands = @(
    "scp deploy\cloud_proxy_server.py ${User}@${Server}:~/",
    "scp deploy\quick_deploy_cloud_proxy.sh ${User}@${Server}:~/"
)

Write-Host ""
Write-Host "Starting file upload..." -ForegroundColor Yellow

foreach ($cmd in $scpCommands) {
    Write-Host "Executing: $cmd" -ForegroundColor Cyan
    
    # Check if scp command exists
    if (Get-Command scp -ErrorAction SilentlyContinue) {
        Invoke-Expression $cmd
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Upload successful" -ForegroundColor Green
        } else {
            Write-Host "Upload failed" -ForegroundColor Red
        }
    } else {
        Write-Host "SCP command not found. Please execute manually:" -ForegroundColor Yellow
        Write-Host "   $cmd" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. SSH to cloud server: ssh ${User}@${Server}"
Write-Host "2. Execute deploy script:"
Write-Host "   chmod +x quick_deploy_cloud_proxy.sh"
Write-Host "   ./quick_deploy_cloud_proxy.sh"
Write-Host "3. Verify service status: curl http://localhost:8080/health"

Write-Host ""
Write-Host "Local Verification:" -ForegroundColor Yellow
Write-Host "python test\test_cloud_proxy_feishu.py"

Write-Host ""
Write-Host "Alternative Upload Methods:" -ForegroundColor Cyan
Write-Host "- Use WinSCP or FileZilla"
Write-Host "- Use VSCode Remote-SSH extension"
Write-Host "- Use SCP command in WSL" 