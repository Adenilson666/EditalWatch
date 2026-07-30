BEGIN;


-- ============================================================
-- FONTES
-- ============================================================

INSERT INTO sources (
    name,
    base_url,
    source_type,
    collection_allowed,
    policy_checked_at,
    is_active
)
VALUES
    (
        'Portal Exemplo Federal',
        'https://example.com/federal',
        'html',
        TRUE,
        CURRENT_TIMESTAMP,
        TRUE
    ),
    (
        'API Exemplo Acadêmica',
        'https://api.example.com/academic',
        'api',
        TRUE,
        CURRENT_TIMESTAMP,
        TRUE
    )
ON CONFLICT (name)
DO UPDATE SET
    base_url = EXCLUDED.base_url,
    source_type = EXCLUDED.source_type,
    collection_allowed = EXCLUDED.collection_allowed,
    policy_checked_at = EXCLUDED.policy_checked_at,
    is_active = EXCLUDED.is_active;


-- ============================================================
-- CATEGORIAS
-- ============================================================

INSERT INTO categories (name)
VALUES
    ('Tecnologia da Informação'),
    ('Desenvolvimento'),
    ('Banco de Dados'),
    ('Segurança da Informação'),
    ('Infraestrutura'),
    ('Nível Superior')
ON CONFLICT (name)
DO NOTHING;


-- ============================================================
-- EXECUÇÕES DE COLETA
-- ============================================================

INSERT INTO collection_runs (
    source_id,
    started_at,
    finished_at,
    status,
    records_found,
    records_inserted,
    records_updated,
    records_rejected
)
SELECT
    source.id,
    TIMESTAMPTZ '2026-07-29 08:00:00-03',
    TIMESTAMPTZ '2026-07-29 08:00:05-03',
    'success',
    3,
    3,
    0,
    0
FROM sources AS source
WHERE source.name = 'Portal Exemplo Federal'
AND NOT EXISTS (
    SELECT 1
    FROM collection_runs AS run
    WHERE run.source_id = source.id
      AND run.started_at =
          TIMESTAMPTZ '2026-07-29 08:00:00-03'
);


INSERT INTO collection_runs (
    source_id,
    started_at,
    finished_at,
    status,
    records_found,
    records_inserted,
    records_updated,
    records_rejected
)
SELECT
    source.id,
    TIMESTAMPTZ '2026-07-29 08:05:00-03',
    TIMESTAMPTZ '2026-07-29 08:05:03-03',
    'success',
    2,
    2,
    0,
    0
FROM sources AS source
WHERE source.name = 'API Exemplo Acadêmica'
AND NOT EXISTS (
    SELECT 1
    FROM collection_runs AS run
    WHERE run.source_id = source.id
      AND run.started_at =
          TIMESTAMPTZ '2026-07-29 08:05:00-03'
);


-- ============================================================
-- EDITAIS
-- ============================================================

WITH notice_data (
    source_name,
    external_id,
    title,
    organization,
    notice_number,
    publication_date,
    registration_deadline,
    url,
    status,
    content_hash,
    seen_at,
    run_started_at,
    raw_payload
) AS (
    VALUES
        (
            'Portal Exemplo Federal',
            'FED-001',
            'Concurso para Analista de Tecnologia da Informação',
            'Instituição Federal de Demonstração',
            '01/2026',
            DATE '2026-07-20',
            DATE '2026-08-15',
            'https://example.com/federal/edital-001',
            'open',
            repeat('a', 64),
            TIMESTAMPTZ '2026-07-29 08:00:00-03',
            TIMESTAMPTZ '2026-07-29 08:00:00-03',
            '{
                "external_id": "FED-001",
                "origin": "demo"
            }'::JSONB
        ),
        (
            'Portal Exemplo Federal',
            'FED-002',
            'Concurso para Especialista em Banco de Dados',
            'Instituição Federal de Demonstração',
            '02/2026',
            DATE '2026-07-22',
            DATE '2026-08-10',
            'https://example.com/federal/edital-002',
            'open',
            repeat('b', 64),
            TIMESTAMPTZ '2026-07-29 08:00:00-03',
            TIMESTAMPTZ '2026-07-29 08:00:00-03',
            '{
                "external_id": "FED-002",
                "origin": "demo"
            }'::JSONB
        ),
        (
            'Portal Exemplo Federal',
            'FED-003',
            'Processo Seletivo para Desenvolvedor de Sistemas',
            'Instituição Federal de Demonstração',
            '03/2026',
            DATE '2026-07-25',
            DATE '2026-08-20',
            'https://example.com/federal/edital-003',
            'open',
            repeat('c', 64),
            TIMESTAMPTZ '2026-07-29 08:00:00-03',
            TIMESTAMPTZ '2026-07-29 08:00:00-03',
            '{
                "external_id": "FED-003",
                "origin": "demo"
            }'::JSONB
        ),
        (
            'API Exemplo Acadêmica',
            'API-001',
            'Seleção para Segurança da Informação',
            'Universidade de Demonstração',
            '04/2026',
            DATE '2026-07-21',
            DATE '2026-08-18',
            'https://api.example.com/academic/notice-001',
            'open',
            repeat('d', 64),
            TIMESTAMPTZ '2026-07-29 08:05:00-03',
            TIMESTAMPTZ '2026-07-29 08:05:00-03',
            '{
                "external_id": "API-001",
                "origin": "demo"
            }'::JSONB
        ),
        (
            'API Exemplo Acadêmica',
            'API-002',
            'Seleção Temporária para Suporte e Infraestrutura',
            'Universidade de Demonstração',
            '05/2026',
            DATE '2026-07-10',
            DATE '2026-07-25',
            'https://api.example.com/academic/notice-002',
            'closed',
            repeat('e', 64),
            TIMESTAMPTZ '2026-07-29 08:05:00-03',
            TIMESTAMPTZ '2026-07-29 08:05:00-03',
            '{
                "external_id": "API-002",
                "origin": "demo"
            }'::JSONB
        )
)

INSERT INTO notices (
    source_id,
    external_id,
    title,
    organization,
    notice_number,
    publication_date,
    registration_deadline,
    url,
    status,
    content_hash,
    first_seen_at,
    last_seen_at,
    last_collection_run_id,
    raw_payload
)
SELECT
    source.id,
    data.external_id,
    data.title,
    data.organization,
    data.notice_number,
    data.publication_date,
    data.registration_deadline,
    data.url,
    data.status,
    data.content_hash,
    data.seen_at,
    data.seen_at,
    run.id,
    data.raw_payload
FROM notice_data AS data

INNER JOIN sources AS source
    ON source.name = data.source_name

LEFT JOIN collection_runs AS run
    ON run.source_id = source.id
   AND run.started_at = data.run_started_at

ON CONFLICT (source_id, url)
DO UPDATE SET
    external_id = EXCLUDED.external_id,
    title = EXCLUDED.title,
    organization = EXCLUDED.organization,
    notice_number = EXCLUDED.notice_number,
    publication_date = EXCLUDED.publication_date,
    registration_deadline =
        EXCLUDED.registration_deadline,
    status = EXCLUDED.status,
    content_hash = EXCLUDED.content_hash,
    last_seen_at = GREATEST(
        notices.last_seen_at,
        EXCLUDED.last_seen_at
    ),
    last_collection_run_id =
        EXCLUDED.last_collection_run_id,
    raw_payload = EXCLUDED.raw_payload;


-- ============================================================
-- RELACIONAMENTO EDITAL-CATEGORIA
-- ============================================================

WITH category_mapping (
    source_name,
    external_id,
    category_name
) AS (
    VALUES
        (
            'Portal Exemplo Federal',
            'FED-001',
            'Tecnologia da Informação'
        ),
        (
            'Portal Exemplo Federal',
            'FED-001',
            'Nível Superior'
        ),
        (
            'Portal Exemplo Federal',
            'FED-002',
            'Tecnologia da Informação'
        ),
        (
            'Portal Exemplo Federal',
            'FED-002',
            'Banco de Dados'
        ),
        (
            'Portal Exemplo Federal',
            'FED-003',
            'Tecnologia da Informação'
        ),
        (
            'Portal Exemplo Federal',
            'FED-003',
            'Desenvolvimento'
        ),
        (
            'API Exemplo Acadêmica',
            'API-001',
            'Tecnologia da Informação'
        ),
        (
            'API Exemplo Acadêmica',
            'API-001',
            'Segurança da Informação'
        ),
        (
            'API Exemplo Acadêmica',
            'API-002',
            'Tecnologia da Informação'
        ),
        (
            'API Exemplo Acadêmica',
            'API-002',
            'Infraestrutura'
        )
)

INSERT INTO notice_categories (
    notice_id,
    category_id
)
SELECT
    notice.id,
    category.id
FROM category_mapping AS mapping

INNER JOIN sources AS source
    ON source.name = mapping.source_name

INNER JOIN notices AS notice
    ON notice.source_id = source.id
   AND notice.external_id = mapping.external_id

INNER JOIN categories AS category
    ON category.name = mapping.category_name

ON CONFLICT DO NOTHING;


COMMIT;