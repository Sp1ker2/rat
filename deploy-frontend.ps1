# Deploy frontend only
Write-Host "Deploying frontend to server..." -ForegroundColor Cyan

# Check if frontend is built
if (-not (Test-Path "frontend\build\index.html")) {
    Write-Host "Frontend not built! Building now..." -ForegroundColor Yellow
    cd frontend
    npm install
    npm run build
    cd ..
}

# Run Ansible
docker run --rm -it `
  -v "$(pwd):/workspace" `
  -v "$($env:USERPROFILE)\.ssh:/root/.ssh:ro" `
  -w /workspace `
  cytopia/ansible:latest `
  sh -c "apk add --no-cache sshpass openssh-client > /dev/null 2>&1 && ansible-playbook ansible/deploy-frontend.yml -i ansible/inventory.yml -v"

Write-Host "Frontend deployed!" -ForegroundColor Green

