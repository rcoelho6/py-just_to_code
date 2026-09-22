# Manual de estudo: FastAPI, Peewee e SQLite

Esta branch, `feature/fastapi`, foi criada exclusivamente a partir de `main`. Ela troca o framework web Flask por FastAPI, mantendo o modelo de persistência Peewee + SQLite presente na base.

## 1. Fluxo da aplicação

```text
Cliente HTTP
  -> FastAPI Router em app/routes.py
  -> TaskService em app/services.py
  -> Modelo Peewee em app/models.py
  -> SQLite
```

`create_app` monta a aplicação e registra o router. O serviço concentra as operações de negócio; as rotas cuidam do HTTP e o modelo encapsula o acesso Peewee.

## 2. Application factory

`app/__init__.py` possui `create_app`. A função lê `DATABASE_URL`, converte `sqlite:///arquivo.db` para o caminho usado pelo Peewee, cria `SqliteDatabase`, vincula o modelo `Task`, cria a tabela e instancia `TaskService`.

```python
database = SqliteDatabase(_sqlite_path(settings["DATABASE_URL"]))
database.bind([Task], bind_refs=False, bind_backrefs=False)
database.create_tables([Task])
app.state.task_service = TaskService(database)
register_routes(app)
```

O objeto `app.state` é o espaço do FastAPI para compartilhar dependências de aplicação. O middleware abre a conexão antes da requisição e fecha depois dela.

## 3. Rotas FastAPI

`app/routes.py` usa `APIRouter`. As rotas são declaradas com decorators:

```python
@router.post("/tasks", status_code=201)
@router.post("/tasks/", status_code=201)
async def create(request: Request):
    ...
```

A função de criação lê o corpo JSON, cria uma entidade Peewee com `build_task`, chama `app.state.task_service.create` e devolve `JSONResponse`. O cabeçalho `Location` é definido explicitamente para preservar o contrato da main.

A atualização usa `/tasks/{task_id}`. FastAPI converte o parâmetro da URL para inteiro antes de chamar a função. A aplicação ainda valida descrição e prioridade e converte `TaskNotFoundError` para status `404`.

As operações `GET` e `DELETE` não possuem rotas registradas, portanto FastAPI retorna `405`. `POST /tasks/{id}` também não possui handler e permanece não permitido.

## 4. Por que o corpo é lido com `Request`

FastAPI oferece modelos Pydantic para validação automática. Nesta portabilidade, o corpo é lido manualmente com `await request.json()` para preservar o comportamento da main: payloads inválidos retornam `400` com o formato `{"message": ..., "status": 400}`. Se um modelo Pydantic fosse usado diretamente, o comportamento padrão seria uma resposta de validação `422`.

Depois do parsing, `build_task` mantém a regra central: descrição precisa conter texto e prioridade precisa ser um inteiro não negativo.

## 5. Serviço e Peewee

`TaskService` recebe uma instância de `peewee.Database`. Na criação, usa uma transação `database.atomic()` e salva a tarefa. Na atualização, procura por ID, evita um `save` se os valores não mudaram e levanta `TaskNotFoundError` quando a tarefa não existe.

O modelo `Task` é uma classe Peewee:

```python
class Task(BaseModel):
    id = AutoField()
    description = TextField(null=False)
    priority = IntegerField(null=False)
```

Peewee mapeia essa classe para a tabela SQLite `task`. `AutoField` cria o ID incremental; `TextField` armazena a descrição; `IntegerField` armazena a prioridade.

## 6. Uvicorn

`run.py` importa a aplicação e inicia o servidor ASGI:

```python
uvicorn.run(app, host="0.0.0.0", port=8080)
```

FastAPI é um framework ASGI. Uvicorn é o servidor que recebe conexões, executa a aplicação assíncrona e devolve as respostas HTTP. Em produção, o comando pode ser substituído por `uvicorn app:app --host 0.0.0.0 --port 8080`.

## 7. Documentação automática

Uma vantagem do FastAPI é a geração automática de documentação OpenAPI. Acesse:

- `/docs` para Swagger UI;
- `/redoc` para ReDoc;
- `/openapi.json` para o schema.

Esses endpoints são uma capacidade adicionada pelo FastAPI; o contrato de tarefas continua o mesmo da main.

## 8. Testes

`tests/test_tasks.py` usa `TestClient`, que permite chamar a aplicação FastAPI sem iniciar um processo Uvicorn real. Cada teste cria um banco SQLite temporário com `create_app` e verifica status, JSON, cabeçalho `Location` e persistência.

Execute:

```bash
pytest
```

## 9. Dependências

O `pyproject.toml` declara:

- `fastapi`: framework web e aplicação ASGI;
- `uvicorn`: servidor ASGI;
- `peewee`: ORM usado pela main;
- `pytest` e `httpx`: testes.

Flask não é usado nesta branch. A implementação foi criada a partir da main, sem trazer a estrutura das branches de arquiteturas anteriores.
