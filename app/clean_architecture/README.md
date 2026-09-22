# Clean Architecture

A implementação atual separa regras de negócio, contratos, casos de uso, adaptadores de entrada e infraestrutura. Os nomes dos diretórios seguem a organização da branch:

| Área | Caminho | Responsabilidade |
|---|---|---|
| Domínios | `usecases/domains.py` | Entidade `Task` e validações invariantes. |
| Portas | `usecases/ports.py` | Contratos `TaskIncomeBoundary` e `TaskDatasourceBoundary`. |
| Serviço | `usecases/service.py` | Caso de uso de criação e atualização. |
| Applications | `applications/controllers.py` | Controller Flask e rotas HTTP. |
| DTOs | `applications/dtos.py` | Conversão entre JSON e entidade de domínio. |
| Infrastructures | `infrastructures/peewee_models.py` | Modelo Peewee da tabela `task`. |
| Datasource | `infrastructures/peewee_datasource.py` | Implementação SQLite da porta de persistência. |
| Composição | `app/__init__.py` | Composition root da aplicação Flask. |

O fluxo de dependências aponta para dentro. O controller recebe `TaskIncomeBoundary`; o `TaskService` implementa essa porta e recebe `TaskDatasourceBoundary`; o `PeeweeTaskDatasource` implementa a porta de persistência. O domínio não conhece Flask, Peewee ou SQLite.

`TaskIncomeBoundary` é um `Protocol` marcado como `runtime_checkable`, permitindo que os testes confirmem que o serviço oferece o contrato esperado. Essa verificação não transforma o protocolo em um container de dependências: a composição continua explícita em `create_app`.

A aplicação preserva o contrato HTTP do POC Java: `POST /tasks` cria uma tarefa e `PUT /tasks/{id}` atualiza uma tarefa. As operações `GET` e `DELETE` continuam fora do escopo original.
