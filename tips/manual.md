# Manual: endpoints e SQLite sem frameworks

Esta branch, `features/no-framework`, foi criada diretamente a partir de `main`. A regra principal é não usar framework web, ORM ou framework de testes. O código utiliza módulos que já fazem parte da biblioteca padrão do Python.

## 1. Mapa do código

| Arquivo | Responsabilidade |
|---|---|
| `app/models.py` | Dataclass `Task` e validações de domínio. |
| `app/services.py` | Casos de uso e protocolo do repositório. |
| `app/database.py` | Conexão, schema e consultas com `sqlite3`. |
| `app/routes.py` | Servidor HTTP, parsing JSON e respostas. |
| `app/__init__.py` | Composition root. |
| `run.py` | Inicialização do servidor. |

O fluxo de uma criação é:

```text
HTTP request -> TaskRequestHandler -> TaskService -> TaskRepository -> sqlite3 -> SQLite
```

O controller não é Flask: é uma classe derivada de `BaseHTTPRequestHandler`. O repository não é Peewee: são comandos SQL executados pela API `sqlite3`.

## 2. Entidade `Task`

`app/models.py` define uma dataclass imutável:

```python
@dataclass(frozen=True, slots=True)
class Task:
    description: str
    priority: int
    id: int | None = None
```

`__post_init__` rejeita descrição ausente ou em branco, prioridade negativa ou não inteira e identificador inválido. `TaskValidationError` é uma exceção comum do Python, sem dependência de biblioteca externa.

A validação fica na entidade para que chamadas HTTP e testes diretos tenham o mesmo comportamento.

## 3. Serviço e protocolo

`app/services.py` contém `TaskService`. Ele recebe um objeto que cumpre `TaskRepositoryPort`:

```python
class TaskRepositoryPort(Protocol):
    def create(self, task: Task) -> Task: ...
    def find(self, task_id: int) -> Task | None: ...
    def update(self, task: Task) -> Task: ...
```

`Protocol` é parte de `typing`; não cria container de dependências. Ele apenas documenta o contrato estrutural. O serviço não sabe se o repositório usa SQLite, memória ou outro mecanismo.

Ao atualizar, o serviço procura a tarefa, retorna erro se ela não existir e evita gravar quando descrição e prioridade permanecem iguais.

## 4. SQLite sem ORM

`app/database.py` usa `sqlite3.connect` para abrir uma conexão por operação. O contexto `with connection:` confirma a transação quando o bloco termina normalmente e faz rollback em caso de exceção.

A tabela é criada com SQL explícito:

```sql
CREATE TABLE IF NOT EXISTS task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    priority INTEGER NOT NULL
)
```

A criação usa parâmetros:

```python
connection.execute(
    "INSERT INTO task (description, priority) VALUES (?, ?)",
    (task.description, task.priority),
)
```

Os `?` são importantes: valores não são concatenados na string SQL, evitando injeção de SQL. O `row_factory = sqlite3.Row` permite ler colunas por nome. O método `_to_task` converte a linha do banco novamente para a entidade `Task`.

A conexão por operação torna o exemplo simples e seguro para o servidor com múltiplas threads. Uma aplicação maior pode usar pool de conexões, mas isso seria uma decisão de infraestrutura adicional.

## 5. Servidor HTTP da biblioteca padrão

`app/routes.py` usa:

```python
class TaskRequestHandler(BaseHTTPRequestHandler):
```

A classe trata os métodos `do_POST`, `do_PUT`, `do_GET` e `do_DELETE`. `ThreadingHTTPServer` cria uma thread por requisição, e o repositório abre conexões SQLite independentes.

Para ler o corpo, o handler consulta `Content-Length` e lê exatamente essa quantidade de bytes de `rfile`. Depois usa `json.loads`. O código verifica se o resultado é um objeto JSON antes de acessar `description` e `priority`.

Para escrever uma resposta, `_json` faz manualmente o trabalho que um framework normalmente faria:

1. serializa o dicionário com `json.dumps`;
2. converte o texto para bytes;
3. chama `send_response`;
4. define `Content-Type` e `Content-Length`;
5. adiciona `Location` quando necessário;
6. finaliza os cabeçalhos com `end_headers`;
7. escreve os bytes em `wfile`.

A resposta de criação é `201`; a de atualização é `200`; validação produz `400`; tarefa inexistente produz `404`; métodos não implementados produzem `405`.

## 6. Composition root

`app/__init__.py` tem `build_server`. Ele lê `DATABASE_PATH` ou o formato compatível `DATABASE_URL=sqlite:///...`, instancia `TaskRepository`, injeta-o em `TaskService` e injeta o serviço no handler por meio do atributo `task_service` do servidor.

```python
repository = TaskRepository(database_path)
return create_server(host, port, TaskService(repository))
```

`run.py` chama `serve_forever()` e fecha o servidor no bloco `finally`. `KeyboardInterrupt` permite encerrar com Ctrl+C.

## 7. Testes sem pytest

`tests/test_no_framework.py` usa apenas `unittest`, `tempfile`, `threading` e `urllib.request`.

- O teste de domínio valida a regra de descrição.
- O teste de serviço usa `InMemoryRepository` e não cria arquivo SQLite.
- O teste de integração inicia o servidor em uma porta livre (`0`), envia requisições HTTP reais e usa um banco temporário.
- `server.shutdown()` encerra o loop e `server.server_close()` libera o socket.

Execute com:

```bash
python3 -m unittest discover -s tests -v
```

## 8. Comparação com a implementação da main

A branch mantém o contrato funcional da main, mas troca as ferramentas:

| Main | `features/no-framework` |
|---|---|
| Flask | `http.server` |
| Blueprint e `request` | `BaseHTTPRequestHandler` |
| Peewee | `sqlite3` e SQL explícito |
| Modelo ORM | Dataclass `Task` |
| `pytest` | `unittest` |
| Factory Flask | `build_server` |

A ausência de framework exige tratar manualmente cabeçalhos, JSON, métodos HTTP, conexões e SQL. Essa é a finalidade didática da branch: mostrar o que Flask e Peewee automatizam.

## 9. Limitações

`http.server` é adequado para demonstração e desenvolvimento simples, mas não oferece automaticamente middleware, autenticação, roteamento avançado, observabilidade ou produção endurecida. SQLite também tem limitações de concorrência e escala. Para um sistema real, frameworks e ferramentas especializadas podem ser preferíveis; esta branch não os utiliza justamente para tornar o funcionamento interno explícito.
