# Manual de estudo do `py-just_to_code`

Este manual explica o código do projeto Flask que replica o POC `just_to_code`, originalmente implementado com Spring Boot, Spring Data JPA e H2. O objetivo é permitir que uma pessoa que ainda está aprendendo Python entenda o caminho completo de uma requisição HTTP, desde a entrada JSON até a persistência no SQLite.

> **Resumo do projeto:** a aplicação expõe `POST /tasks` para criar tarefas e `PUT /tasks/{id}` para atualizá-las. A branch de origem não implementava listagem, consulta individual ou exclusão; por isso, essas operações continuam fora do escopo deste port.

## 1. Visão geral da arquitetura

O projeto separa responsabilidades em quatro partes principais:

| Arquivo | Responsabilidade |
|---|---|
| `run.py` | Ponto de entrada para iniciar o servidor Flask. |
| `app/__init__.py` | Fábrica da aplicação, configuração do banco e ciclo de vida das sessões. |
| `app/routes.py` | Rotas HTTP, leitura do JSON, códigos de status e respostas de erro. |
| `app/models.py` | Modelo `Task`, mapeamento ORM e validação dos dados. |
| `app/services.py` | Regras de persistência e operações de criação e atualização. |
| `tests/test_tasks.py` | Testes de integração com o cliente de testes do Flask. |

O fluxo de uma criação é:

```text
Cliente HTTP
    |
    v
POST /tasks
    |
    v
Blueprint em app/routes.py
    |
    v
Task + validação em app/models.py
    |
    v
TaskService em app/services.py
    |
    v
Session do SQLAlchemy
    |
    v
SQLite: INSERT na tabela task
    |
    v
Resposta JSON 201 + Location: /tasks/{id}
```

A aplicação usa uma arquitetura em camadas simples. O Flask conhece a camada HTTP. O serviço conhece a persistência. O modelo representa os dados e suas regras básicas. Essa separação evita colocar toda a lógica dentro da função da rota.

## 2. Preparar o ambiente

Na raiz do projeto, crie um ambiente virtual e instale as dependências:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
```

O arquivo `pyproject.toml` declara duas dependências de execução:

- **Flask** fornece o servidor web, roteamento, objetos de requisição e respostas JSON.
- **SQLAlchemy** fornece o mapeamento objeto-relacional e a comunicação com o banco.

O grupo opcional `test` instala o **pytest**, usado para executar a suíte automatizada.

Para iniciar a aplicação:

```bash
python run.py
```

O servidor escuta em `0.0.0.0:8080`. Para testar a criação em outro terminal:

```bash
curl -i -X POST http://localhost:8080/tasks \
  -H 'Content-Type: application/json' \
  -d '{"description":"Estudar Flask","priority":1}'
```

A resposta esperada é semelhante a:

```http
HTTP/1.1 201 CREATED
Location: /tasks/1
Content-Type: application/json

{"description":"Estudar Flask","priority":1}
```

O arquivo `tasks.db` é criado automaticamente no diretório em que o processo é iniciado, porque a configuração padrão usa `sqlite:///tasks.db`.

## 3. Como o Flask funciona neste projeto

### 3.1 Aplicação e fábrica

O Flask representa a aplicação web em um objeto `Flask`. Neste projeto, esse objeto é criado por `create_app()` em `app/__init__.py`.

```python
app = Flask(__name__)
```

`__name__` informa ao Flask onde o módulo está localizado. Essa informação é usada para localizar recursos da aplicação.

A função `create_app` é chamada de **application factory**, ou fábrica da aplicação. Em vez de criar uma aplicação global com configuração fixa, ela constrói uma instância configurável:

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

Essa abordagem é importante por dois motivos. Primeiro, os testes podem usar um banco temporário sem modificar o banco de desenvolvimento. Segundo, o mesmo código pode ser iniciado com configurações diferentes para desenvolvimento, testes e produção.

O parâmetro `test_config` começa como `None`. Quando recebe um dicionário, suas opções substituem as configurações padrão. Os testes usam esse mecanismo para ativar `TESTING` e indicar um arquivo SQLite temporário.

### 3.2 Blueprint e rotas

As rotas são agrupadas em um `Blueprint`:

```python
tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")
```

Um Blueprint é um conjunto de rotas que pode ser registrado em uma aplicação. O `url_prefix` faz com que as rotas definidas como `""` e `"/"` sejam expostas como `/tasks` e `/tasks/`.

A rota de criação aceita as duas formas:

```python
@tasks_bp.route("", methods=["POST"])
@tasks_bp.route("/", methods=["POST"])
def create():
    ...
```

A rota de atualização captura o identificador da URL:

```python
@tasks_bp.route("/<int:task_id>", methods=["PUT"])
def update(task_id: int):
    ...
```

O conversor `<int:task_id>` faz o Flask aceitar apenas um valor inteiro nessa posição e entrega esse valor à função como `task_id`.

O Blueprint é registrado em `create_app`:

```python
app.register_blueprint(tasks_bp)
```

Sem esse registro, o Flask conheceria o Blueprint, mas as rotas não fariam parte da aplicação final.

### 3.3 Requisição e resposta

O objeto `request` representa a requisição HTTP atual. A função `read_payload` verifica se o cliente enviou JSON:

```python
if not request.is_json:
    return None, error_response("Erro with status 400: Request must be JSON", 400)
```

Depois, o corpo é convertido para um objeto Python:

```python
payload = request.get_json(silent=True)
```

Um objeto JSON como:

```json
{"description": "Estudar Flask", "priority": 1}
```

vira um dicionário Python equivalente a:

```python
{"description": "Estudar Flask", "priority": 1}
```

`jsonify` transforma um dicionário Python em uma resposta JSON e define o cabeçalho `Content-Type` apropriado:

```python
return jsonify({"description": "Estudar Flask", "priority": 1}), 200
```

Também é possível construir a resposta, alterar seu status e adicionar cabeçalhos:

```python
response = jsonify(task_dto(task))
response.status_code = 201
response.headers["Location"] = f"/tasks/{task.id}"
return response
```

O código `201 Created` informa que um recurso foi criado. O cabeçalho `Location` informa o endereço lógico desse novo recurso.

### 3.4 Contexto da aplicação e contexto da requisição

Durante uma requisição, o Flask mantém objetos contextuais, como `current_app` e `request`. A função `get_session` usa `current_app` para obter a fábrica de sessões configurada na aplicação atual:

```python
from flask import current_app

session = current_app.extensions["session_factory"]()
```

Isso evita uma variável global de sessão compartilhada por todas as requisições. Cada requisição recebe sua própria sessão.

Ao final da requisição, Flask chama a função registrada com `@app.teardown_appcontext`:

```python
@app.teardown_appcontext
def close_session(_exception=None):
    session = getattr(app, "_request_session", None)
    if session is not None:
        session.close()
        app._request_session = None
```

Fechar a sessão libera recursos e impede que uma sessão seja reutilizada acidentalmente depois do fim da requisição.

### 3.5 Tratamento de erros

A função auxiliar `error_response` padroniza o formato das falhas:

```python
def error_response(message: str, status: int):
    return jsonify({"message": message, "status": status}), status
```

As rotas capturam erros de validação, recurso inexistente e falhas inesperadas. Por exemplo, quando o serviço não encontra o identificador solicitado, a rota retorna `404`:

```python
except TaskNotFoundError as exc:
    get_session().rollback()
    return error_response(f"Erro with status 404: {exc}", 404)
```

Os handlers do Blueprint tratam métodos e caminhos que não estão implementados:

```python
@tasks_bp.errorhandler(405)
def method_not_allowed(_error):
    return error_response("Method not allowed", 405)
```

Assim, a API mantém uma resposta JSON mesmo quando o Flask rejeita o método HTTP antes de executar uma função de rota.

## 4. Como o SQLite funciona neste projeto

### 4.1 O que é SQLite

SQLite é um banco de dados relacional embutido. Ele não precisa de um servidor separado. O banco inteiro pode ser armazenado em um único arquivo, como `tasks.db`.

Essa característica é conveniente para um POC, exemplos locais e testes. O processo Flask abre o arquivo, executa comandos SQL e fecha os recursos por meio do driver e do SQLAlchemy.

SQLite não é o mesmo que um banco “sem estrutura”. Ele continua oferecendo tabelas, colunas, tipos, chaves e transações. A diferença principal é que o mecanismo roda dentro do processo da aplicação, em vez de rodar como um serviço de banco separado.

### 4.2 A URL de conexão

A configuração padrão é:

```python
DATABASE_URL=os.getenv("DATABASE_URL", "sqlite:///tasks.db")
```

A expressão significa:

- `sqlite` é o dialeto do banco.
- `///` indica um caminho relativo ao diretório atual do processo.
- `tasks.db` é o arquivo usado pelo banco.

Para um caminho absoluto em Linux, pode-se usar uma URL como:

```bash
DATABASE_URL='sqlite:////tmp/py-just-to-code.db' python run.py
```

Para testes, o projeto recebe uma URL temporária criada pelo pytest:

```python
{"DATABASE_URL": f"sqlite:///{tmp_path / 'test.db'}"}
```

Cada execução de teste fica isolada em seu próprio arquivo.

### 4.3 Engine, Base e metadados

O **engine** é o objeto que sabe como conectar o SQLAlchemy ao banco:

```python
engine = create_engine(app.config["DATABASE_URL"], future=True)
```

O projeto define uma classe base para os modelos ORM:

```python
class Base(DeclarativeBase):
    pass
```

`Task` herda de `Base`. Com isso, o SQLAlchemy registra a definição da tabela nos metadados:

```python
class Task(Base):
    __tablename__ = "task"
```

Na criação da aplicação, o projeto executa:

```python
Base.metadata.create_all(engine)
```

Esse comando cria as tabelas que ainda não existem. Ele não é um sistema completo de migrações: não renomeia colunas antigas nem controla com segurança alterações complexas de schema. Para este POC, ele é suficiente. Em um sistema maior, uma alternativa é usar Alembic para migrações versionadas.

### 4.4 A tabela `task`

O modelo define três colunas:

```python
id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
description: Mapped[str] = mapped_column(String, nullable=False)
priority: Mapped[int] = mapped_column(Integer, nullable=False)
```

O SQLAlchemy mapeia essas declarações para uma tabela equivalente a:

```sql
CREATE TABLE task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description VARCHAR NOT NULL,
    priority INTEGER NOT NULL
);
```

O `id` identifica cada tarefa. O SQLite gera esse valor quando uma nova tarefa é inserida. `nullable=False` impede que a coluna seja nula no banco, embora a validação da aplicação produza mensagens mais claras antes da tentativa de inserção.

### 4.5 Sessão e transação

A `sessionmaker` cria sessões conectadas ao engine:

```python
session_factory = sessionmaker(bind=engine, expire_on_commit=False)
```

A sessão representa uma unidade de trabalho. No método `create`, a tarefa é adicionada, a transação é confirmada e o objeto é atualizado com o identificador criado:

```python
self.session.add(task)
self.session.commit()
self.session.refresh(task)
```

A sequência é importante:

1. `add` coloca o objeto no conjunto de mudanças pendentes.
2. `commit` envia o `INSERT` ao SQLite e confirma a transação.
3. `refresh` lê os valores persistidos, incluindo o `id` gerado.

Quando há um erro depois de uma operação que poderia ter iniciado uma transação, a rota chama `rollback`:

```python
get_session().rollback()
```

O rollback desfaz as alterações não confirmadas da sessão. Sem ele, uma sessão pode permanecer em estado de erro e não aceitar operações posteriores.

### 4.6 Consulta e atualização

O serviço procura uma tarefa por identificador com uma expressão SQLAlchemy:

```python
existing = self.session.scalar(
    select(Task).where(Task.id == task.id)
)
```

O SQLAlchemy traduz essa expressão para SQL equivalente a:

```sql
SELECT id, description, priority
FROM task
WHERE id = ?;
```

O valor é enviado como parâmetro, em vez de ser concatenado manualmente no SQL. Essa forma reduz riscos de injeção e mantém a consulta estruturada.

Se os valores não mudaram, o serviço não executa uma atualização:

```python
if existing.description == task.description and existing.priority == task.priority:
    return
```

Se mudaram, o serviço altera a entidade existente e confirma a transação:

```python
existing.description = task.description
existing.priority = task.priority
self.session.commit()
```

Essa implementação atualiza a entidade carregada pelo banco. Ela não substitui o objeto recebido diretamente, porque o objeto recebido é um modelo temporário usado para transportar os dados validados da requisição.

## 5. O modelo e as validações

### 5.1 Construtor de `Task`

O construtor permite receber `description`, `priority` e opcionalmente `id`:

```python
def __init__(self, description: str, priority: int,
             id: int | None = None, *, updating: bool = False):
```

Quando `updating=True`, o identificador precisa ser positivo. Essa regra reproduz a validação da entidade Java para atualizações.

Depois, o construtor chama `validate_task`:

```python
validate_task(description, priority)
```

A validação rejeita descrição nula, descrição que contém somente espaços, prioridade nula, prioridade booleana e prioridade negativa. A rejeição explícita de `bool` é necessária porque, em Python, `bool` é uma subclasse de `int`; sem essa verificação, `True` poderia ser aceito como prioridade `1`.

### 5.2 DTO e resposta

A função `task_dto` converte o modelo ORM em um dicionário que representa o contrato público:

```python
def task_dto(task: Task) -> dict:
    return {
        "description": task.description,
        "priority": task.priority,
    }
```

O `id` não é incluído no corpo porque a API original retornava apenas os campos do `TaskDto`. O identificador fica disponível no cabeçalho `Location` após a criação.

## 6. Endpoints disponíveis

### 6.1 Criar tarefa

Requisição:

```http
POST /tasks
Content-Type: application/json

{"description":"Ler a documentação","priority":2}
```

O caminho da requisição é:

1. `read_payload` verifica o cabeçalho JSON.
2. `Task` valida os campos.
3. `TaskService.create` faz `INSERT` e confirma a transação.
4. A rota monta a resposta `201`.

### 6.2 Atualizar tarefa

Requisição:

```http
PUT /tasks/1
Content-Type: application/json

{"description":"Ler Flask e SQLite","priority":1}
```

A rota cria um objeto temporário com o `id` recebido na URL. O serviço consulta a tarefa existente. Se ela não existir, retorna `404`. Caso exista, os campos são comparados e eventualmente atualizados.

### 6.3 Métodos que ainda não existem

A origem na branch `main` não tinha implementação para:

- `GET /tasks`
- `GET /tasks/{id}`
- `DELETE /tasks/{id}`

Por isso, o port responde `405 Method Not Allowed` para essas operações. Essa decisão preserva o contrato da origem. Se a API precisar evoluir, essas funcionalidades podem ser adicionadas em uma mudança separada, com testes e documentação próprios.

## 7. Testes

A suíte usa `app.test_client()`, que permite enviar requisições à aplicação sem abrir uma porta TCP. O fixture `app` cria uma aplicação de teste com um arquivo SQLite temporário:

```python
@pytest.fixture
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "DATABASE_URL": f"sqlite:///{tmp_path / 'test.db'}",
    })
```

O teste de criação verifica três comportamentos: status `201`, cabeçalho `Location` e persistência real no banco. A consulta direta ao SQLAlchemy confirma que o registro foi gravado.

Os testes também verificam validações, atualização, recurso inexistente e métodos não implementados:

```bash
pytest
```

Uma suíte maior pode incluir testes de payload JSON inválido, prioridade decimal, concorrência, rollback e migrações. Esses casos não eram necessários para reproduzir o contrato original, mas são bons próximos exercícios.

## 8. Comparação com a versão Java

A correspondência conceitual entre as implementações é:

| Spring/Java | Flask/Python | Função equivalente |
|---|---|---|
| `@RestController` | Blueprint com funções de rota | Receber requisições HTTP |
| `@RequestMapping("/tasks")` | `url_prefix="/tasks"` | Definir prefixo de URL |
| `@PostMapping` | `@route(..., methods=["POST"])` | Registrar método HTTP |
| `@RequestBody` | `request.get_json()` | Ler corpo JSON |
| `ResponseEntity` | `jsonify(...), status` | Montar resposta e status |
| Entidade JPA `@Entity` | Classe `Task` declarativa | Mapear objeto para tabela |
| `JpaRepository` | `Session` + `select` | Consultar e persistir dados |
| `@Service` | `TaskService` | Isolar regras de aplicação |
| H2 | SQLite | Banco relacional local |
| JUnit + Spring Test | pytest + `test_client` | Testar comportamento HTTP |

A equivalência não é uma tradução linha a linha. Flask não fornece automaticamente um container de injeção, um repositório gerado ou um ciclo de vida JPA. Essas responsabilidades são explícitas no código Python.

## 9. Limitações e próximos passos

O uso de `create_all` simplifica o início do POC, mas não substitui migrações. Para evolução do schema, adicione Alembic e registre cada alteração de tabela.

SQLite é adequado para desenvolvimento e pequenos usos locais. Em um serviço com muitas escritas concorrentes ou requisitos de alta disponibilidade, avalie PostgreSQL. O serviço já recebe a URL por configuração, então a troca pode ser feita sem alterar as rotas.

A aplicação não possui autenticação, autorização, paginação ou documentação OpenAPI. Esses recursos também não existiam na branch de origem. Ao adicioná-los, mantenha testes que descrevam o novo contrato.

O servidor embutido iniciado por `python run.py` é apropriado para desenvolvimento. Em produção, use um servidor WSGI, como Gunicorn, atrás de um proxy reverso e configure logs, variáveis de ambiente e políticas de backup.

## 10. Exercícios sugeridos

1. Implemente `GET /tasks/{id}` e adicione um teste para os casos `200` e `404`.
2. Implemente `GET /tasks` com ordenação por `priority`.
3. Implemente `DELETE /tasks/{id}` e defina se a resposta será `204` ou um corpo JSON.
4. Substitua `Base.metadata.create_all` por migrações Alembic.
5. Adicione um campo `completed` e atualize o modelo, os testes e a documentação.
6. Execute a aplicação com um banco PostgreSQL por meio de `DATABASE_URL`.

## Referências

[1]: https://flask.palletsprojects.com/en/stable/ "Flask Documentation"
[2]: https://flask.palletsprojects.com/en/stable/patterns/appfactories/ "Flask Application Factories"
[3]: https://docs.sqlalchemy.org/en/20/orm/quickstart.html "SQLAlchemy ORM Quick Start"
[4]: https://docs.sqlalchemy.org/en/20/core/engines.html "SQLAlchemy Engine Configuration"
[5]: https://www.sqlite.org/docs.html "SQLite Documentation"
[6]: https://docs.pytest.org/en/stable/ "pytest Documentation"
