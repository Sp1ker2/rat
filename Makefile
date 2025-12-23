.PHONY: deploy shell ping check logs restart

# Основной деплой
deploy:
	@echo "Deploying via Ansible..."
	@docker run --rm \
		-v "$$(pwd):/workspace" \
		-w /workspace \
		-v ~/.ssh:/root/.ssh:ro \
		-e ANSIBLE_HOST_KEY_CHECKING=False \
		-e ANSIBLE_REMOTE_TMP=/tmp/.ansible-root \
		-e ANSIBLE_CONFIG=/workspace/ansible.cfg \
		cytopia/ansible:latest \
		sh -c "apk add --no-cache sshpass openssh-client > /dev/null 2>&1 && ansible-playbook ansible/deploy.yml -i ansible/inventory.yml -v"

# Интерактивный shell
shell:
	@echo "Starting Ansible interactive shell..."
	@docker run --rm -it \
		-v "$$(pwd):/workspace" \
		-w /workspace \
		-v ~/.ssh:/root/.ssh:ro \
		-e ANSIBLE_HOST_KEY_CHECKING=False \
		-e ANSIBLE_REMOTE_TMP=/tmp/.ansible-root \
		-e ANSIBLE_CONFIG=/workspace/ansible.cfg \
		cytopia/ansible:latest \
		sh -c "apk add --no-cache sshpass openssh-client && /bin/sh"

# Проверка подключения
ping:
	@echo "Pinging server..."
	@docker run --rm \
		-v "$$(pwd):/workspace" \
		-w /workspace \
		-e ANSIBLE_HOST_KEY_CHECKING=False \
		-e ANSIBLE_REMOTE_TMP=/tmp/.ansible-root \
		-e ANSIBLE_CONFIG=/workspace/ansible.cfg \
		cytopia/ansible:latest \
		sh -c "apk add --no-cache sshpass openssh-client > /dev/null 2>&1 && ansible all -i ansible/inventory.yml -m ping"

# Проверка синтаксиса
check:
	@echo "Checking playbook syntax..."
	@docker run --rm \
		-v "$$(pwd):/workspace" \
		-w /workspace \
		cytopia/ansible:latest \
		ansible-playbook ansible/deploy.yml --syntax-check

# Посмотреть логи на сервере
logs:
	@ssh root@185.115.33.46 "docker logs webrtc-python-server -f"

# Перезапустить контейнер на сервере
restart:
	@ssh root@185.115.33.46 "cd /root/webrtc-server && docker-compose restart"

# Dry-run деплоя
dry-run:
	@echo "Dry-run deployment..."
	@docker run --rm \
		-v "$$(pwd):/workspace" \
		-w /workspace \
		-v ~/.ssh:/root/.ssh:ro \
		-e ANSIBLE_HOST_KEY_CHECKING=False \
		-e ANSIBLE_REMOTE_TMP=/tmp/.ansible-root \
		-e ANSIBLE_CONFIG=/workspace/ansible.cfg \
		cytopia/ansible:latest \
		sh -c "apk add --no-cache sshpass openssh-client > /dev/null 2>&1 && ansible-playbook ansible/deploy.yml -i ansible/inventory.yml --check"

# Показать информацию о сервере
info:
	@docker run --rm \
		-v "$$(pwd):/workspace" \
		-w /workspace \
		-e ANSIBLE_HOST_KEY_CHECKING=False \
		-e ANSIBLE_REMOTE_TMP=/tmp/.ansible-root \
		-e ANSIBLE_CONFIG=/workspace/ansible.cfg \
		cytopia/ansible:latest \
		sh -c "apk add --no-cache sshpass openssh-client > /dev/null 2>&1 && ansible all -i ansible/inventory.yml -m setup | grep ansible_distribution"

help:
	@echo "Available commands:"
	@echo "  make deploy    - Deploy application via Ansible"
	@echo "  make shell     - Start interactive Ansible shell"
	@echo "  make ping      - Ping server"
	@echo "  make check     - Check playbook syntax"
	@echo "  make logs      - Show container logs"
	@echo "  make restart   - Restart container on server"
	@echo "  make dry-run   - Dry-run deployment"
	@echo "  make info      - Show server information"

