# Manual de estudo do `py-just_to_code` com Peewee

Este manual explica o código do projeto Flask que replica o POC `just_to_code`, originalmente implementado com Spring Boot, Spring Data JPA e H2. Nesta branch, `feature/layered-architecture`, o acesso ao SQLite é feito pelo **Peewee**, e o código é organizado em camadas inspiradas na arquitetura `main` do projeto Java.

> **Resumo:** a aplicação expõe `POST /tasks` para criar tarefas e `PUT /tasks/{id}` para atualizá-las. O projeto original não implementava listagem, consulta individual nem exclusão; por isso essas operações continuam fora do escopo.

## 1. Arquitetura

| Arquivo | Responsabilidade |
|---|---|
| `run.py` | Inicia o servidor Flask. |
| `app/__init__.py` | Composition root: cria Flask, SQLite, repositório, serviço e Blueprint. |
| `app/usecases/domain` | Entidade `Task` e regras de validação, sem dependências externas. |
| `app/usecases/ports` | Contrato `TaskRepository` usado pela aplicação. |
| `app/usecases/services` | Casos de uso de criação e atualização. |
| `app/infrastructure/persistence/models.py` | Modelo Peewee ligado à tabela SQLite. |
| `app/infrastructure/persistence/repositories.py` | Adapta Peewee ao contrato do repositório. |
| `app/application/ports.py` | Porta `TaskIncomeBoundary` entre o controller e os serviços. |
| `app/application/http` | Traduz HTTP/JSON para chamadas da porta de entrada. |
| `tests/test_tasks.py` | Testa a API usando o cliente de testes do Flask. |

O fluxo de uma criação é:

```text
Cliente HTTP
  -> POST /tasks
  -> Blueprint criado por app/application/http/routes.py
  -> Entidade Task em app/usecases/domain/entities.py
  -> TaskIncomeBoundary em app/application/ports.py
  -> TaskService em app/usecases/services/services.py
  -> TaskRepository em app/usecases/ports/ports.py
  -> PeeweeTaskRepository em app/infrastructure/persistence
  -> SQLite: INSERT na tabela task
  -> Resposta JSON 201 + Location: /tasks/{id}
```

### 1.1 Regra de dependência

A regra principal é que as camadas internas não conhecem detalhes externos. O domínio não importa Flask nem Peewee. A aplicação depende apenas da entidade e do protocolo `TaskRepository`. A infraestrutura conhece Peewee e implementa esse protocolo. A camada HTTP conhece Flask e chama a aplicação. O arquivo `app/__init__.py` conecta todas as peças.

Essa separação permite testar `TaskService` com um repositório em memória, sem iniciar Flask e sem abrir SQLite. Também permite substituir Peewee por outro mecanismo de persistência sem alterar a entidade ou as rotas.

## 2. Preparar e executar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
python run.py
```

A aplicação fica disponível em `http://localhost:8080`. Para criar uma tarefa:

```bash
curl -i -X POST http://localhost:8080/tasks \
  -H 'Content-Type: application/json' \
  -d '{"description":"Estudar Peewee","priority":1}'
```

A resposta esperada é semelhante a:

```http
HTTP/1.1 201 CREATED
Location: /tasks/1
Content-Type: application/json

{"description":"Estudar Peewee","priority":1}
```

Execute os testes com:

```bash
pytest
```

## 3. Como o Flask funciona

### 3.1 Application Factory

O objeto principal do Flask é criado por `create_app` em `app/__init__.py`:

```python
app = Flask(__name__)
```

O projeto usa o padrão **application factory**. Isso significa que a função cria uma nova aplicação sempre que é chamada. Assim, os testes podem usar um banco temporário sem alterar o banco de desenvolvimento.

```python
def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE_URL=os.getenv("DATABASE_URL", "sqlite:///tasks.db"),
        TESTING=False,
    )
    if test_config:
        app.config.update(test_config)
```

A configuração `DATABASE_URL` vem de variável de ambiente quando existir. Caso contrário, o arquivo padrão é `tasks.db`.

### 3.2 Blueprints e rotas

As rotas de tarefas são criadas por uma fábrica de Blueprint. A fábrica recebe `TaskIncomeBoundary` como dependência:

```python
def create_tasks_blueprint(service: TaskIncomeBoundary) -> Blueprint:
    blueprint = Blueprint("tasks", __name__, url_prefix="/tasks")
    ...
    return blueprint
```

O Blueprint é registrado no composition root com `app.register_blueprint(create_tasks_blueprint(service))`. O prefixo evita repetir `/tasks` em cada definição e a injeção explícita evita que a rota crie seu próprio banco ou serviço.

A criação aceita `/tasks` e `/tasks/`:

```python
@tasks_bp.route("", methods=["POST"])
@tasks_bp.route("/", methods=["POST"])
def create():
    ...
```

A atualização captura um número da URL:

```python
@tasks_bp.route("/<int:task_id>", methods=["PUT"])
def update(task_id: int):
    ...
```

O conversor `<int:task_id>` faz o Flask entregar o identificador como inteiro à função.

### 3.3 JSON, status e cabeçalhos

`request.is_json` verifica se o cliente informou um corpo JSON. Em seguida, `request.get_json(silent=True)` converte o corpo para um dicionário Python.

`jsonify` converte dicionários Python para JSON:

```python
return jsonify({"description": "Estudar", "priority": 1}), 200
```

Na criação, a resposta é construída para incluir o identificador do novo registro:

```python
response = jsonify(task_dto(task))
response.status_code = 201
response.headers["Location"] = f"/tasks/{task.id}"
return response
```

O status `201` significa que um recurso foi criado. O cabeçalho `Location` informa o endereço desse recurso.

### 3.4 Ciclo de vida da conexão

O Flask permite executar funções antes e depois de cada requisição. Este projeto abre o SQLite antes da requisição:

```python
@app.before_request
def open_database_connection():
    if database.is_closed():
        database.connect()
```

Depois, fecha a conexão:

```python
@app.teardown_request
def close_database_connection(_exception=None):
    if not database.is_closed():
        database.close()
```

O objetivo é não manter uma conexão aberta indefinidamente. Cada requisição usa a conexão necessária e a libera ao terminar.

### 3.5 Tratamento de erros

A função `error_response` garante um formato único:

```python
def error_response(message: str, status: int):
    return jsonify({"message": message, "status": status}), status
```

Erros de validação retornam `400`. Quando o identificador não existe, o serviço levanta `TaskNotFoundError` e a rota retorna `404`. Falhas inesperadas retornam `500`.

Os handlers de `405` e `404` também retornam JSON. Por isso, métodos ainda não implementados não produzem uma página HTML padrão do Flask.

## 4. Como o SQLite funciona

SQLite é um banco relacional embutido. Ele não precisa de um servidor separado. A base de dados fica em um arquivo, neste caso `tasks.db`.

Ele ainda possui tabelas, colunas, chaves, consultas e transações. A diferença é que o mecanismo roda dentro do processo da aplicação, e não como um serviço independente.

A URL padrão é:

```python
sqlite:///tasks.db
```

O prefixo `sqlite` define o banco. Os três caracteres `/` indicam um caminho relativo, e `tasks.db` é o arquivo.

Para escolher outro arquivo:

```bash
DATABASE_URL='sqlite:///tmp/tasks.db' python run.py
```

Para um caminho absoluto no Linux:

```bash
DATABASE_URL='sqlite:////tmp/py-just-to-code.db' python run.py
```

Nesta branch, `_sqlite_path` converte a URL para o formato de caminho que o Peewee espera. A implementação rejeita outros bancos porque o objetivo desta branch é estudar Peewee com SQLite.

## 5. Como o Peewee funciona

### 5.1 Database

O objeto `SqliteDatabase` representa a conexão e as operações com o arquivo SQLite:

```python
database = SqliteDatabase(
    _sqlite_path(app.config["DATABASE_URL"]),
    pragmas={"foreign_keys": 1},
)
```

O pragma `foreign_keys` instrui o SQLite a respeitar restrições de chave estrangeira. O modelo atual não possui uma relação, mas deixar essa opção ativa é uma configuração segura para futuras tabelas relacionadas.

A aplicação registra o objeto no `app.extensions`:

```python
app.extensions["database"] = database
```

As extensões do Flask são um local apropriado para guardar recursos ligados à aplicação. `get_database()` recupera esse objeto usando `current_app`.

### 5.2 Model e tabela

No Peewee, uma classe que herda de `Model` representa uma tabela. O projeto define uma classe base:

```python
class BaseModel(Model):
    class Meta:
        database = None
```

Depois define a tabela de tarefas:

```python
class PeeweeTask(BaseModel):
    id = AutoField()
    description = TextField(null=False)
    priority = IntegerField(null=False)

    class Meta:
        table_name = "task"
```

As colunas correspondem a:

- `AutoField`: chave primária inteira gerada automaticamente.
- `TextField`: texto da descrição.
- `IntegerField`: prioridade inteira.
- `null=False`: a coluna não pode receber `NULL`.

A aplicação liga o modelo ao banco criado para aquela instância:

```python
database.bind([PeeweeTask], bind_refs=False, bind_backrefs=False)
```

Essa ligação é especialmente útil nos testes, porque cada aplicação pode usar um arquivo SQLite diferente.

### 5.3 Criação da tabela

Depois de vincular o modelo, a aplicação abre o banco e cria a tabela se ela ainda não existir:

```python
database.connect(reuse_if_open=True)
database.create_tables([PeeweeTask])
database.close()
```

`create_tables` não é um sistema completo de migrações. Ele cria tabelas ausentes, mas não controla mudanças complexas em tabelas existentes. Em uma aplicação maior, use migrações versionadas, por exemplo com Peewee Migrate.

### 5.4 Inserção

No repositório, uma tarefa de domínio é inserida assim:

```python
with self._database.atomic():
    record = PeeweeTask.create(
        description=task.description,
        priority=task.priority,
    )
```

`create` gera um `INSERT` e atualiza `record.id` com o valor gerado pelo SQLite. A entidade de domínio continua independente do objeto Peewee.

O bloco `atomic()` abre uma transação. Se o bloco termina normalmente, a transação é confirmada. Se uma exceção ocorre, a transação é revertida.

### 5.5 Consulta

O serviço procura um registro com:

```python
existing = PeeweeTask.get_or_none(PeeweeTask.id == task.id)
```

O Peewee transforma essa expressão em uma consulta SQL parametrizada parecida com:

```sql
SELECT id, description, priority
FROM task
WHERE id = ?
LIMIT 1;
```

`get_or_none` retorna um objeto `PeeweeTask` quando encontra o registro e `None` quando não encontra. O repositório converte o resultado para a entidade `Task`; assim, a camada de aplicação não precisa conhecer Peewee.

Também é possível consultar diretamente no interpretador Python:

```python
task = Task.get_by_id(1)
print(task.description)
```

### 5.6 Atualização

Quando os valores mudaram, o serviço altera o objeto carregado e salva apenas as colunas modificadas:

```python
existing.description = task.description
existing.priority = task.priority
record.save(only=[PeeweeTask.description, PeeweeTask.priority])
```

O Peewee gera um `UPDATE` usando a chave primária do objeto. O argumento `only` deixa claro que o identificador não deve ser alterado.

Se os valores já são iguais, o serviço retorna sem executar `UPDATE`. Essa otimização preserva o comportamento da aplicação Java original.

### 5.7 Transações e rollback

O bloco:

```python
with database.atomic():
    ...
```

é a forma recomendada de agrupar operações relacionadas no Peewee. Uma criação ou atualização deve ser totalmente confirmada ou totalmente desfeita.

No caso de um erro, o contexto `atomic()` faz rollback automaticamente. Isso é diferente do código anterior com SQLAlchemy, que exigia chamar `session.rollback()` diretamente nas rotas.

## 6. Validação e contrato da API

A função `validate_task` rejeita descrição nula, descrição em branco, prioridade ausente, prioridade booleana e prioridade negativa. A função `build_task` também exige um identificador positivo quando está construindo uma atualização.

A validação fica fora do modelo Peewee porque os campos do ORM também podem ser usados por consultas e operações internas. `build_task` é o ponto explícito que transforma dados recebidos pela API em uma tarefa validada.

`task_dto` limita a resposta aos campos públicos do contrato:

```python
def task_dto(task: Task) -> dict:
    return {
        "description": task.description,
        "priority": task.priority,
    }
```

O `id` não aparece no corpo porque a API original o comunicava pelo cabeçalho `Location` na criação.

## 7. Endpoints

### Criar

```http
POST /tasks
Content-Type: application/json

{"description":"Ler Peewee","priority":2}
```

A rota valida o corpo, constrói uma tarefa, chama `TaskService.create` e retorna `201`.

### Atualizar

```http
PUT /tasks/1
Content-Type: application/json

{"description":"Ler Flask e Peewee","priority":1}
```

A rota valida o corpo e o identificador. O serviço procura a tarefa. Se não existir, retorna `404`; caso exista, atualiza seus campos.

### Operações ainda não implementadas

A origem não possuía:

- `GET /tasks`;
- `GET /tasks/{id}`;
- `DELETE /tasks/{id}`.

Elas continuam retornando `405 Method Not Allowed` para preservar o contrato original.

## 8. Testes

Os testes usam `create_app` com um SQLite temporário:

```python
@pytest.fixture
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "DATABASE_URL": f"sqlite:///{tmp_path / 'test.db'}",
    })
```

O teste de criação confirma status `201`, cabeçalho `Location`, JSON e persistência real:

```python
task = Task.get_by_id(1)
assert task.description == "created"
```

O cliente de testes do Flask envia requisições sem abrir uma porta TCP. Assim, a suíte verifica o comportamento HTTP com rapidez e isolamento.

Execute:

```bash
pytest
```

## 9. Comparação com Spring, SQLAlchemy e Peewee

| Conceito | Spring/Java | SQLAlchemy | Peewee |
|---|---|---|---|
| Rota HTTP | `@PostMapping` | Função Flask | Função Flask |
| Entidade | `@Entity` | Classe declarativa | Classe `Model` |
| Banco | H2 | `Engine` | `SqliteDatabase` |
| Sessão | `JpaRepository`/contexto JPA | `Session` | Conexão e `atomic()` |
| Consulta | `findById` | `select(...).where(...)` | `get_or_none(...)` |
| Inserção | `save` | `session.add` + `commit` | `model.save` |
| Atualização | `save` | alterar objeto + `commit` | alterar objeto + `save` |
| Transação | Gerenciada pelo framework | `Session` | `database.atomic()` |

Peewee é mais enxuto e explícito. Ele oferece menos abstrações automáticas que Spring Data, mas permite ver diretamente onde a conexão é aberta, onde a transação começa e onde o modelo é salvo.

## 10. Limitações e próximos passos

SQLite atende bem ao POC e ao desenvolvimento local. Para muitas escritas concorrentes ou alta disponibilidade, avalie PostgreSQL. Nesta branch, `_sqlite_path` aceita somente URLs SQLite de propósito.

O servidor iniciado por `python run.py` é adequado para desenvolvimento. Em produção, use um servidor WSGI e configure logs, variáveis de ambiente, backup e migrações.

Próximos exercícios recomendados:

1. Implementar `GET /tasks/{id}` usando `Task.get_or_none`.
2. Implementar `GET /tasks` usando `Task.select()`.
3. Implementar `DELETE /tasks/{id}` dentro de `database.atomic()`.
4. Adicionar uma tabela relacionada e testar `foreign_keys`.
5. Adicionar migrações com Peewee Migrate.
6. Adicionar índices para consultas frequentes.

## Referências

[1]: https://flask.palletsprojects.com/en/stable/ "Flask Documentation"
[2]: https://flask.palletsprojects.com/en/stable/patterns/appfactories/ "Flask Application Factories"
[3]: https://docs.peewee-orm.com/en/latest/peewee/quickstart.html "Peewee Quickstart"
[4]: https://docs.peewee-orm.com/en/latest/peewee/database.html "Peewee Database Documentation"
[5]: https://docs.peewee-orm.com/en/latest/peewee/transactions.html "Peewee Transactions"
[6]: https://www.sqlite.org/docs.html "SQLite Documentation"
[7]: https://docs.pytest.org/en/stable/ "pytest Documentation"
