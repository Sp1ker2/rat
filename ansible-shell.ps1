# Зайти в интерактивный контейнер Ansible
# Использование: .\ansible-shell.ps1

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Запуск интерактивного контейнера Ansible..." -ForegroundColor Cyan
Write-Host "После входа выполните: ansible-playbook ansible/deploy.yml -i ansible/inventory.yml -v" -ForegroundColor Yellow
Write-Host ""

docker run --rm -it `
    -v "${ScriptDir}:/workspace" `
    -w /workspace `
    -v "${env:USERPROFILE}\.ssh:/root/.ssh:ro" `
    -e ANSIBLE_HOST_KEY_CHECKING=False `
    -e ANSIBLE_REMOTE_TMP=/tmp/.ansible-root `
    -e ANSIBLE_CONFIG=/workspace/ansible.cfg `
    cytopia/ansible:latest `
    sh -c "apk add --no-cache sshpass openssh-client && /bin/sh"

