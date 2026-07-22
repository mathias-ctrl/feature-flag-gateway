# Contribuindo

Obrigado pelo interesse em contribuir.

## Preparação

```bash
cp .env.example .env
docker compose up -d --build
```

## Antes de abrir um Pull Request

```bash
docker compose exec api ruff check .
docker compose exec api mypy app
docker compose exec api pytest -v
```

## Regras

- siga PEP 8;
- use type hints;
- mantenha funções pequenas;
- preserve a separação entre domínio, serviços e infraestrutura;
- utilize Arrange, Act e Assert nos testes;
- adicione testes para toda correção ou funcionalidade;
- não reduza a cobertura mínima de 85%;
- não faça commit de segredos.

## Commits

Prefira mensagens objetivas:

```text
feat: add percentage rollout rules
fix: refresh flag after transaction commit
test: cover redis idempotency behavior
docs: improve local setup instructions
```
