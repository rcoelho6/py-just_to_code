# py-just_to_code

Port em Python/Flask do projeto [`just_to_code`](https://github.com/rcoelho6/just_to_code), com uma implementação de **Hexagonal Architecture** na branch `feature/hexagonal-architecture`. Esta branch foi criada a partir de `feature/orm-peewee` e utiliza as branches `feature/clean-architecture` e `feature/layered-architecture` como referências de separação de responsabilidades, boundaries, Peewee e testes.

## Arquitetura hexagonal

O núcleo da aplicação fica protegido por portas. Adaptadores externos dependem das portas, e não o contrário.

| Elemento | Localização | Responsabilidade |
|---|---|---|
| Domínio | `app/hexagonal/domain/entities.py` | Entidade `Task` e invariantes de negócio. |
| Porta de entrada | `app/hexagonal/ports/inbound.py` | `TaskUseCasePort`, usada por HTTP ou outros drivers. |
| Porta de saída | `app/hexagonal/ports/outbound.py` | `TaskRepositoryPort`, usada para persistência. |
| Aplicação | `app/hexagonal/application/services.py` | `TaskService` e regras dos casos de uso. |
| Adaptador de entrada | `app/hexagonal/adapters/inbound/http.py` | Flask, JSON e códigos HTTP. |
| Adaptador de saída | `app/hexagonal/adapters/outbound/peewee.py` | Peewee, SQLite e mapeamento de registros. |
| Composição | `app/__init__.py` | Conecta portas aos adaptadores concretos. |

O fluxo de entrada é:

```text
HTTP/JSON -> TaskUseCasePort -> TaskService -> TaskRepositoryPort -> Peewee/SQLite
```

O núcleo não importa Flask, Peewee ou SQLite. `TaskUseCasePort` é `runtime_checkable`, e os testes confirmam que o serviço implementa a porta de entrada.

## Contrato preservado

| Método | Endpoint | Resultado |
|---|---|---|
| `POST` | `/tasks` ou `/tasks/` | Cria uma tarefa, responde `201` e envia `Location: /tasks/{id}`. |
| `PUT` | `/tasks/{id}` | Atualiza uma tarefa, responde `200`. |
| `GET` | `/tasks` e `/tasks/{id}` | Não implementado na origem (`405`). |
| `DELETE` | `/tasks/{id}` | Não implementado na origem (`405`). |

`description` não pode ser nula ou vazia, e `priority` deve ser um inteiro não negativo. Erros usam `{"message": "...", "status": <status HTTP>}`.

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

Os testes unitários exercitam o domínio e o serviço com um repositório em memória. Os testes de integração exercitam o adaptador Flask e o adaptador Peewee com SQLite temporário.

## Documentação

O manual detalhado está em [tips/manual.md](tips/manual.md). A estrutura resumida está em [app/hexagonal/README.md](app/hexagonal/README.md).

## Relação com as outras branches

A branch `feature/clean-architecture` orientou a separação entre domínio, casos de uso, boundaries e infraestrutura. A branch `feature/layered-architecture` orientou a organização de serviços, repositórios, controller e testes. Nesta versão, esses conceitos são expressos explicitamente como **driving port** (`TaskUseCasePort`), **driven port** (`TaskRepositoryPort`), adaptadores e um núcleo hexagonal.

## Limites do POC

A API mantém o escopo original e não adiciona autenticação, OpenAPI, listagem ou exclusão de tarefas. `create_tables` é suficiente para o POC; uma aplicação maior deve usar migrações versionadas. Um banco diferente pode ser usado criando outro adaptador que implemente `TaskRepositoryPort`.
