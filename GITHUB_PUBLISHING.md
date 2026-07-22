# Publicação no GitHub

## Nome recomendado

`feature-flag-gateway`

## Descrição curta

Multi-tenant feature flag gateway built with FastAPI, PostgreSQL, Redis,
JWT, idempotency and real-time SSE synchronization.

## Descrição em português

Gateway multi-tenant de feature flags com FastAPI, PostgreSQL, cache Redis,
JWT, idempotência e sincronização em tempo real via SSE.

## Tópicos recomendados

```text
fastapi
python
feature-flags
redis
postgresql
sqlalchemy
asyncio
sse
jwt
multi-tenant
repository-pattern
unit-of-work
docker
pytest
alembic
```

## Criar o repositório pelo terminal

Na pasta do projeto:

```bash
git init
git branch -M main
git add .
git commit -m "feat: publish feature flag gateway"
```

Crie um repositório vazio no GitHub com o nome `feature-flag-gateway`.

Depois:

```bash
git remote add origin https://github.com/SEU-USUARIO/feature-flag-gateway.git
git push -u origin main
```

## Usando GitHub CLI

```bash
gh auth login
gh repo create feature-flag-gateway   --public   --source=.   --remote=origin   --push   --description "Multi-tenant feature flag gateway with Redis cache and real-time SSE"
```

## Checklist antes do push

```bash
git status
git ls-files | grep -E '(^|/)\.env$' && echo "ERRO: .env rastreado"
docker compose exec api pytest -v
```

Confirme:

- `.env` não está versionado;
- os 23 testes passam;
- cobertura permanece acima de 85%;
- nenhum token ou senha real está nos arquivos;
- README está atualizado;
- a aplicação inicia pelo Docker Compose.
