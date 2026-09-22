# Clean Architecture

A implementação segue a direção de dependências da Clean Architecture:

- `domain`: entidade `Task` e invariantes de negócio. Não importa Flask, Peewee ou SQLite.
- `usecases`: boundaries de entrada/saída e `TaskService`. Define o que a aplicação faz, mas não como o banco funciona.
- `adapters`: presenters e controller Flask. Converte JSON para entidades e entidades para respostas.
- `frameworks`: detalhes externos. O `TaskModel` e `PeeweeTaskDatasource` implementam a persistência SQLite.
- `app/__init__.py`: composition root. É o único lugar que conhece todas as implementações e faz a composição.

O fluxo de dependência aponta para dentro. O controller depende de `TaskIncomeBoundary`, um `Protocol` de entrada, e o caso de uso depende de `TaskDatasourceBoundary`, um `Protocol` de saída. Ambos ficam em `usecases/ports.py`; o `TaskService` implementa a porta de entrada e o datasource Peewee implementa a porta de saída. `TaskIncomeBoundary` é `runtime_checkable`, permitindo verificar em testes que o serviço está conectado ao contrato correto. Isso permite testar o caso de uso com um fake em memória e trocar SQLite por outro armazenamento sem alterar o domínio.
