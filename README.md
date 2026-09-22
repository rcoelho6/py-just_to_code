# py-just_to_code — `features/no-framework`

Versão baseada **exclusivamente na branch `main`** do projeto `just_to_code`. Esta implementação mantém o contrato REST de tarefas, mas não usa Flask, Peewee, Spring, ORM ou qualquer framework de aplicação. O servidor HTTP e o acesso ao banco usam somente a biblioteca padrão do Python.

## Componentes

| Componente | Implementação |
|---|---|
| Servidor HTTP | `http.server.ThreadingHTTPServer` |
| Handler de requisições | `http.server.BaseHTTPRequestHandler` |
| Serialização | `json` |
| Banco | `sqlite3` |
| Entidade | `dataclasses.dataclass` |
| Contrato do repositório | `typing.Protocol` |
| Testes | `unittest`, `urllib` e `tempfile` |

## Estrutura

```text
app/
├── database.py   # SQLite direto com sqlite3 e TaskRepository
├── models.py     # Task e validações
├── routes.py     # BaseHTTPRequestHandler e endpoints
├── services.py   # regras de criação e atualização
└── __init__.py   # composição do servidor
run.py            # entrypoint
```

## Contrato HTTP

| Método | Endpoint | Resultado |
|---|---|---|
| `POST` | `/tasks` ou `/tasks/` | Cria uma tarefa, responde `201` e envia `Location: /tasks/{id}`. |
| `PUT` | `/tasks/{id}` | Atualiza uma tarefa, responde `200`. |
| `GET` | `/tasks` e `/tasks/{id}` | Não implementado na origem (`405`). |
| `DELETE` | `/tasks/{id}` | Não implementado na origem (`405`). |

O JSON utiliza `description` e `priority`. A descrição não pode ser vazia e a prioridade deve ser um inteiro não negativo. Erros seguem `{"message": "...", "status": <status HTTP>}`.

## Executar

Não é necessário instalar dependência externa:

```bash
python3 run.py
```

O servidor escuta em `0.0.0.0:8080`. Para escolher o arquivo do banco:

```bash
DATABASE_PATH=/tmp/tasks.db python3 run.py
```

Também é aceito o formato de compatibilidade `DATABASE_URL=sqlite:///tmp/tasks.db`.

## Testar

```bash
python3 -m unittest discover -s tests -v
```

Os testes cobrem validação da entidade, serviço com repositório em memória e integração HTTP com SQLite temporário.

## O que foi removido

- Flask foi substituído por `http.server`.
- Peewee foi substituído por SQL parametrizado usando `sqlite3`.
- O modelo ORM foi substituído por uma dataclass e uma tabela criada com SQL explícito.
- Pytest foi substituído por `unittest`.
- A composição da aplicação é feita diretamente em `build_server`.

Essa abordagem tem menos conveniências que Flask e Peewee, mas torna explícitos o parsing HTTP, os cabeçalhos, o ciclo de vida do servidor, as transações e as consultas SQL.
