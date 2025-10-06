# Changelog

## [0.1.5] - 2025-09-25
### Corrigido
- Ajustados os modelos SQLAlchemy para usar explicitamente o esquema `public`
- Atualizadas as chaves estrangeiras para referenciar o esquema correto
- Garantido que as tabelas relacionadas à autenticação e cartas usem o mesmo esquema

## [0.1.4] - 2025-09-25
### Corrigido
- Corrigido erro na análise da URL do banco de dados
- Melhorada a robustez do código para lidar com diferentes formatos de URL

## [0.1.3] - 2025-09-25
### Adicionado
- Adicionado diagnóstico detalhado para a conexão com o banco de dados
- Adicionado logging para ajudar na depuração de problemas de conexão
- Adicionada verificação automática da conexão e das tabelas do banco de dados na inicialização

## [0.1.2] - 2025-09-25
### Corrigido
- Corrigido problema com o esquema do banco de dados PostgreSQL
- Modificado o SQLAlchemy para usar explicitamente o esquema "public"
- Adicionado script para verificar e garantir que as tabelas estejam no esquema correto

## [0.1.1] - 2025-09-25
### Corrigido
- Corrigido problema de autenticação LDAP onde o sistema não conseguia identificar o usuário corretamente
- Modificado o método de autenticação para usar o username como identificador do usuário
- Melhorada a extração de informações da resposta LDAP para criar usuários no banco de dados

### Adicionado
- Criado script SQL para configuração das tabelas de autenticação (roles e user_roles)
- Adicionado suporte para criar automaticamente um usuário administrador inicial

## [0.1.0] - 2025-09-24
### Adicionado
- Versão inicial do sistema migrado para FastAPI
- Implementação básica de autenticação LDAP
- Estrutura de banco de dados PostgreSQL
- Integração com MinIO para armazenamento de arquivos
