# Hexagonal Architecture

A aplicação organiza o núcleo e os adaptadores em torno de portas. A direção das dependências aponta para o núcleo:

| Elemento | Caminho | Papel |
|---|---|---|
| Domínio | `domain/entities.py` | Entidade `Task` e validações. |
| Porta de entrada | `ports/inbound.py` | `TaskUseCasePort`, contrato dos casos de uso. |
| Porta de saída | `ports/outbound.py` | `TaskRepositoryPort`, contrato que o armazenamento deve cumprir. |
| Aplicação | `application/services.py` | `TaskService`, implementação dos casos de uso. |
| Adaptador inbound | `adapters/inbound/http.py` | Traduz HTTP/JSON para chamadas da porta de entrada. |
| Adaptador outbound | `adapters/outbound/peewee.py` | Traduz a porta de saída para Peewee/SQLite. |

A porta de entrada é chamada de **driving port**: algo externo dirige o núcleo por ela. A porta de saída é chamada de **driven port**: o núcleo a utiliza, e uma tecnologia externa a implementa. O serviço não conhece Flask; o domínio e o serviço não conhecem Peewee.

`app/__init__.py` é o composition root. Ele cria o banco, instancia `PeeweeTaskRepository`, injeta-o em `TaskService` e entrega o serviço ao adaptador Flask. Para trocar HTTP por CLI ou SQLite por PostgreSQL, basta criar outro adaptador compatível com a porta correspondente.
