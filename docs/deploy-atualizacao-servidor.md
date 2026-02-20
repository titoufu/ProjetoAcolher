# Atualizar o servidor a partir de mudanças no PC (Projeto Acolher)

Este roteiro descreve o fluxo seguro para publicar mudanças feitas no PC (desenvolvimento) no servidor Debian (produção local), minimizando erros e evitando conflitos no Git.

## Premissas

* O servidor roda com **Gunicorn (systemd)** + **Nginx**.
* O servidor deve usar sempre: `DJANGO_SETTINGS_MODULE=config.settings_prod` (para não depender do `config/settings.py` versionado).
* Arquivos de ambiente **não entram no Git**: `.env`, `staticfiles/`, `venv/`, etc.
* Regra de ouro: **no servidor, `git status` deve ficar limpo** quase sempre.

---

## Parte A — No PC (preparar e publicar as mudanças)

### 1) Confirmar branch e estado do repositório

Execute:

* `git status`
* `git branch`

Verifique:

* Você está na branch correta (a mesma usada no servidor).
* O `git status` lista somente alterações esperadas.

Opcional (confirma se está alinhado com remoto):

* `git fetch --all --prune`
* `git status`

---

### 2) Conferir exatamente o que mudou (evita mandar coisa errada)

Execute:

* `git diff --name-only`  *(mudanças ainda não “staged”)*

Se quiser ver também mudanças já “staged”:

* `git diff --cached --name-only`

Cuidados:

* Confirme que aparecem apenas os arquivos esperados (templates, urls, views, docs).
* Se aparecer algo “de servidor” (ex.: `.env`, `staticfiles/`, banco local), pare e revise o `.gitignore`.

---

### 3) Testar localmente antes do commit

* Suba o `runserver` (na porta que estiver livre).
* Teste o fluxo/rota alterada.
* Reabra as páginas afetadas e confirme que não quebrou layout.

Dica:

* Para templates, use **Ctrl+F5** (evitar cache do navegador).

---

### 4) Preparar o commit (resiliente: cobre novos, deletados e renomes)

> **Atenção:** `git commit -am ...` é prático, mas **não pega arquivos novos (untracked)**.

Fluxo recomendado (robusto):

1. Conferir novamente:

* `git status`

2. Adicionar **todas** as mudanças (inclui novos arquivos e deletados):

* `git add -A`

3. Conferir o que vai entrar no commit:

* `git status`
* (opcional) `git diff --cached`

4. Fazer o commit:

* `git commit -m "Mensagem clara aqui"`

**Se você não quiser adicionar tudo**, use `git add <arquivos>` em vez de `git add -A`.

---

### 5) Push para o GitHub

Antes do push, recomenda-se confirmar que não há divergência com remoto:

* `git status`

Agora:

* `git push`

Confira:

* O push foi para a branch correta (aparece no output).

---

## Parte B — No servidor (atualizar sem dor)

### 6) Conferir se o servidor está “clean” antes do pull

No servidor:

* `cd ~/apps/ProjetoAcolher`
* `git status`

Precisa estar:

* `working tree clean`
* sem arquivos “modified” ou “untracked” (exceto o que estiver corretamente ignorado)

Se NÃO estiver clean:

* Se for alteração temporária, use:

  * `git stash push -u -m "stash antes do pull"`
* Depois do pull, geralmente:

  * `git stash drop`

> **Regra de ouro:** evite editar arquivos versionados diretamente no servidor. Prefira editar no PC → commit/push → pull no servidor.

---

### 7) Puxar mudanças

Execute:

* `git pull`

Se aparecer erro do tipo “Your local changes would be overwritten”:

* Você tem arquivo modificado localmente no servidor.
* Soluções seguras:

  * **Se não precisa da mudança local:** `git restore <arquivo>` e repita `git pull`
  * **Se precisa preservar temporariamente:** `git stash push -u ...` e depois `git pull`

Se der conflito:

* Pare.
* Resolva com calma (idealmente no PC), faça commit e volte ao servidor para puxar novamente.

---

### 8) Aplicar mudanças conforme o tipo de alteração

#### 8.1) Alterou somente templates (HTML)

* `sudo systemctl restart acolher`

#### 8.2) Alterou código Python (views, urls, settings, etc.)

* `sudo systemctl restart acolher`

#### 8.3) Alterou arquivos estáticos (`static/` — CSS/JS/IMG)

* `python3 manage.py collectstatic --noinput --settings=config.settings_prod`
* `sudo systemctl reload nginx`
* (se mudou Python também) `sudo systemctl restart acolher`

#### 8.4) Alterou models (banco)

Preferência: gerar migrations no PC e commitar.

No servidor:

* `python3 manage.py migrate --settings=config.settings_prod`
* `sudo systemctl restart acolher`

---

### 9) Teste rápido no servidor (sem navegador)

Sugestão:

* use `curl -I` para checar status.

Exemplos:

* `/` → 302
* `/accounts/login/` → 200
* `/admin/` → 302
* `/static/img/logo.png` → 200

---

### 10) Teste na rede (outro PC)

* `http://192.168.0.234/`
* `http://192.168.0.234/admin/`

Se o admin estiver sem CSS:

* revise `collectstatic` e a configuração do Nginx em `/static/`.

---

### 11) Logs (diagnóstico)

Gunicorn:

* `sudo journalctl -u acolher -n 120 --no-pager`

Nginx:

* `sudo journalctl -u nginx -n 120 --no-pager`

---

## Parte C — Proteções anti-dor (essencial)

### 12) Produção não depende do `config/settings.py`

Servidor deve usar:

* `DJANGO_SETTINGS_MODULE=config.settings_prod`

Isso evita `git pull` quebrar DEBUG/DB/ALLOWED_HOSTS.

### 13) Garantir `.gitignore` adequado

No Git:

* `.env`
* `staticfiles/`
* `venv/`
* `db.sqlite3`

### 14) Manter servidor “clean”

Sempre:

* `git status` antes do `git pull`
* stash/drop consciente

---

## Fluxo ideal (resumo em 2 linhas)

1. PC: `pull → editar → testar → git add -A → commit → push`
2. Servidor: `status clean → pull → restart acolher → (collectstatic se necessário) → testar`

---

Se você quiser, eu também posso acrescentar um bloco “**Plano de emergência**” (como voltar ao commit anterior rapidamente com `git checkout <hash>` / tags), mas esse texto acima já cobre quase todos os problemas que você encontrou.
