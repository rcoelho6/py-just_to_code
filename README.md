# py-just_to_code

Port em Python/Flask do projeto [`just_to_code`](https://github.com/rcoelho6/just_to_code), baseado na branch Java `feat/clean-arch` nesta branch `feature/clean-architecture`.

## Clean Architecture

A implementação segue a direção de dependências da Clean Architecture:

| Camada | Localização | Responsabilidade |
|---|---|---|
| Domínio | `app/clean_architecture/domain` | Entidade `Task` e invariantes, sem frameworks. |
| Casos de uso | `app/clean_architecture/usecases` | Boundaries e `TaskService`, sem Flask ou Peewee. |
| Adaptadores | `app/clean_architecture/adapters` | Controller HTTP e presenters JSON. |
| Frameworks | `app/clean_architecture/frameworks` | Peewee, SQLite e modelo persistente. |
| Composição | `app/__init__.py` | Conecta as implementações concretas. |

O domínio não conhece detalhes externos. As portas `TaskIncomeBoundary` e `TaskDatasourceBoundary` ficam centralizadas em `app/clean_architecture/usecases/ports.py`. O `TaskService` implementa a porta de entrada e o datasource Peewee implementa a porta de saída. `TaskIncomeBoundary` é `runtime_checkable`, permitindo validar o contrato em testes. O controller recebe a porta por injeção, em vez de criar diretamente o serviço ou o banco.

## Contrato preservado

| Método | Endpoint | Resultado |
|---|---|---|
| `POST` | `/tasks` ou `/tasks/` | Cria uma tarefa, responde `201` e envia `Location: /tasks/{id}` |
| `PUT` | `/tasks/{id}` | Atualiza uma tarefa, responde `200` |
| `GET` | `/tasks` e `/tasks/{id}` | Ainda não implementado na origem (`405`) |
| `DELETE` | `/tasks/{id}` | Ainda não implementado na origem (`405`) |

`description` não pode ser nula ou vazia, e `priority` deve ser um inteiro não negativo. Erros usam o formato `{"message": "...", "status": <http status>}`.

## Executar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
python run.py
```

A API fica disponível em `http://localhost:8080`. O banco padrão é o arquivo SQLite `tasks.db`. Para executar com outro arquivo:

```bash
DATABASE_URL='sqlite:///tmp/tasks.db' python run.py
```

## Testar

```bash
pytest
```

A suíte contém testes de integração HTTP e testes unitários do caso de uso com um datasource em memória. Dessa forma, a regra da aplicação é testada sem Flask, Peewee ou SQLite.

## Documentação

O manual [tips/manual.md](tips/manual.md) explica a Clean Architecture, o fluxo de dependências, Flask, Peewee, SQLite, boundaries, adaptadores e testes. A estrutura também está resumida em [app/clean_architecture/README.md](app/clean_architecture/README.md).

## Alternativas ao Java

Spring MVC foi substituído por Flask. `TaskIncomeBoundary` e `TaskDatasourceBoundary` substituem as interfaces de entrada e saída da aplicação Java. `TaskModel` e `PeeweeTaskDatasource` substituem a entidade JPA e o datasource adaptador. A composição explícita no `create_app` substitui a configuração automática do container Spring.

## Licença

O projeto de origem declara licença MIT. Este port preserva a mesma intenção; consulte o repositório de origem para o texto legal completo.
