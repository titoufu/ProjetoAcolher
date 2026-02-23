# Projeto Acolher — Rotina DEV → PROD (Git + Docker/WSL)

Este projeto roda em:

- **DEV (Windows + VSCode):** normalmente com SQLite e `DJANGO_DEBUG=1`
- **PROD (Windows + WSL + Docker):** Postgres em container, `DJANGO_DEBUG=0`, acesso via LAN

---

## Regras de ouro

1) **NUNCA commitar `.env`** (fica local em cada máquina).  
2) **Config de ambiente vem do `.env`** (DEBUG, ALLOWED_HOSTS, DB_ENGINE/DB_* etc.).  
3) No servidor (PROD), **não editar código manualmente**. Tudo via `git pull`.

---

## DEV (Windows/VSCode) — rotina padrão

```bash
git add -A
git commit -m "mensagem"
git push
```

---

## PROD (Servidor) — rotina padrão após um push

No WSL (Ubuntu), dentro do projeto:

```bash
cd ~/apps/ProjetoAcolher
git pull
docker compose up -d --build
```

Depois, aplique os comandos conforme o tipo de mudança (abaixo).

---

## O que fazer no PROD conforme o tipo de mudança

### 1) Mudei APENAS HTML/CSS/JS (templates/static)
Ex.: `templates/`, `static/`, ajustes de layout.

```bash
docker compose exec web python manage.py collectstatic --noinput
docker compose restart web
```

---

### 2) Mudei VIEW / URL / SERVICE (Python, mas SEM models)
Ex.: `views.py`, `urls.py`, `services/*.py`, templates etc.

```bash
docker compose restart web
```

> Se você também mexeu em static, rode `collectstatic` (item 1).

---

### 3) Mudei MODELS / ESTRUTURA DO BANCO (criar/alterar tabelas)
Ex.: `models.py`, constraints, campos novos.

**No DEV (recomendado):**
```bash
python manage.py makemigrations
```

**No PROD:**
```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
docker compose restart web
```

> Observação: em PROD, o ideal é que as migrations já venham do Git (criadas no DEV).  
> No PROD, geralmente você roda apenas `migrate`.

---

### 4) Mudei USUÁRIOS / GRUPOS / PERMISSÕES

#### A) Só criei/ajustei usuários pelo admin
Nada técnico a fazer; apenas use o `/admin/`.

#### B) Criei grupos/permissões no código (decorators, helpers `is_operador`/`is_gestor`, etc.)
```bash
docker compose restart web
```

#### C) Preciso criar um superusuário (se sumiu/zerou)
```bash
docker compose exec web python manage.py createsuperuser
```

#### D) Preciso resetar senha de um usuário
```bash
docker compose exec web python manage.py changepassword NOME_DO_USUARIO
```

---

## Checagens rápidas (produção)

### Ver se subiu
```bash
docker compose ps
```

### Ver logs (erro 500, etc.)
```bash
docker compose logs --tail=200 web
docker compose logs --tail=200 db
```

### Testes de URL no servidor
```bash
curl -I http://127.0.0.1:8080/admin/
curl -I http://127.0.0.1:8080/static/admin/css/base.css
```

---

## Importante: Static/WhiteNoise

Em PROD com `DEBUG=0`, o Django não serve static sozinho.  
Este projeto usa **WhiteNoise**, então após alterações em static:

- rode `collectstatic`
- reinicie o `web`

---

## Endereços

- **Local no servidor:** `http://localhost:8080/`
- **Rede local:** `http://IP_DO_SERVIDOR:8080/` (ex.: `http://192.168.0.30:8080/`)
r: http://localhost:8080/

Rede local: http://IP_DO_SERVIDOR:8080/ (ex.: http://192.168.0.30:8080/)