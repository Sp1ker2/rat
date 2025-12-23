# Деплой через Ansible в Docker
# Использование: .\deploy.ps1

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Deploying via Ansible..." -ForegroundColor Cyan

docker run --rm `
    -v "${ScriptDir}:/workspace" `
    -w /workspace `
    -v "${env:USERPROFILE}\.ssh:/root/.ssh:ro" `
    -e ANSIBLE_HOST_KEY_CHECKING=False `
    -e ANSIBLE_REMOTE_TMP=/tmp/.ansible-root `
    -e ANSIBLE_CONFIG=/workspace/ansible.cfg `
    cytopia/ansible:latest `
    sh -c "apk add --no-cache sshpass openssh-client > /dev/null 2>&1 && ansible-playbook ansible/deploy.yml -i ansible/inventory.yml -v"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Deploy completed!" -ForegroundColor Green
} else {
    Write-Host "Deploy failed!" -ForegroundColor Red
    exit 1
}
