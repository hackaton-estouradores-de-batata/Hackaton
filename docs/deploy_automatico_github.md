# Deploy automatico com GitHub Actions (Linux)

Este guia configura deploy automatico em servidor Linux sempre que houver push na branch `main`.

## 1. Arquivos adicionados

- `compose.prod.yaml`: stack de producao (sem hot reload e sem bind de codigo)
- `.github/workflows/deploy-prod.yml`: workflow de deploy via SSH

## 2. Preparar servidor Linux (1a vez)

Exemplo em Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git

# Docker Engine + Compose plugin
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker

docker --version
docker compose version
```

Crie pasta do projeto:

```bash
sudo mkdir -p /opt/hackaton
sudo chown -R $USER:$USER /opt/hackaton
```

## 3. Chave de deploy no servidor (acesso ao repo)

No servidor, gere um par SSH para leitura do repositorio:

```bash
ssh-keygen -t ed25519 -C "deploy@hackaton" -f ~/.ssh/hackaton_deploy_key -N ""
cat ~/.ssh/hackaton_deploy_key.pub
```

No GitHub do repositorio:

1. Settings
2. Deploy keys
3. Add deploy key
4. Cole a chave publica
5. Permissao: Read only

Configure o SSH local do servidor:

```bash
cat >> ~/.ssh/config << 'EOF'
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/hackaton_deploy_key
  IdentitiesOnly yes
EOF

chmod 600 ~/.ssh/config ~/.ssh/hackaton_deploy_key
chmod 644 ~/.ssh/hackaton_deploy_key.pub
ssh -T git@github.com
```

## 4. Criar `.env` no servidor

No servidor, dentro de `/opt/hackaton` (apos primeiro deploy ou clone manual), crie e ajuste:

```env
APP_ENV=production
API_PORT=8000
WEB_PORT=3000
API_BIND=127.0.0.1
WEB_BIND=127.0.0.1
DATABASE_URL=sqlite:////workspace/data/app.db
CASE_STORAGE_DIR=/workspace/data/processos_exemplo
POLICY_PATH=/workspace/policy/acordos_v1.yaml
OPENAI_API_KEY=coloque_sua_chave
NEXT_PUBLIC_USE_MOCK=false
```

## 5. Configurar GitHub Secrets

No repo: Settings > Secrets and variables > Actions > New repository secret.

Crie os secrets:

- `SSH_HOST`: IP ou dominio do servidor
- `SSH_USER`: usuario Linux que vai executar o deploy
- `SSH_PRIVATE_KEY`: chave privada usada pelo GitHub Actions para entrar no servidor
- `SSH_PORT`: normalmente `22`
- `SSH_FINGERPRINT`: fingerprint do host SSH (seguranca)
- `DEPLOY_DIR`: caminho de deploy, ex.: `/opt/hackaton`

### Como obter fingerprint do host

No seu computador:

```bash
ssh-keyscan -t ed25519 SEU_SERVIDOR | ssh-keygen -lf -
```

Use no secret apenas o hash exibido (ex.: `SHA256:...`).

## 6. Como o deploy funciona

Quando houver push em `main`:

1. O workflow conecta no servidor por SSH.
2. Faz clone/pull do repositorio em `DEPLOY_DIR`.
3. Valida existencia de `.env`.
4. Roda `docker compose -f compose.prod.yaml up -d --build --remove-orphans`.
5. Remove imagens dangling com `docker image prune -f`.

## 7. Execucao manual do workflow

No GitHub: Actions > Deploy Production > Run workflow.

## 8. Validacao apos deploy

No servidor:

```bash
cd /opt/hackaton
docker compose -f compose.prod.yaml ps
docker compose -f compose.prod.yaml logs -f api
curl http://127.0.0.1:8000/healthz
```

## 9. Recomendacao para internet publica

Para ambiente publico, rode um proxy reverso (Nginx/Caddy/Traefik) com HTTPS e mantenha API/WEB bindados em `127.0.0.1`.
