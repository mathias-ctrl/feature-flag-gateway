# Feature Flag Gateway

Gateway de feature flags multi-tenant construído com FastAPI para ativar ou
desativar funcionalidades em tempo real, sem exigir um novo deploy da aplicação.

O projeto combina PostgreSQL, Redis, Server-Sent Events e uma arquitetura em
camadas para oferecer avaliações rápidas, isolamento por tenant, idempotência,
sincronização em tempo real e uma suíte de testes com cobertura superior a 85%.

## Por que este projeto existe

Em aplicações tradicionais, a ativação de uma funcionalidade costuma depender
de configuração estática ou de um novo deploy. Isso aumenta o risco operacional,
dificulta rollbacks rápidos e impede liberações graduais.

Este projeto foi criado para centralizar decisões de feature flags em uma API
capaz de:

- ativar ou desativar recursos instantaneamente;
- separar configurações por tenant e ambiente;
- responder avaliações pelo Redis sem consultar o banco a cada requisição;
- notificar clientes conectados em tempo real por SSE;
- evitar processamento duplicado com chaves de idempotência;
- proteger operações com JWT e validação de tenant.

## Resultado alcançado

A implementação final entrega:

- API FastAPI assíncrona;
- arquitetura multi-tenant;
- PostgreSQL com SQLAlchemy 2.0 assíncrono;
- migrações Alembic;
- cache-aside com Redis;
- Redis Pub/Sub para distribuição de eventos;
- Server-Sent Events para atualização em tempo real;
- autenticação JWT;
- hash de senhas com bcrypt;
- idempotência distribuída;
- Repository Pattern;
- Unit of Work;
- Dependency Injection;
- Factory de aplicação;
- paginação por cursor;
- tratamento centralizado de erros;
- logs estruturados;
- headers de segurança;
- Docker e Docker Compose;
- 23 testes automatizados;
- cobertura total aproximada de 88%.

## Arquitetura

```text
Cliente
  |
  v
FastAPI
  |
  +--> Autenticação JWT e tenant
  |
  +--> Camada de serviços
          |
          +--> Redis cache-aside
          |
          +--> Unit of Work
          |      |
          |      +--> Repository
          |             |
          |             +--> PostgreSQL
          |
          +--> Redis Pub/Sub
                    |
                    +--> SSE
```

### Fluxo de avaliação

1. O cliente solicita a avaliação de uma flag.
2. A API valida o JWT e o tenant.
3. O serviço consulta o Redis.
4. Em cache hit, a resposta é retornada imediatamente.
5. Em cache miss, a flag é carregada do PostgreSQL.
6. O resultado é gravado no Redis com TTL.
7. A resposta informa se veio do cache ou do banco.

### Fluxo de atualização

1. A API valida JWT, tenant e `Idempotency-Key`.
2. A alteração é persistida em uma transação.
3. A entidade é atualizada e recarregada antes da serialização.
4. O cache Redis é sincronizado.
5. Um evento é publicado no Redis Pub/Sub.
6. Clientes SSE recebem a alteração em tempo real.

## Tecnologias

- Python 3.12
- FastAPI
- Pydantic
- SQLAlchemy 2.0
- PostgreSQL
- Redis
- Alembic
- PyJWT
- bcrypt
- structlog
- sse-starlette
- pytest
- pytest-asyncio
- pytest-cov
- Ruff
- mypy
- Docker
- Docker Compose

## Estrutura do projeto

```text
feature-flag-gateway/
├── alembic/
│   ├── versions/
│   └── env.py
├── app/
│   ├── api/
│   │   ├── dependencies.py
│   │   └── routes/
│   ├── core/
│   │   ├── config.py
│   │   ├── errors.py
│   │   ├── logging.py
│   │   └── security.py
│   ├── domain/
│   │   ├── models.py
│   │   ├── repositories.py
│   │   └── schemas.py
│   ├── infrastructure/
│   │   ├── repositories/
│   │   ├── cache.py
│   │   ├── database.py
│   │   └── unit_of_work.py
│   ├── services/
│   │   ├── flags.py
│   │   └── idempotency.py
│   └── main.py
├── tests/
│   ├── integration/
│   └── unit/
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── pyproject.toml
└── README.md
```

## Como executar

### Pré-requisitos

- Docker
- Docker Compose

### Inicialização

```bash
cp .env.example .env
```

Troque o valor de `JWT_SECRET` por uma chave segura com pelo menos 32 caracteres.

Depois:

```bash
docker compose up -d --build
```

Confira os serviços:

```bash
docker compose ps
```

A API estará disponível em:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## Gerando um token de desenvolvimento

No diretório do projeto:

```bash
TOKEN=$(docker compose exec -T api python -c "from app.core.config import get_settings; from app.core.security import create_access_token; print(create_access_token('user-1', 'tenant-a', get_settings()))")
```

Confirme que a variável foi preenchida:

```bash
test -n "$TOKEN" && echo "TOKEN carregado" || echo "TOKEN vazio"
```

A variável precisa ser gerada novamente ao abrir outro terminal ou trocar de
usuário com `su`.

## Exemplos de uso

### Health check

```bash
curl -i http://localhost:8000/health
```

### Criar uma flag

```bash
curl -i -X POST http://localhost:8000/v1/flags   -H "Authorization: Bearer $TOKEN"   -H "X-Tenant-ID: tenant-a"   -H "Idempotency-Key: create-checkout-v2-001"   -H "Content-Type: application/json"   -d '{
    "key": "checkout.v2",
    "environment": "production",
    "enabled": true,
    "description": "Novo fluxo de checkout"
  }'
```

### Avaliar uma flag

```bash
curl -s   http://localhost:8000/v1/flags/production/checkout.v2/evaluate   -H "Authorization: Bearer $TOKEN"   -H "X-Tenant-ID: tenant-a" |
python3 -m json.tool
```

Resposta esperada:

```json
{
  "tenant_id": "tenant-a",
  "environment": "production",
  "key": "checkout.v2",
  "enabled": true,
  "source": "cache"
}
```

### Atualizar uma flag

```bash
curl -i -X PUT   http://localhost:8000/v1/flags/production/checkout.v2   -H "Authorization: Bearer $TOKEN"   -H "X-Tenant-ID: tenant-a"   -H "Idempotency-Key: update-checkout-v2-001"   -H "Content-Type: application/json"   -d '{
    "enabled": false,
    "description": "Checkout desativado temporariamente"
  }'
```

### Listar flags

```bash
curl -s   "http://localhost:8000/v1/flags?environment=production&limit=20"   -H "Authorization: Bearer $TOKEN"   -H "X-Tenant-ID: tenant-a" |
python3 -m json.tool
```

### Acompanhar eventos SSE

```bash
curl -N http://localhost:8000/v1/flags/events/stream   -H "Authorization: Bearer $TOKEN"   -H "X-Tenant-ID: tenant-a"
```

Evento esperado:

```text
event: flag.updated
data: {"type":"flag.updated","tenant_id":"tenant-a","environment":"production","key":"checkout.v2","enabled":false}
```

## Testes

Execute dentro do container:

```bash
docker compose exec api pytest -v
```

A suíte inclui testes de:

- avaliação via cache;
- cache miss e leitura do banco;
- atualização e sincronização;
- conflitos;
- recurso inexistente;
- idempotência;
- segurança JWT;
- hash de senha;
- erros HTTP;
- cache Redis;
- publicação de eventos;
- schema de resposta da API.

Resultado de referência:

```text
23 passed
Required test coverage of 85% reached
Total coverage: 87.68%
```

## Qualidade de código

```bash
docker compose exec api ruff check .
docker compose exec api mypy app
docker compose exec api pytest -v
```

Ou com Make:

```bash
make lint
make test
```

## Variáveis de ambiente

| Variável | Finalidade |
|---|---|
| `APP_NAME` | Nome da aplicação |
| `ENVIRONMENT` | Ambiente de execução |
| `DATABASE_URL` | URL assíncrona do PostgreSQL |
| `REDIS_URL` | URL do Redis |
| `JWT_SECRET` | Segredo de assinatura JWT |
| `JWT_ALGORITHM` | Algoritmo JWT |
| `JWT_EXPIRATION_MINUTES` | Expiração do token |
| `CACHE_TTL_SECONDS` | TTL das flags no Redis |

## Decisões técnicas

### Redis em vez de consulta constante ao banco

Avaliações de feature flags são operações de leitura frequente. O Redis reduz a
latência e evita sobrecarga no PostgreSQL.

### SSE em vez de polling

SSE mantém uma conexão HTTP simples e permite que a API envie alterações aos
clientes imediatamente, sem consultas repetitivas.

### Unit of Work

A Unit of Work concentra o ciclo de vida da transação e impede que a camada de
negócio dependa de detalhes da sessão SQLAlchemy.

### Repository Pattern

O repository desacopla consultas e persistência da lógica de negócio, facilitando
testes unitários com fakes.

### Idempotência distribuída

A chave é registrada no Redis com operação atômica e expiração, impedindo
processamento duplicado mesmo com várias instâncias da API.

### Isolamento multi-tenant

Tenant é aplicado ao JWT, queries, cache, eventos e logs, reduzindo o risco de
vazamento de dados entre clientes.

## Limitações e próximos passos

- implementar regras segmentadas por usuário, país ou percentual;
- adicionar histórico e auditoria de alterações;
- criar endpoint de autenticação e gestão de usuários;
- implementar RBAC;
- adicionar OpenTelemetry;
- criar dashboard administrativo;
- usar transactional outbox para garantia mais forte de entrega de eventos;
- adicionar rate limiting;
- publicar imagem em registry;
- configurar CI no GitHub Actions.

## Segurança

Não faça commit do arquivo `.env`.

Troque todos os segredos antes de implantar em produção.

Leia também [SECURITY.md](SECURITY.md).

## Licença

Distribuído sob a licença MIT. Consulte [LICENSE](LICENSE).
