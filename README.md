# py-just_to_code

Port em Python/Flask do projeto [`just_to_code`](https://github.com/rcoelho6/just_to_code), baseado na branch Java `feat/clean-arch`. Esta branch, `feature/clean-architecture`, organiza o POC usando Clean Architecture, Peewee e SQLite.

## Estrutura atual

| Camada | Localização | Responsabilidade |
|---|---|---|
| Domínio e regras | `app/clean_architecture/usecases/domains.py` | Entidade imutável `Task` e invariantes de negócio. |
| Portas | `app/clean_architecture/usecases/ports.py` | `TaskIncomeBoundary` e `TaskDatasourceBoundary`, definidos com `Protocol`. |
| Casos de uso | `app/clean_architecture/usecases/service.py` | `TaskService` e `TaskNotFoundError`. |
| Applications | `app/clean_architecture/applications` | Controller Flask e DTOs de entrada/saída. |
| Infrastructures | `app/clean_architecture/infrastructures` | Modelo Peewee e datasource SQLite. |
| Composição | `app/__init__.py` | Cria o banco, conecta as implementações e registra o Blueprint. |

As dependências apontam para dentro. O controller depende de `TaskIncomeBoundary`, não de `TaskService`. O serviço depende de `TaskDatasourceBoundary`, não de Peewee. O domínio não importa Flask, Peewee ou SQLite.

## Contrato HTTP

| Método | Endpoint | Resultado |
|---|---|---|
| `POST` | `/tasks` ou `/tasks/` | Cria uma tarefa, responde `201` e envia `Location: /tasks/{id}`. |
| `PUT` | `/tasks/{id}` | Atualiza uma tarefa, responde `200`. |
| `GET` | `/tasks` e `/tasks/{id}` | Não implementado na origem (`405`). |
| `DELETE` | `/tasks/{id}` | Não implementado na origem (`405`). |

O corpo usa `description` e `priority`. A descrição não pode ser nula ou vazia, e a prioridade deve ser um inteiro não negativo. Erros usam `{"message": "...", "status": <status HTTP>}`.

## Executar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
python run.py
```

A API fica disponível em `http://localhost:8080`. O banco padrão é `tasks.db`. Para indicar outro arquivo SQLite:

```bash
DATABASE_URL='sqlite:///tmp/tasks.db' python run.py
```

## Testar

```bash
pytest
```

A suíte combina testes de integração HTTP com SQLite temporário e testes unitários do `TaskService` usando um datasource em memória. Também verifica que `TaskService` implementa a porta `TaskIncomeBoundary`.

## Documentação

O manual detalhado está em [tips/manual.md](tips/manual.md). A visão resumida da arquitetura está em [app/clean_architecture/README.md](app/clean_architecture/README.md).

## Equivalência com a branch Java

`Task` corresponde ao domínio Java; `TaskIncomeBoundary` e `TaskDatasourceBoundary` correspondem às boundaries de entrada e saída; `TaskService` corresponde ao serviço de caso de uso; `TaskDto` corresponde ao presenter de entrada; `TaskModel` e `PeeweeTaskDatasource` correspondem ao adaptador de persistência. Flask substitui Spring MVC, e a composição explícita em `create_app` substitui a descoberta de dependências do container Spring.

## Limites do POC

A aplicação preserva o escopo original e não adiciona autenticação, OpenAPI, listagem ou exclusão de tarefas. `create_tables` é suficiente para o POC, mas uma aplicação maior deve usar migrações versionadas. SQLite pode ser substituído por outro banco implementando a mesma `TaskDatasourceBoundary`.
