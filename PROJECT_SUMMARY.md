# Resumo do Projeto

## Problema

Aplicações que dependem de deploy para ativar ou desativar funcionalidades
possuem maior risco operacional, resposta lenta a incidentes e baixa
flexibilidade para liberações graduais.

## Solução

Foi desenvolvido um gateway centralizado de feature flags, multi-tenant e
assíncrono, capaz de avaliar flags pelo Redis e propagar alterações em tempo
real usando Redis Pub/Sub e Server-Sent Events.

## Como foi feito

A API foi construída com FastAPI e Pydantic. A persistência utiliza SQLAlchemy
2.0 assíncrono e PostgreSQL. Repository Pattern, Unit of Work, Dependency
Injection e Factory separam a lógica de negócio da infraestrutura.

Redis é usado para três responsabilidades distintas:

1. cache distribuído;
2. eventos Pub/Sub;
3. idempotência de requisições.

JWT protege as rotas e carrega o tenant da sessão. O tenant também está presente
nas consultas, chaves de cache e canais de eventos.

## Resultado

- avaliação rápida por cache;
- atualização sem novo deploy;
- sincronização em tempo real;
- isolamento multi-tenant;
- operações mutáveis idempotentes;
- execução local totalmente containerizada;
- 23 testes automatizados;
- cobertura superior a 85%;
- documentação de uso e publicação.
