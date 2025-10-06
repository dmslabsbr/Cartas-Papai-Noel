# Documentação da API - Noel

Esta documentação descreve as APIs disponíveis no sistema Noel.

## Autenticação

Todas as rotas da API (exceto as rotas de autenticação) requerem autenticação. A autenticação pode ser feita de duas maneiras:

1. **Sessão Web**: Para aplicações web, a autenticação é gerenciada por sessões.
2. **API Token**: Para clientes API, a autenticação é feita via token JWT.

### Endpoints de Autenticação

#### Login

```
POST /api/auth/login
```

**Parâmetros do corpo da requisição:**

| Nome     | Tipo   | Descrição                |
|----------|--------|--------------------------|
| username | string | Email do usuário         |
| password | string | Senha do usuário         |

**Resposta de sucesso (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "email": "usuario@example.com",
    "display_name": "Nome do Usuário",
    "roles": [
      {
        "id": 1,
        "code": "USER",
        "description": "Usuário comum"
      }
    ]
  }
}
```

**Resposta de erro (401 Unauthorized):**

```json
{
  "detail": "Credenciais inválidas"
}
```

#### Obter Usuário Atual

```
GET /api/auth/me
```

**Cabeçalhos:**

| Nome           | Valor                      |
|----------------|----------------------------|
| Authorization  | Bearer {access_token}      |

**Resposta de sucesso (200 OK):**

```json
{
  "email": "usuario@example.com",
  "display_name": "Nome do Usuário",
  "roles": [
    {
      "id": 1,
      "code": "USER",
      "description": "Usuário comum"
    }
  ]
}
```

**Resposta de erro (401 Unauthorized):**

```json
{
  "detail": "Não autenticado"
}
```

## Cartinhas

### Listar Cartinhas

```
GET /cartas/api
```

**Parâmetros de consulta:**

| Nome   | Tipo   | Descrição                                                   |
|--------|--------|-------------------------------------------------------------|
| status | string | Filtrar por status: "disponivel", "adotadas" ou "minhas"    |
| skip   | int    | Número de registros para pular (paginação)                  |
| limit  | int    | Número máximo de registros a retornar (paginação)           |

**Resposta de sucesso (200 OK):**

```json
[
  {
    "id": 1,
    "id_carta": 101,
    "nome": "Nome da Criança",
    "sexo": "M",
    "presente": "Brinquedo desejado",
    "status": "disponível",
    "observacao": "Observação opcional",
    "adotante_email": null,
    "del_bl": false,
    "del_time": null,
    "created_at": "2023-01-01T10:00:00",
    "updated_at": "2023-01-01T10:00:00"
  }
]
```

### Obter Detalhes de uma Cartinha

```
GET /cartas/api/{id_carta}
```

**Parâmetros de caminho:**

| Nome     | Tipo | Descrição           |
|----------|------|--------------------|
| id_carta | int  | ID da cartinha     |

**Resposta de sucesso (200 OK):**

```json
{
  "id": 1,
  "id_carta": 101,
  "nome": "Nome da Criança",
  "sexo": "M",
  "presente": "Brinquedo desejado",
  "status": "disponível",
  "observacao": "Observação opcional",
  "adotante_email": null,
  "del_bl": false,
  "del_time": null,
  "created_at": "2023-01-01T10:00:00",
  "updated_at": "2023-01-01T10:00:00"
}
```

**Resposta de erro (404 Not Found):**

```json
{
  "detail": "Cartinha não encontrada"
}
```

### Adotar uma Cartinha

```
POST /cartas/api/adopt
```

**Parâmetros do corpo da requisição:**

| Nome     | Tipo | Descrição           |
|----------|------|--------------------|
| id_carta | int  | ID da cartinha     |

**Resposta de sucesso (200 OK):**

```json
{
  "id": 1,
  "id_carta": 101,
  "nome": "Nome da Criança",
  "sexo": "M",
  "presente": "Brinquedo desejado",
  "status": "adotada",
  "observacao": "Observação opcional",
  "adotante_email": "usuario@example.com",
  "del_bl": false,
  "del_time": null,
  "created_at": "2023-01-01T10:00:00",
  "updated_at": "2023-01-01T10:00:00"
}
```

**Resposta de erro (400 Bad Request):**

```json
{
  "detail": "Não foi possível adotar a cartinha"
}
```

### Cancelar Adoção de uma Cartinha

```
POST /cartas/api/cancel/{id_carta}
```

**Parâmetros de caminho:**

| Nome     | Tipo | Descrição           |
|----------|------|--------------------|
| id_carta | int  | ID da cartinha     |

**Resposta de sucesso (200 OK):**

```json
{
  "id": 1,
  "id_carta": 101,
  "nome": "Nome da Criança",
  "sexo": "M",
  "presente": "Brinquedo desejado",
  "status": "disponível",
  "observacao": "Observação opcional",
  "adotante_email": null,
  "del_bl": false,
  "del_time": null,
  "created_at": "2023-01-01T10:00:00",
  "updated_at": "2023-01-01T10:00:00"
}
```

**Resposta de erro (400 Bad Request):**

```json
{
  "detail": "Não foi possível cancelar a adoção"
}
```

## Rotas Administrativas

As rotas a seguir requerem permissão de administrador (role "ADMIN").

### Criar uma Nova Cartinha

```
POST /cartas/api/admin/create
```

**Parâmetros do corpo da requisição:**

| Nome      | Tipo   | Descrição                                  |
|-----------|--------|-------------------------------------------|
| id_carta  | int    | ID único da cartinha                      |
| nome      | string | Nome da criança                           |
| sexo      | string | Sexo da criança ("M" ou "F")              |
| presente  | string | Presente desejado                         |
| status    | string | Status inicial (padrão: "disponível")     |
| observacao| string | Observação opcional                       |

**Resposta de sucesso (200 OK):**

```json
{
  "id": 1,
  "id_carta": 101,
  "nome": "Nome da Criança",
  "sexo": "M",
  "presente": "Brinquedo desejado",
  "status": "disponível",
  "observacao": "Observação opcional",
  "adotante_email": null,
  "del_bl": false,
  "del_time": null,
  "created_at": "2023-01-01T10:00:00",
  "updated_at": "2023-01-01T10:00:00"
}
```

### Atualizar uma Cartinha

```
PUT /cartas/api/admin/{id_carta}
```

**Parâmetros de caminho:**

| Nome     | Tipo | Descrição           |
|----------|------|--------------------|
| id_carta | int  | ID da cartinha     |

**Parâmetros do corpo da requisição:**

| Nome          | Tipo   | Descrição                             |
|---------------|--------|---------------------------------------|
| nome          | string | Nome da criança (opcional)            |
| sexo          | string | Sexo da criança (opcional)            |
| presente      | string | Presente desejado (opcional)          |
| status        | string | Status da cartinha (opcional)         |
| observacao    | string | Observação (opcional)                 |
| adotante_email| string | Email do adotante (opcional)          |

**Resposta de sucesso (200 OK):**

```json
{
  "id": 1,
  "id_carta": 101,
  "nome": "Nome Atualizado",
  "sexo": "M",
  "presente": "Brinquedo atualizado",
  "status": "disponível",
  "observacao": "Observação atualizada",
  "adotante_email": null,
  "del_bl": false,
  "del_time": null,
  "created_at": "2023-01-01T10:00:00",
  "updated_at": "2023-01-01T10:00:00"
}
```

**Resposta de erro (404 Not Found):**

```json
{
  "detail": "Cartinha não encontrada"
}
```

### Excluir uma Cartinha

```
DELETE /cartas/api/admin/{id_carta}
```

**Parâmetros de caminho:**

| Nome     | Tipo | Descrição           |
|----------|------|--------------------|
| id_carta | int  | ID da cartinha     |

**Resposta de sucesso (200 OK):**

```json
{
  "success": true,
  "message": "Cartinha removida com sucesso"
}
```

**Resposta de erro (404 Not Found):**

```json
{
  "detail": "Cartinha não encontrada"
}
```
