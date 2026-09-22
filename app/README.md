# Organização da aplicação

A branch `feature/layered-architecture` divide o código por responsabilidade:

- `usecases/domain`: entidades e regras que não conhecem Flask, Peewee ou SQLite.
- `usecases/ports`: porta de persistência `TaskRepository`.
- `application/ports.py`: porta de entrada `TaskIncomeBoundary`, usada pelo controller e implementada pelo serviço.
- `usecases/services`: casos de uso e implementação concreta do serviço.
- `infrastructure`: implementação concreta da persistência com Peewee.
- `application/http`: adaptação entre HTTP/JSON e a porta de entrada.
- `app/__init__.py`: composition root; conecta as implementações e cria a aplicação.

A dependência aponta para dentro: o controller depende de `TaskIncomeBoundary`, não de `TaskService`; o serviço depende de `TaskRepository`; e a infraestrutura implementa esse repositório. O domínio não importa nenhuma biblioteca web ou de banco.
