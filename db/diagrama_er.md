# Diagrama de Entidade-Relacionamento (ER)

Diagrama completo do banco de dados do sistema Noel-R utilizando Mermaid.js.

```mermaid
erDiagram
    usuarios ||--o{ cartas_diversas : "adota"
    usuarios ||--o{ cartas_diversas : "entrega"
    usuarios }o--|| modulo : "pertence"
    usuarios ||--o{ user_roles : "tem"
    modulo ||--o{ usuarios : "contém"
    grupos ||--o{ cartas_diversas : "categoriza"
    roles ||--o{ user_roles : "atribui"
    user_roles }o--|| usuarios : "vincula"
    user_roles }o--|| roles : "vincula"
    
    usuarios {
        text email PK "Chave primária"
        text display_name "Nome de exibição"
        text matricula "Matrícula do usuário"
        integer id_modulo FK "Referência ao módulo"
        boolean bl_ativo "Usuário ativo"
        timestamptz created_at "Data de criação"
    }
    
    modulo {
        integer id_modulo PK "Chave primária"
        text nome UK "Nome único do módulo"
    }
    
    cartas_diversas {
        integer id PK "Chave primária (auto-incremento)"
        integer id_carta UK "ID único da carta"
        text nome "Nome da criança"
        text sexo "M ou F"
        text presente "Presente desejado"
        text status "Status da carta"
        text observacao "Observações"
        text adotante_email FK "Email do adotante"
        text urlcarta "URL do anexo (PDF/Imagem)"
        text urlcarta_pq "URL da miniatura (200x300)"
        integer idade "Idade da criança"
        integer id_grupo_key FK "Grupo da cartinha"
        integer cod_carta "Código adicional"
        boolean del_bl "Soft delete"
        timestamptz del_time "Data de exclusão"
        timestamptz created_at "Data de criação"
        timestamptz updated_at "Data de atualização"
        boolean entregue_bl "Flag de entrega"
        text entregue_por_email FK "Email de quem entregou"
        timestamptz entregue_em "Data de entrega"
    }
    
    grupos {
        integer id_grupo PK "Chave primária"
        text ds_grupo "Descrição do grupo"
        text cor "Cor em hexadecimal (ex: #00FF00)"
    }
    
    icon_presente {
        integer id PK "Chave primária"
        text keyword "Palavra-chave"
        text icon_code "Código do ícone"
    }
    
    roles {
        integer id PK "Chave primária"
        text code UK "Código único do papel"
        text description "Descrição do papel"
    }
    
    user_roles {
        integer id PK "Chave primária"
        text user_email FK "Email do usuário"
        integer role_id FK "ID do papel"
    }
```

## Legenda

- **PK**: Primary Key (Chave Primária)
- **FK**: Foreign Key (Chave Estrangeira)
- **UK**: Unique Key (Chave Única)
- **||--o{**: Relacionamento Um-para-Muitos
- **}o--||**: Relacionamento Muitos-para-Um

## Descrição dos Relacionamentos

1. **usuarios ↔ modulo**: Um usuário pertence a um módulo (opcional). Um módulo pode ter muitos usuários.
2. **usuarios ↔ cartas_diversas (adota)**: Um usuário pode adotar muitas cartinhas. Uma cartinha pode ter um adotante (opcional).
3. **usuarios ↔ cartas_diversas (entrega)**: Um usuário (admin) pode marcar muitas cartinhas como entregues. Uma cartinha pode ser entregue por um usuário.
4. **grupos ↔ cartas_diversas**: Um grupo pode ter muitas cartinhas. Uma cartinha pertence a um grupo (opcional).
5. **usuarios ↔ user_roles ↔ roles**: Sistema RBAC (Role-Based Access Control). Um usuário pode ter muitos papéis através da tabela de associação `user_roles`.

## Índices Principais

- `idx_cartas_status`: Índice no campo `status` da tabela `cartas_diversas`
- `idx_cartas_adotante`: Índice no campo `adotante_email` da tabela `cartas_diversas`
- `idx_cartas_delbl`: Índice no campo `del_bl` da tabela `cartas_diversas`
- `idx_cartas_entregue`: Índice no campo `entregue_bl` da tabela `cartas_diversas`

## Constraints

- **ck_cartas_sexo**: Check constraint que garante que o campo `sexo` em `cartas_diversas` seja apenas 'M' ou 'F'
- **uq_user_role**: Unique constraint em `user_roles` para evitar duplicação de pares (user_email, role_id)

