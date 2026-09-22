# Manual de estudo: Hexagonal Architecture com Flask, Peewee e SQLite

Este manual descreve a branch `feature/hexagonal-architecture`. A implementação foi criada a partir de `feature/orm-peewee`, usando como referências as branches `feature/clean-architecture` e `feature/layered-architecture`. O objetivo é mostrar como proteger o núcleo da aplicação contra detalhes externos por meio de portas e adaptadores.

## 1. O que é arquitetura hexagonal

Na arquitetura hexagonal, o núcleo da aplicação fica no centro e se comunica com o exterior através de portas. Adaptadores traduzem protocolos externos para essas portas. O desenho não depende de a aplicação ter literalmente seis lados; o hexágono representa a possibilidade de conectar diferentes tecnologias ao mesmo núcleo.

Há dois tipos principais de porta:

- **Driving port**, ou porta de entrada: expõe casos de uso para algo que dirige a aplicação, como HTTP, CLI ou mensagens.
- **Driven port**, ou porta de saída: descreve algo que o núcleo precisa que o ambiente externo faça, como persistir dados ou publicar eventos.

Nesta branch:

| Elemento | Caminho | Papel |
|---|---|---|
| Domínio | `app/hexagonal/domain/entities.py` | Regras e entidade `Task`. |
| Porta de entrada | `app/hexagonal/ports/inbound.py` | `TaskUseCasePort`. |
| Porta de saída | `app/hexagonal/ports/outbound.py` | `TaskRepositoryPort`. |
| Aplicação | `app/hexagonal/application/services.py` | `TaskService`. |
| Adaptador inbound | `app/hexagonal/adapters/inbound/http.py` | Flask e JSON. |
| Adaptador outbound | `app/hexagonal/adapters/outbound/peewee.py` | Peewee e SQLite. |
| Composição | `app/__init__.py` | Liga portas e adaptadores. |

O fluxo completo de uma criação é:

```text
Cliente HTTP
  -> adapters/inbound/http.py
  -> ports/inbound.py: TaskUseCasePort
  -> application/services.py: TaskService
  -> ports/outbound.py: TaskRepositoryPort
  -> adapters/outbound/peewee.py
  -> Peewee/SQLite
```

A seta representa uma chamada em tempo de execução. A dependência de código aponta para o núcleo: o adaptador HTTP depende da porta de entrada, e o adaptador Peewee implementa a porta de saída. O núcleo não importa Flask ou Peewee.

## 2. Domínio

`domain/entities.py` contém a entidade pura:

```python
@dataclass(frozen=True, slots=True)
class Task:
    description: str
    priority: int
    id: int | None = None
```

A entidade usa `frozen=True` para evitar mutações acidentais e `slots=True` para manter uma estrutura compacta. `__post_init__` valida as invariantes: um identificador existente deve ser positivo, a descrição deve conter texto e a prioridade deve ser um inteiro não negativo.

`TaskValidationError` também pertence ao domínio. Ele não sabe que uma requisição HTTP deve retornar `400`; essa tradução é responsabilidade do adaptador Flask.

```python
if not isinstance(self.description, str) or not self.description.strip():
    raise TaskValidationError("Description cannot be null or blank")
```

Esse isolamento permite executar testes do domínio sem inicializar Flask, conectar SQLite ou instalar um ORM.

## 3. Porta de entrada

`ports/inbound.py` define o contrato usado pelos adaptadores que dirigem o núcleo:

```python
@runtime_checkable
class TaskUseCasePort(Protocol):
    def create(self, task: Task) -> Task:
        ...

    def update(self, task: Task) -> None:
        ...
```

`Protocol` fornece tipagem estrutural. O adaptador não precisa conhecer a classe concreta `TaskService`; precisa apenas de um objeto com `create` e `update`. `runtime_checkable` permite verificar essa relação em teste:

```python
assert isinstance(service, TaskUseCasePort)
```

Essa porta é o lado de entrada do hexágono. Uma futura CLI, consumer de fila ou outro framework web pode ser criado sem modificar o serviço.

## 4. Porta de saída

`ports/outbound.py` define o contrato que o serviço precisa para persistir tarefas:

```python
class TaskRepositoryPort(Protocol):
    def create(self, task: Task) -> Task:
        ...

    def find(self, task_id: int) -> Task | None:
        ...

    def update(self, task: Task) -> Task:
        ...
```

Essa é uma porta driven. O núcleo chama seus métodos, mas não decide se a implementação usará SQLite, PostgreSQL, uma API remota ou um dicionário em memória.

A porta de saída recebe e retorna a entidade de domínio. Isso evita que um modelo Peewee atravesse a fronteira do hexágono.

## 5. Serviço da aplicação

`application/services.py` contém `TaskService`, que implementa a porta de entrada e recebe a porta de saída no construtor:

```python
class TaskService(TaskUseCasePort):
    def __init__(self, repository: TaskRepositoryPort):
        self._repository = repository
```

Na criação, o serviço delega a persistência ao repository port. Na atualização, procura a tarefa pelo ID. Se não encontrar, levanta `TaskNotFoundError`. Se os valores não mudaram, encerra sem executar uma gravação; caso contrário, chama `update`.

```python
existing = self._repository.find(task.id)
if existing is None:
    raise TaskNotFoundError("ID not found")
if existing.description == task.description and existing.priority == task.priority:
    return
self._repository.update(task)
```

O serviço não importa Flask, `request`, `jsonify`, Peewee ou `SqliteDatabase`. Esse é o centro da diferença em relação a uma implementação acoplada ao framework.

## 6. Adaptador inbound HTTP

`adapters/inbound/http.py` implementa o lado HTTP. `create_tasks_blueprint` recebe `TaskUseCasePort`:

```python
def create_tasks_blueprint(task_use_case: TaskUseCasePort) -> Blueprint:
    ...
```

O adaptador lê JSON, constrói `Task`, chama a porta e converte a resposta para JSON. Ele também traduz exceções para códigos HTTP. O adaptador conhece Flask e o formato da API, mas não cria o repository nem conhece a tabela do banco.

A rota de criação aceita `POST /tasks` e `POST /tasks/`, retorna `201` e inclui `Location: /tasks/{id}`. A rota de atualização aceita `PUT /tasks/{id}` e retorna `200`. `GET` e `DELETE` permanecem indisponíveis porque não faziam parte do contrato original.

A função `_task_from_payload` é uma pequena tradução de entrada. A entidade valida os dados depois que o payload é convertido; assim, a regra não fica duplicada no controller.

## 7. Adaptador outbound Peewee

`adapters/outbound/peewee.py` contém três responsabilidades externas: o modelo `TaskRecord`, a conversão para domínio e `PeeweeTaskRepository`.

`TaskRecord` representa a tabela:

```python
class TaskRecord(PeeweeBaseModel):
    id = AutoField()
    description = TextField(null=False)
    priority = IntegerField(null=False)
```

O método `to_domain` impede que o objeto Peewee escape para o núcleo. O repository usa `TaskRecord.create`, `get_or_none` e `save`, mas expõe apenas a interface `TaskRepositoryPort`.

A persistência ocorre em transações:

```python
with self._database.atomic():
    record = TaskRecord.create(
        description=task.description,
        priority=task.priority,
    )
```

Se o bloco falhar, o Peewee faz rollback. Esse detalhe pertence ao adaptador outbound, não ao serviço.

## 8. Composition root

`app/__init__.py` é o ponto de composição. Ele cria o Flask e o SQLite, associa `TaskRecord` ao banco e monta o grafo de dependências:

```python
repository = PeeweeTaskRepository(database)
task_use_case = TaskService(repository)
app.register_blueprint(create_tasks_blueprint(task_use_case))
```

Esse é o único lugar que conhece simultaneamente Flask, `TaskService`, `PeeweeTaskRepository` e `TaskRecord`. A composição é explícita, substituindo a descoberta automática de dependências do Spring.

Durante uma requisição, `before_request` abre a conexão quando necessário e `teardown_request` fecha a conexão. O arquivo padrão é `tasks.db`; `DATABASE_URL` permite selecionar outro arquivo SQLite.

## 9. Testes

`tests/test_hexagonal.py` testa o domínio e o serviço com `InMemoryRepository`. Esse repositório implementa a porta de saída sem Peewee. Os testes demonstram que:

1. O domínio pode ser usado isoladamente.
2. O serviço implementa a porta de entrada.
3. O serviço cria e atualiza por meio da porta de saída.
4. Uma tarefa inexistente produz `TaskNotFoundError`.

`tests/test_tasks.py` testa os dois adaptadores juntos: o Flask real chama o serviço e o repository Peewee persiste em um SQLite temporário. Assim, existe uma camada de testes unitários do núcleo e outra de integração dos adaptadores.

Execute tudo com:

```bash
pytest
```

## 10. Relação com Clean e Layered Architecture

A Clean Architecture forneceu a separação entre domínio, casos de uso, boundaries e infraestrutura. A Layered Architecture forneceu a referência para dividir controller, serviço, repository, modelo e testes.

A arquitetura hexagonal acrescenta uma distinção explícita entre direção das portas:

| Referência | Tradução hexagonal |
|---|---|
| Boundary de entrada | `TaskUseCasePort`, driving port |
| Boundary de persistência | `TaskRepositoryPort`, driven port |
| Serviço de aplicação | `TaskService`, núcleo de casos de uso |
| Controller Flask | Adaptador inbound |
| Repository Peewee | Adaptador outbound |
| Composition root | `create_app` |

O resultado evita que a estrutura de camadas seja confundida com a direção das dependências. Mais de um adaptador pode usar a mesma porta de entrada, e mais de uma tecnologia pode implementar a mesma porta de saída.

## 11. Evolução

Para adicionar uma CLI, crie um adaptador inbound que receba `TaskUseCasePort`. Para trocar SQLite, crie um adaptador outbound que implemente `TaskRepositoryPort` e altere somente `create_app`. Para publicar eventos, adicione outra porta de saída e outro adaptador, mantendo o serviço livre da biblioteca do broker.

O POC não inclui autenticação, OpenAPI, migrações versionadas, `GET` ou `DELETE`. Esses recursos podem ser adicionados como novos adaptadores ou casos de uso sem colocar dependências externas dentro do domínio.
