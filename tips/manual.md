# Manual de estudo: Clean Architecture com Flask, Peewee e SQLite

Este manual descreve a versão atual da branch `feature/clean-architecture`. Ela foi baseada na branch Java `feat/clean-arch`, mas usa dataclasses, `Protocol`, composição explícita e adaptadores idiomáticos de Python. A organização atual usa os diretórios `usecases`, `applications` e `infrastructures`.

## 1. Visão geral

Clean Architecture separa as regras centrais dos detalhes externos. A entidade e os casos de uso não precisam saber se a entrega acontece por Flask ou se a persistência acontece em SQLite. Esses detalhes ficam nas bordas e são conectados em `app/__init__.py`.

| Camada | Arquivo ou diretório | Função |
|---|---|---|
| Domínio | `app/clean_architecture/usecases/domains.py` | Entidade `Task` e invariantes. |
| Portas | `app/clean_architecture/usecases/ports.py` | Contratos de entrada e saída. |
| Caso de uso | `app/clean_architecture/usecases/service.py` | Criação e atualização de tarefas. |
| Applications | `app/clean_architecture/applications/controllers.py` | Rotas Flask e tradução HTTP. |
| DTOs | `app/clean_architecture/applications/dtos.py` | Tradução entre JSON e domínio. |
| Infrastructures | `app/clean_architecture/infrastructures/peewee_models.py` | Modelo persistente. |
| Datasource | `app/clean_architecture/infrastructures/peewee_datasource.py` | Implementação Peewee da persistência. |
| Composição | `app/__init__.py` | Montagem das dependências. |

O fluxo de uma criação é:

```text
Cliente HTTP
  -> applications/controllers.py
  -> applications/dtos.py
  -> usecases/domains.py: Task
  -> usecases/ports.py: TaskIncomeBoundary
  -> usecases/service.py: TaskService
  -> usecases/ports.py: TaskDatasourceBoundary
  -> infrastructures/peewee_datasource.py
  -> infrastructures/peewee_models.py
  -> SQLite
```

A regra de dependência aponta para dentro. O controller não importa `TaskService`; ele recebe a porta `TaskIncomeBoundary`. O serviço não importa Peewee; ele recebe `TaskDatasourceBoundary`. O domínio não importa Flask nem banco.

## 2. Domínio em `usecases/domains.py`

A entidade `Task` é uma dataclass imutável:

```python
@dataclass(frozen=True, slots=True)
class Task:
    description: str
    priority: int
    id: int | None = None
```

`frozen=True` impede alterações acidentais depois da criação. `slots=True` restringe os atributos aos campos declarados. O método `__post_init__` protege as invariantes: o identificador, quando presente, deve ser positivo; a descrição deve conter texto; e a prioridade deve ser um inteiro não negativo.

A exceção `TaskValidationError` pertence ao domínio. O controller a traduz para HTTP `400`, mas o domínio não conhece o significado de HTTP. Isso mantém a regra reutilizável por outros adaptadores.

## 3. Portas em `usecases/ports.py`

O arquivo de portas contém dois contratos usando `typing.Protocol`.

`TaskIncomeBoundary` é a porta de entrada. Ela descreve os casos de uso que um adaptador de entrega pode chamar: `create` e `update`.

`TaskDatasourceBoundary` é a porta de saída. Ela descreve o que o caso de uso precisa do armazenamento: criar, procurar e atualizar uma tarefa.

```python
@runtime_checkable
class TaskIncomeBoundary(Protocol):
    def create(self, task: Task) -> Task:
        ...

    def update(self, task: Task) -> None:
        ...
```

`Protocol` usa tipagem estrutural: uma classe pode satisfazer o contrato por possuir os métodos corretos, sem precisar herdar de uma classe-base. `runtime_checkable` permite uma verificação simples em testes:

```python
assert isinstance(service, TaskIncomeBoundary)
```

Essa verificação serve para confirmar a composição; ela não substitui injeção de dependências. A instância concreta ainda é criada explicitamente em `create_app`.

## 4. Caso de uso em `usecases/service.py`

`TaskService` implementa `TaskIncomeBoundary` e recebe `TaskDatasourceBoundary` no construtor:

```python
class TaskService(TaskIncomeBoundary):
    def __init__(self, task_source: TaskDatasourceBoundary):
        self._task_source = task_source
```

No caso de uso de criação, a entidade é encaminhada para a porta de persistência. No caso de atualização, o serviço procura a entidade pelo identificador. Se ela não existir, levanta `TaskNotFoundError`. Se descrição e prioridade forem iguais, não executa uma atualização desnecessária. Caso contrário, chama `update` no datasource.

```python
existing = self._task_source.find(task.id)
if existing is None:
    raise TaskNotFoundError("ID not found")
if existing.description == task.description and existing.priority == task.priority:
    return
self._task_source.update(task)
```

O serviço não conhece JSON, Flask, status HTTP, Peewee ou SQLite. Por isso, seus testes usam um datasource em memória.

## 5. Applications: controllers e DTOs

`applications/dtos.py` contém `TaskDto`. Ele recebe um dicionário JSON e cria uma entidade de domínio com `to_domain`. Para atualização, o identificador vem da URL e é passado como `task_id`.

`applications/controllers.py` contém `create_tasks_blueprint`. A fábrica recebe `TaskIncomeBoundary` como dependência:

```python
def create_tasks_blueprint(task_income_boundary: TaskIncomeBoundary) -> Blueprint:
    ...
```

Essa assinatura é importante. O controller não cria `TaskService`, não abre conexão e não conhece a implementação Peewee. Ele apenas traduz:

1. HTTP para um payload JSON.
2. Payload para `TaskDto`.
3. DTO para `Task`.
4. Chamada à porta de entrada.
5. Entidade resultante para JSON.
6. Exceções de domínio/aplicação para respostas HTTP.

A criação responde `201` e define `Location: /tasks/{id}`. A atualização responde `200`. Erros de validação respondem `400`, tarefa ausente responde `404` e falhas inesperadas respondem `500`.

## 6. Infrastructures e Peewee

`infrastructures/peewee_models.py` define `TaskModel`, uma representação de persistência distinta da entidade `Task`:

```python
class TaskModel(PeeweeBaseModel):
    id = AutoField()
    description = TextField(null=False)
    priority = IntegerField(null=False)
```

A separação impede que detalhes do ORM vazem para o domínio. `to_domain` converte um registro Peewee em `Task`.

`infrastructures/peewee_datasource.py` implementa `TaskDatasourceBoundary`. Ele usa `TaskModel.create`, `get_or_none` e `save` dentro de transações `database.atomic()`.

```python
with self._database.atomic():
    model = TaskModel.create(
        description=task.description,
        priority=task.priority,
    )
```

Se o bloco termina normalmente, a transação é confirmada. Se uma exceção acontece, o Peewee desfaz a operação. O `TaskService` não precisa conhecer esse detalhe.

## 7. Composition root em `app/__init__.py`

A função `create_app` é a application factory e o composition root. Ela cria o Flask, lê `DATABASE_URL`, instancia `SqliteDatabase`, associa `TaskModel`, cria a tabela e conecta os componentes:

```python
datasource = PeeweeTaskDatasource(database)
task_income_boundary = TaskService(datasource)
app.register_blueprint(create_tasks_blueprint(task_income_boundary))
```

As dependências são montadas de fora para dentro:

```text
SqliteDatabase
  -> PeeweeTaskDatasource
  -> TaskService
  -> TaskIncomeBoundary
  -> Flask Blueprint
```

O ciclo de vida da conexão é controlado por `before_request` e `teardown_request`. A conexão abre antes da requisição e fecha ao final. O banco padrão é `tasks.db`.

## 8. Flask e SQLite

Flask registra o Blueprint com o prefixo `/tasks`. As rotas disponíveis são `POST /tasks`, `POST /tasks/` e `PUT /tasks/<int:task_id>`. `GET` e `DELETE` continuam fora do escopo porque não estavam implementados no projeto original.

SQLite é um banco relacional embutido em arquivo. Ele não exige um servidor separado, o que o torna adequado para este POC e para testes temporários. A configuração padrão é:

```bash
python run.py
```

Para outro arquivo:

```bash
DATABASE_URL='sqlite:///tmp/tasks.db' python run.py
```

`create_tables` cria tabelas ausentes, mas não substitui migrações versionadas. Em uma aplicação maior, use uma ferramenta de migração e considere PostgreSQL para cenários de concorrência e disponibilidade maiores.

## 9. Testes

`tests/test_clean_architecture.py` testa o domínio e o serviço sem Flask, Peewee ou SQLite. `InMemoryDatasource` implementa os métodos necessários da porta de saída. O teste também verifica que `TaskService` implementa `TaskIncomeBoundary`.

`tests/test_tasks.py` testa a integração HTTP com SQLite temporário. Ele cobre criação, cabeçalho `Location`, validação, atualização, `404`, métodos não implementados e persistência do registro.

Execute a suíte com:

```bash
pytest
```

## 10. Comparação com a implementação Java

| Java `feat/clean-arch` | Python atual |
|---|---|
| Domínio `Task` | `usecases/domains.py: Task` |
| `TaskIncomeBoundary` | `usecases/ports.py: TaskIncomeBoundary` |
| `TaskDatasourceBoundary` | `usecases/ports.py: TaskDatasourceBoundary` |
| Serviço de caso de uso | `usecases/service.py: TaskService` |
| Presenter/DTO | `applications/dtos.py: TaskDto` |
| Controller | `applications/controllers.py` |
| Modelo JPA | `infrastructures/peewee_models.py: TaskModel` |
| Datasource JPA | `infrastructures/peewee_datasource.py: PeeweeTaskDatasource` |

A versão Python preserva a separação entre boundaries, casos de uso e adaptadores, mas usa dataclasses, `Protocol`, pytest e composição explícita em vez de anotações e injeção automática do Spring.

## 11. Limites e evolução

A branch mantém deliberadamente o escopo do POC. Autenticação, autorização, OpenAPI, `GET`, `DELETE` e migrações não foram adicionados. Novos casos de uso devem ser expostos por uma porta, implementados no serviço e conectados a adaptadores sem inserir dependências externas no domínio.

Para trocar o banco, implemente `TaskDatasourceBoundary` em outro datasource e altere somente a composição em `create_app`. O controller e o serviço não precisam saber qual tecnologia está por trás da porta.
