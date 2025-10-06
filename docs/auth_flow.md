# Fluxo de Autenticação - Noel

Este documento descreve o fluxo de autenticação e autorização implementado no sistema Noel.

## Visão Geral

O sistema Noel utiliza um sistema de autenticação baseado em sessões para a interface web e tokens JWT para a API. A autenticação é realizada contra uma API LDAP externa, que valida as credenciais do usuário.

## Componentes Principais

### 1. Middleware de Autenticação

O middleware `AuthMiddleware` é responsável por verificar se o usuário está autenticado para acessar rotas protegidas. Ele:

- Verifica se o usuário possui uma sessão válida
- Redireciona para a página de login quando necessário
- Retorna erro 401 para requisições API não autenticadas
- Permite acesso livre a rotas públicas configuradas

### 2. Serviço de Autenticação

O serviço `AuthService` é responsável por:

- Comunicar-se com a API LDAP externa para validar credenciais
- Criar ou atualizar registros de usuário no banco de dados local
- Gerenciar as roles (papéis) dos usuários

### 3. Dependências de Autenticação

As dependências `get_current_user` e `require_roles` são utilizadas nas rotas para:

- Obter os dados do usuário atual a partir da sessão ou token JWT
- Verificar se o usuário possui as permissões necessárias para acessar determinadas rotas

## Fluxo de Autenticação Web

1. **Acesso à Rota Protegida:**
   - Usuário tenta acessar uma rota protegida
   - Middleware verifica se existe uma sessão válida
   - Se não existir, redireciona para `/login?next={url_original}`

2. **Login:**
   - Usuário preenche o formulário de login com email e senha
   - Aplicação envia as credenciais para a API LDAP
   - API LDAP valida as credenciais e retorna os dados do usuário
   - Aplicação cria uma sessão com os dados do usuário
   - Usuário é redirecionado para a URL original ou para a página inicial

3. **Acesso a Rotas Protegidas:**
   - Middleware verifica a sessão e permite o acesso
   - Dependência `get_current_user` fornece os dados do usuário para a rota
   - Dependência `require_roles` verifica se o usuário tem as permissões necessárias

4. **Logout:**
   - Usuário clica em "Sair"
   - Aplicação limpa a sessão
   - Usuário é redirecionado para a página inicial

## Fluxo de Autenticação API

1. **Login API:**
   - Cliente envia credenciais para `/api/auth/login`
   - Aplicação valida as credenciais com a API LDAP
   - Se válidas, gera um token JWT e retorna ao cliente
   - Cliente armazena o token para uso em requisições futuras

2. **Requisições Autenticadas:**
   - Cliente inclui o token no cabeçalho `Authorization: Bearer {token}`
   - Middleware verifica a validade do token
   - Dependência `get_current_user` extrai os dados do usuário do token
   - Dependência `require_roles` verifica as permissões do usuário

## Modelo de Roles (Papéis)

O sistema utiliza um modelo de roles para controlar o acesso a funcionalidades específicas:

1. **USER:** Papel padrão para todos os usuários autenticados
   - Pode visualizar cartinhas
   - Pode adotar cartinhas
   - Pode cancelar suas próprias adoções

2. **ADMIN:** Papel para administradores do sistema
   - Pode criar, editar e excluir cartinhas
   - Pode acessar a área administrativa
   - Pode gerenciar usuários e suas permissões

3. **RH:** Papel para usuários do departamento de RH
   - Pode visualizar relatórios
   - Pode gerenciar módulos

## Implementação Técnica

### Armazenamento de Sessão

As sessões são armazenadas em cookies criptografados usando o middleware `SessionMiddleware` do Starlette. A configuração inclui:

- Chave secreta para criptografia
- Tempo de expiração configurável
- Opção de cookie seguro em produção

### Estrutura de Banco de Dados

O sistema utiliza as seguintes tabelas para gerenciar autenticação e autorização:

1. **usuarios:** Armazena informações básicas dos usuários
   - `email` (PK): Email do usuário (identificador único)
   - `display_name`: Nome de exibição
   - `matricula`: Matrícula (opcional)
   - `id_modulo`: Referência ao módulo do usuário
   - `bl_ativo`: Flag indicando se o usuário está ativo

2. **roles:** Armazena os papéis disponíveis no sistema
   - `id` (PK): ID do papel
   - `code`: Código do papel (ex: "ADMIN", "USER")
   - `description`: Descrição do papel

3. **user_roles:** Associação muitos-para-muitos entre usuários e papéis
   - `user_email` (PK, FK): Email do usuário
   - `role_id` (PK, FK): ID do papel

## Segurança

- Senhas nunca são armazenadas no banco de dados local
- Autenticação é delegada à API LDAP externa
- Sessões são criptografadas
- Tokens JWT têm tempo de expiração limitado
- CORS configurado para restringir origens em ambiente de produção
- Middleware de autenticação protege todas as rotas por padrão

## Configuração

As seguintes variáveis de ambiente são utilizadas para configurar o sistema de autenticação:

- `LDAP_API_URL`: URL da API LDAP externa
- `SESSION_SECRET_KEY`: Chave secreta para criptografia de sessões
- `SESSION_MAX_AGE`: Tempo de vida máximo das sessões em segundos (padrão: 24 horas)

## Fluxograma de Autenticação

```
┌─────────────┐     ┌────────────────┐     ┌────────────────┐
│   Usuário   │────▶│  Formulário de │────▶│   API LDAP     │
│             │     │     Login      │     │                │
└─────────────┘     └────────────────┘     └───────┬────────┘
                                                  │
                                                  ▼
┌─────────────┐     ┌────────────────┐     ┌────────────────┐
│   Sessão    │◀────│  Validação de  │◀────│   Dados do     │
│             │     │  Credenciais   │     │    Usuário     │
└──────┬──────┘     └────────────────┘     └────────────────┘
       │
       ▼
┌─────────────┐     ┌────────────────┐     ┌────────────────┐
│   Acesso    │────▶│  Verificação   │────▶│   Acesso       │
│ Requisitado │     │   de Sessão    │     │  Permitido     │
└─────────────┘     └───────┬────────┘     └────────────────┘
                           │
                           ▼
                    ┌────────────────┐
                    │ Redirecionamento│
                    │  para Login    │
                    └────────────────┘
```

## Boas Práticas Implementadas

1. **Separação de Responsabilidades:**
   - Middleware para verificação de autenticação
   - Serviço para comunicação com API LDAP
   - Repositórios para acesso ao banco de dados
   - Dependências para injeção nas rotas

2. **Segurança:**
   - Autenticação delegada a serviço especializado
   - Sessões criptografadas
   - Verificação de permissões em cada rota protegida
   - Proteção contra CSRF

3. **Usabilidade:**
   - Redirecionamento para a URL original após login
   - Mensagens de erro claras
   - Feedback visual do status de autenticação
