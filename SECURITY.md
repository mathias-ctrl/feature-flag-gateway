# Política de Segurança

## Relatando vulnerabilidades

Não abra uma issue pública contendo segredos, tokens, credenciais ou detalhes
exploráveis.

Envie o relato de forma privada ao mantenedor do repositório, incluindo:

- descrição;
- impacto;
- passos para reprodução;
- versão afetada;
- sugestão de correção, quando possível.

## Práticas importantes

- nunca faça commit do `.env`;
- altere o `JWT_SECRET` antes de produção;
- utilize TLS em produção;
- restrinja acesso ao PostgreSQL e Redis;
- rotacione credenciais periodicamente;
- use um gerenciador de segredos;
- limite origens e redes permitidas;
- monitore falhas de autenticação e idempotência.
