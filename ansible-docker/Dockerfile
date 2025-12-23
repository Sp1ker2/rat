FROM alpine:latest

RUN apk add --no-cache \
    ansible \
    openssh-client \
    python3 \
    py3-pip \
    docker-cli \
    docker-compose \
    bash

# Установка Ansible коллекций
RUN ansible-galaxy collection install community.docker || true

WORKDIR /ansible

# Файлы будут монтироваться через volumes
CMD ["ansible-playbook", "ansible/deploy.yml", "-i", "ansible/inventory.yml", "-v"]
