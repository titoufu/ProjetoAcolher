# Atualizar o servidor a partir de mudanças no PC (Projeto Acolher)

Este roteiro descreve o fluxo seguro para publicar mudanças feitas no PC (desenvolvimento)
no servidor Debian (produção local), minimizando erros e evitando conflitos no Git.

## Premissas

- O servidor roda com **Gunicorn (systemd)** + **Nginx**.
- O servidor deve usar sempre: `DJANGO_SETTINGS_MODULE=config.settings_prod`
  (para não depender do `config/settings.py` versionado).
- Arquivos de ambiente **não entram no Git**: `.env`, `staticfiles/`, `venv/`, etc.

---

## Parte A — No PC (preparar e publicar as mudanças)

### 1) Confirmar branch e estado do repositório
Execute:
- `git status`
- `git branch`

Verifique:
- Você está na branch correta (a mesma usada no servidor).
- O `git status` lista somente as alterações que você pretende publicar.

---

### 2) Conferir exatamente o que mudou
Execute:
- `git diff --name-only`

Cuidados:
- Confirme que aparecem apenas os arquivos esperados (ex.: templates, urls, views).
- Se aparecer algo que “não deveria ir para produção”, pare e revise.

---

### 3) Testar localmente antes do commit
- Suba o `runserver` (na porta que estiver livre).
- Teste o fluxo/rota alterada.
- Reabra páginas afetadas e confirme que não quebrou layout.

Dica:
- Para templates, use **Ctrl+F5** (evitar cache do navegador).

---

### 4) Commit (somente o que deve ir)
Execute:
- `git status` (última conferência)
- `git commit -am "Mensagem clara aqui"` (ou `git add` + `git commit`)

Não comitar:
- `.env`
- `staticfiles/`
- `venv/`
- `__pycache__/`, `*.pyc`
- arquivos locais de editor (`.vscode/`, etc.)

---

### 5) Push para o GitHub
Execute:
- `git push`

Confira:
- O push foi para a branch correta (aparece no output).

---

## Parte B — No servidor (atualizar sem dor)

### 6) Conferir se o servidor está “clean”
No servidor:
- `cd ~/apps/ProjetoAcolher`
- `git status`

Precisa estar:
- `working tree clean`
- sem arquivos “modified” ou “untracked” (exceto o que estiver corretamente ignorado)

Se NÃO estiver clean:
- Se for alteração temporária, use:
  - `git stash push -u -m "stash antes do pull"`
- Depois do `pull`, geralmente:
  - `git stash drop` (na maioria dos casos)

Regra de ouro:
- O servidor deve ficar **clean** quase sempre.

---

### 7) Puxar mudanças
Execute:
- `git pull`

Se der conflito:
- Pare.
- Resolva com calma (idealmente no PC), faça commit e volte ao servidor para puxar novamente.

---

### 8) Aplicar mudanças conforme o tipo de alteração

#### 8.1) Alterou somente templates (HTML)
- `sudo systemctl restart acolher`

#### 8.2) Alterou código Python (views, urls, settings, serviços)
- `sudo systemctl restart acolher`

#### 8.3) Alterou arquivos estáticos (`static/` — CSS/JS/IMG)
- `python3 manage.py collectstatic --noinput --settings=config.settings_prod`
- `sudo systemctl reload nginx`
- (se mudou Python também) `sudo systemctl restart acolher`

#### 8.4) Alterou models (banco)
Preferência: gerar migrations no PC e commitar.

No servidor:
- `python3 manage.py migrate --settings=config.settings_prod`
- `sudo systemctl restart acolher`

---

### 9) Teste rápido no servidor (sem navegador)
Exemplos:
- `/` → 302
- `/accounts/login/` → 200
- `/admin/` → 302
- `/static/img/logo.png` → 200

Sugestão:
- use `curl -I` para checar status.

---

### 10) Teste na rede (outro PC)
- `http://192.168.0.234/`
- `http://192.168.0.234/admin/`

Se o admin estiver sem CSS:
- revise `collectstatic` e a configuração do Nginx em `/static/`.

---

### 11) Logs (diagnóstico)
Gunicorn:
- `sudo journalctl -u acolher -n 120 --no-pager`

Nginx:
- `sudo journalctl -u nginx -n 120 --no-pager`

---

## Parte C — Proteções anti-dor (essencial)

### 12) Produção não depende do `config/settings.py`
Servidor deve usar:
- `DJANGO_SETTINGS_MODULE=config.settings_prod`

Isso evita `git pull` quebrar DEBUG/DB/ALLOWED_HOSTS.

### 13) Garantir `.gitignore` adequado
No Git:
- `.env`
- `staticfiles/`
- `venv/`
- `db.sqlite3`

### 14) Manter servidor “clean”
Sempre:
- `git status` antes do `git pull`
- stash/drop consciente

---

## Fluxo ideal (resumo em 2 linhas)

1) PC: `pull → editar → testar → commit → push`  
2) Servidor: `status clean → pull → restart acolher → (collectstatic se necessário) → testar`