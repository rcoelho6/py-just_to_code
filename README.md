# py-just_to_code — `feature/fastapi`

Port em Python/FastAPI do projeto [`just_to_code`](https://github.com/rcoelho6/just_to_code), baseado **exclusivamente na branch `main`**. A implementação substitui Flask pelo framework FastAPI e mantém Peewee + SQLite para persistência.

## Estrutura

| Arquivo | Responsabilidade |
|---|---|
| `app/__init__.py` | Application factory `create_app` e composição do banco/serviço. |
| `app/models.py` | Modelo Peewee, validações e DTO de saída. |
| `app/services.py` | Serviço de criação e atualização. |
| `app/routes.py` | Router FastAPI, parsing JSON e respostas HTTP. |
| `run.py` | Inicialização com Uvicorn. |

## Contrato preservado

| Método | Endpoint | Resultado |
|---|---|---|
| `POST` | `/tasks` ou `/tasks/` | Cria uma tarefa, responde `201` e envia `Location: /tasks/{id}`. |
| `PUT` | `/tasks/{id}` | Atualiza uma tarefa, responde `200`. |
| `GET` | `/tasks` e `/tasks/{id}` | Não implementado na origem (`405`). |
| `DELETE` | `/tasks/{id}` | Não implementado na origem (`405`). |

`description` não pode ser nula ou vazia, e `priority` deve ser um inteiro não negativo. Erros usam `{"message": "...", "status": <status HTTP>}`.

## Executar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
python run.py
```

A aplicação fica disponível em `http://localhost:8080`. O FastAPI também disponibiliza documentação interativa em `/docs` e `/redoc`.

Para usar outro banco SQLite:

```bash
DATABASE_URL='sqlite:///tmp/tasks.db' python run.py
```

## Testar

```bash
pytest
```

Os testes utilizam `fastapi.testclient.TestClient` e SQLite temporário.

## Alternativa ao Spring

Spring MVC foi substituído por FastAPI, e o servidor embutido é executado por Uvicorn. Spring Data JPA/H2 foi substituído por Peewee/SQLite, seguindo a base disponível na branch `main`. A composição explícita em `create_app` substitui a configuração automática do Spring.
