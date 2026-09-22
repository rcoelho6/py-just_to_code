# Organização da aplicação

A branch `feature/layered-architecture` divide o código por responsabilidade:

- `domain`: entidades e regras que não conhecem Flask, Peewee ou SQLite.
- `application`: casos de uso e portas (interfaces) esperadas pela aplicação.
- `infrastructure`: implementação concreta da persistência com Peewee.
- `application`: adaptação entre HTTP/JSON e os casos de uso.
- `app/__init__.py`: composition root; conecta as implementações e cria a aplicação.

A dependência aponta para dentro: a camada HTTP depende da aplicação, a aplicação depende do domínio e de uma porta abstrata, e a infraestrutura implementa essa porta. O domínio não importa nenhuma biblioteca web ou de banco.
