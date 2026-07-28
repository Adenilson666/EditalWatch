# Modelo de dados do EditalWatch

## Objetivo

Armazenar fontes, execuções de coleta, editais e categorias,
mantendo rastreabilidade, histórico e prevenção de duplicidades.

## Entidades

### sources

Representa sites, APIs ou arquivos utilizados como fontes.

Campos principais:

- id;
- name;
- base_url;
- source_type;
- terms_url;
- robots_url;
- collection_allowed;
- policy_checked_at;
- is_active;
- created_at.

### collection_runs

Representa cada execução de coleta.

Campos principais:

- id;
- source_id;
- started_at;
- finished_at;
- status;
- records_found;
- records_inserted;
- records_updated;
- records_rejected;
- error_message.

### notices

Representa os editais e oportunidades encontrados.

Campos principais:

- id;
- source_id;
- external_id;
- title;
- organization;
- notice_number;
- publication_date;
- registration_deadline;
- url;
- status;
- content_hash;
- first_seen_at;
- last_seen_at;
- last_collection_run_id;
- raw_payload.

### categories

Representa as categorias aplicadas aos editais.

Campos principais:

- id;
- name;
- created_at.

### notice_categories

Relaciona editais e categorias.

Chave primária composta:

- notice_id;
- category_id.

## Relacionamentos

- Uma fonte possui várias execuções de coleta.
- Uma fonte possui vários editais.
- Um edital pode possuir várias categorias.
- Uma categoria pode pertencer a vários editais.

## Prevenção de duplicidades

A prevenção será realizada com:

1. source_id + external_id, quando existir ID externo;
2. source_id + URL canônica;
3. content_hash calculado com dados normalizados.

## Histórico

Cada edital terá:

- first_seen_at;
- last_seen_at;
- last_collection_run_id.

Cada execução registrará quantidades inseridas, atualizadas,
rejeitadas e eventuais erros.