# Manual de estudo: Clean Architecture com Flask, Peewee e SQLite

Este manual explica a branch `feature/clean-architecture` do projeto `py-just_to_code`. Ela foi baseada na branch Java `feat/clean-arch` do projeto `just_to_code` e mantém o mesmo contrato HTTP, mas usa convenções Python, `Protocol`, dataclasses, injeção explícita e adaptadores independentes.

## 1. Ideia central

Clean Architecture organiza o código em círculos. As regras mais importantes ficam no centro e não conhecem detalhes externos. Flask, Peewee, SQLite e JSON ficam nas bordas.

> **Regra de dependência:** dependências de código apontam para dentro. O domínio não importa o banco. O caso de uso não importa Flask. A infraestrutura implementa uma interface definida por uma camada interna.

Nesta implementação, os círculos são:

| Círculo | Pacote | Conteúdo |
|---|---|---|
| Domínio | `app/clean_architecture/domain` | Entidade `Task` e validações invariantes. |
| Casos de uso | `app/clean_architecture/usecases` | Boundaries e `TaskService`. |
| Adaptadores | `app/clean_architecture/adapters` | Controller Flask e presenters. |
| Frameworks | `app/clean_architecture/frameworks` | Modelo Peewee, SQLite e datasource. |
| Composição | `app/__init__.py` | Montagem das dependências concretas. |

O caminho de uma requisição é:

```text
HTTP/JSON
  -> adapters/controllers.py
  -> TaskDto
  -> domain.Task
  -> usecases.TaskService
  -> usecases.TaskDatasourceBoundary
  -> frameworks.PeeweeTaskDatasource
  -> frameworks.TaskModel
  -> SQLite
```

## 2. Domínio

O domínio está em `app/clean_architecture/domain/task.py`. A entidade é uma dataclass imutável:

```python
@dataclass(frozen=True, slots=True)
class Task:
    description: str
    priority: int
    id: int | None = None
```

`frozen=True` impede que uma entidade seja alterada silenciosamente depois de criada. Para representar uma nova versão, o código cria outro objeto. `slots=True` evita um dicionário de atributos por instância e comunica que a entidade possui apenas os campos declarados.

O método `__post_init__` valida invariantes. Uma descrição vazia e uma prioridade negativa não formam uma tarefa válida. A entidade também rejeita um identificador não positivo quando ele existe.

O domínio não importa Flask, Peewee, SQLAlchemy, SQLite ou qualquer biblioteca HTTP. Isso permite importar e testar `Task` em qualquer contexto Python.

## 3. Boundaries e casos de uso

O arquivo `usecases/ports.py` define duas boundaries usando `typing.Protocol`.

`TaskIncomeBoundary` é a porta de entrada. Ela descreve o que um adaptador externo pode pedir à aplicação: criar e atualizar uma tarefa.

`TaskDatasourceBoundary` é a porta de saída. Ela descreve o que a aplicação precisa do armazenamento: criar, procurar e atualizar uma tarefa.

Um `Protocol` é uma forma de tipagem estrutural. Uma classe não precisa herdar explicitamente de `TaskDatasourceBoundary`; basta oferecer os métodos compatíveis. Isso é útil em Python porque permite usar o datasource real em produção e um fake em testes.

`TaskService` implementa os casos de uso. Ao atualizar, ele primeiro procura a entidade pela porta de saída. Se não encontrar, levanta `TaskNotFoundError`. Se os valores já forem iguais, não chama a operação de atualização. Caso contrário, delega a mudança ao datasource.

```python
existing = self._task_source.find(task.id)
if existing is None:
    raise TaskNotFoundError("ID not found")
if existing.description == task.description and existing.priority == task.priority:
    return
self._task_source.update(task)
```

Observe que `TaskService` não sabe que o banco é SQLite. Ele também não conhece o Flask, o formato JSON ou o código HTTP `404`.

## 4. Adaptadores de entrada

`adapters/presenters.py` contém `TaskDto`, que transforma um dicionário JSON em uma entidade de domínio. O presenter é uma fronteira entre dados externos e objetos internos.

```python
TaskDto.from_payload(payload).to_domain()
```

A conversão de atualização recebe o identificador da URL:

```python
TaskDto.from_payload(payload).to_domain(task_id=task_id)
```

`adapters/controllers.py` cria um Blueprint Flask por meio de `create_tasks_blueprint`. A função recebe `TaskIncomeBoundary` como parâmetro. Essa injeção é importante: o controller não instancia `TaskService` e não abre o banco.

A criação percorre estes passos:

1. O Flask recebe `POST /tasks`.
2. `_read_payload` verifica e decodifica JSON.
3. `TaskDto` transforma o dicionário em `Task`.
4. A boundary de entrada chama `TaskService.create`.
5. A entidade criada volta pelo mesmo fluxo em sentido contrário.
6. `task_to_dto` transforma a entidade em JSON.
7. O controller retorna `201` e o cabeçalho `Location`.

O controller traduz exceções internas para HTTP. `TaskValidationError` vira `400`, `TaskNotFoundError` vira `404` e falhas inesperadas viram `500`.

## 5. Adaptadores de saída e Peewee

`frameworks/peewee_models.py` define `TaskModel`, que é uma representação de persistência. Ele não é a entidade de domínio. Essa distinção é importante porque o modelo Peewee contém detalhes de banco, enquanto `Task` contém regras do negócio.

```python
class TaskModel(PeeweeBaseModel):
    id = AutoField()
    description = TextField(null=False)
    priority = IntegerField(null=False)
```

O método `to_domain` converte o registro externo em entidade interna:

```python
def to_domain(self) -> Task:
    return Task(
        id=self.id,
        description=self.description,
        priority=self.priority,
    )
```

`frameworks/peewee_datasource.py` implementa `TaskDatasourceBoundary`. Ele usa `TaskModel.create`, `get_or_none` e `save`, mas esses detalhes ficam restritos ao círculo externo.

A criação é transacional:

```python
with self._database.atomic():
    model = TaskModel.create(
        description=task.description,
        priority=task.priority,
    )
```

`atomic()` confirma a transação se o bloco termina sem erro e faz rollback se uma exceção é levantada. O caso de uso não precisa conhecer esse mecanismo.

## 6. Composition root

O arquivo `app/__init__.py` é o composition root. Ele é o único ponto que conhece a entidade concreta Peewee, o datasource concreto, o serviço e o controller.

A composição é equivalente a:

```python
datasource = PeeweeTaskDatasource(database)
task_income_boundary = TaskService(datasource)
app.register_blueprint(create_tasks_blueprint(task_income_boundary))
```

O fluxo de dependências é montado de fora para dentro:

```text
SqliteDatabase
  -> PeeweeTaskDatasource
  -> TaskService
  -> create_tasks_blueprint
  -> Flask app
```

Isso substitui a descoberta automática de dependências feita pelo Spring. Em Python, essa composição explícita é simples de ler e fácil de substituir nos testes.

## 7. Flask e ciclo de vida do SQLite

A fábrica `create_app` cria uma instância Flask e permite substituir configurações nos testes. O banco padrão usa `sqlite:///tasks.db`.

Na inicialização, `SqliteDatabase` é criado, o modelo é associado com `database.bind` e a tabela é criada com `create_tables`. Antes de cada requisição, a conexão é aberta. Ao final, a conexão é fechada por `teardown_request`.

SQLite é um banco relacional embutido. Ele armazena tabelas, chaves e transações em um arquivo sem precisar de um servidor separado. Essa característica é adequada ao POC e aos testes temporários.

A branch aceita URLs `sqlite:///`. Para um arquivo relativo:

```bash
DATABASE_URL='sqlite:///tasks.db' python run.py
```

Para um caminho absoluto em Linux:

```bash
DATABASE_URL='sqlite:////tmp/py-just-to-code.db' python run.py
```

Em uma aplicação maior, `create_tables` deve ser substituído por migrações versionadas, como Peewee Migrate.

## 8. Testes

`tests/test_tasks.py` verifica o contrato HTTP e a persistência real. Ele confirma `201`, `Location`, validações, atualização, `404` e métodos ainda não implementados.

`tests/test_clean_architecture.py` usa `InMemoryDatasource`. Esse fake satisfaz a boundary de saída sem usar Peewee:

```python
@dataclass
class InMemoryDatasource:
    tasks: dict[int, Task]
```

Os testes demonstram que o caso de uso pode ser validado sem iniciar Flask, sem abrir SQLite e sem conhecer o adaptador de produção. Esse isolamento é uma das principais vantagens da Clean Architecture.

Execute todos os testes com:

```bash
pytest
```

## 9. Comparação com a branch Java

| Java `feat/clean-arch` | Python `feature/clean-architecture` |
|---|---|
| `usecases.domains.Task` | `domain.task.Task` |
| `TaskIncomeBoundary` | `usecases.ports.TaskIncomeBoundary` |
| `TaskDatasourceBoundary` | `usecases.ports.TaskDatasourceBoundary` |
| `usecases.services.TaskService` | `usecases.task_service.TaskService` |
| `applications.presenters.TaskDto` | `adapters.presenters.TaskDto` |
| `applications.datasources.TaskDatasource` | `frameworks.peewee_datasource.PeeweeTaskDatasource` |
| `infrastructures.models.TaskModel` | `frameworks.peewee_models.TaskModel` |
| Controller Spring | `adapters.controllers.create_tasks_blueprint` |

A versão Python preserva a ideia de boundaries e adaptadores, mas usa mecanismos idiomáticos da linguagem: dataclasses imutáveis, `Protocol`, composição explícita e fixtures simples do pytest.

## 10. Limites e próximos passos

A API original ainda não implementa `GET` nem `DELETE`; essa ausência foi preservada para evitar mudar o contrato. Próximos casos de uso podem ser adicionados como novos métodos das boundaries, seguidos de adaptadores HTTP e persistência.

SQLite é adequado ao POC. Para concorrência e disponibilidade maiores, avalie PostgreSQL e implemente outro datasource atrás da mesma `TaskDatasourceBoundary`.

A aplicação não inclui autenticação, autorização ou OpenAPI porque esses recursos não existem na origem. Eles devem ser adicionados como adaptadores e configurações externas, sem colocar detalhes de framework no domínio.

## Referências

[1]: https://flask.palletsprojects.com/en/stable/ "Flask Documentation"
[2]: https://docs.peewee-orm.com/en/latest/peewee/quickstart.html "Peewee Quickstart"
[3]: https://docs.peewee-orm.com/en/latest/peewee/transactions.html "Peewee Transactions"
[4]: https://www.sqlite.org/docs.html "SQLite Documentation"
[5]: https://docs.pytest.org/en/stable/ "pytest Documentation"
