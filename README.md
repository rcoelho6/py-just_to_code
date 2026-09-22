# py-just_to_code

Port em Python/Flask do projeto [`just_to_code`](https://github.com/rcoelho6/just_to_code), baseado na branch `main`.

## Escopo preservado

A branch de origem é um POC de API REST com o módulo de tarefas. O contrato disponível foi mantido:

| Método | Endpoint | Resultado |
|---|---|---|
| `POST` | `/tasks` ou `/tasks/` | Cria uma tarefa, responde `201` e envia `Location: /tasks/{id}` |
| `PUT` | `/tasks/{id}` | Atualiza uma tarefa, responde `200` |
| `GET` | `/tasks` e `/tasks/{id}` | Ainda não implementado na origem (`405`) |
| `DELETE` | `/tasks/{id}` | Ainda não implementado na origem (`405`) |

O corpo de entrada e saída usa somente `description` e `priority`. `description` não pode ser nula/branca e `priority` deve ser um inteiro não negativo. Erros retornam `{"message": "...", "status": <http status>}`.

## Alternativas Flask

- **Spring Boot MVC** foi substituído por **Flask Blueprints**, mantendo as rotas REST e os códigos HTTP.
- **Spring Data JPA/H2** foi substituído por **SQLAlchemy 2 + SQLite**. SQLite é a alternativa leve e embutida para o POC; em produção, basta apontar `DATABASE_URL` para PostgreSQL ou outro banco suportado pelo SQLAlchemy.
- **Injeção de dependências Spring** foi reduzida a uma fábrica de aplicação Flask e uma `TaskService` explícita, o que mantém as camadas controller/service/model sem adicionar um container de DI para este POC.
- A **H2 Console** não possui equivalente nativo no Flask. Para inspeção local, use uma ferramenta SQLite ou conecte o arquivo `tasks.db`; não foi adicionada uma rota administrativa para não ampliar a superfície da API.
- Swagger/OpenAPI não existia na origem; portanto não foi inventado no port.

## Executar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
python run.py
```

A API fica disponível em `http://localhost:8080`.

Para usar outro banco:

```bash
DATABASE_URL='sqlite:///tasks.db' python run.py
# Exemplo para PostgreSQL: DATABASE_URL='postgresql+psycopg://user:password@host/db' python run.py
```

## Testar

```bash
pytest
```

## Licença

O projeto de origem declara licença MIT. Este port preserva a mesma intenção; consulte o repositório de origem para o texto legal completo.
