# Projeto Acolher

Sistema Django para gestão de assistidos, benefícios, entregas e consultas.

## Documentação (Deploy e Operação)

- **Instalação/Deploy no Debian (Postgres + Gunicorn + Nginx):** `docs/deploy-instalacao-debian.md`
- **Atualizar servidor a partir de mudanças no PC (fluxo Git seguro):** `docs/deploy-atualizacao-servidor.md`

## Operação (atalhos)

- Reiniciar aplicação (Gunicorn/systemd): `sudo systemctl restart acolher`
- Reiniciar/recarregar Nginx: `sudo systemctl reload nginx`
- Logs:
  - App: `sudo journalctl -u acolher -n 120 --no-pager`
  - Nginx: `sudo journalctl -u nginx -n 120 --no-pager`