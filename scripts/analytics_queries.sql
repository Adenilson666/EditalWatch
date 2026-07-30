-- ============================================================
-- 1. INNER JOIN: EDITAIS E SUAS FONTES
-- ============================================================

SELECT
    notice.id,
    notice.title,
    source.name AS source_name,
    notice.status,
    notice.registration_deadline
FROM notices AS notice

INNER JOIN sources AS source
    ON source.id = notice.source_id

ORDER BY
    notice.registration_deadline,
    notice.title;


-- ============================================================
-- 2. JOIN MUITOS-PARA-MUITOS: EDITAIS E CATEGORIAS
-- ============================================================

SELECT
    notice.title,

    STRING_AGG(
        category.name,
        ', '
        ORDER BY category.name
    ) AS categories

FROM notices AS notice

INNER JOIN notice_categories AS relationship
    ON relationship.notice_id = notice.id

INNER JOIN categories AS category
    ON category.id = relationship.category_id

GROUP BY
    notice.id,
    notice.title

ORDER BY
    notice.title;


-- ============================================================
-- 3. GROUP BY: QUANTIDADE DE EDITAIS POR FONTE
-- ============================================================

SELECT
    source.name,

    COUNT(notice.id) AS total_notices,

    COUNT(notice.id) FILTER (
        WHERE notice.status = 'open'
    ) AS open_notices,

    COUNT(notice.id) FILTER (
        WHERE notice.status = 'closed'
    ) AS closed_notices

FROM sources AS source

LEFT JOIN notices AS notice
    ON notice.source_id = source.id

GROUP BY
    source.id,
    source.name

ORDER BY
    total_notices DESC,
    source.name;


-- ============================================================
-- 4. HAVING: CATEGORIAS COM DOIS OU MAIS EDITAIS
-- ============================================================

SELECT
    category.name,
    COUNT(relationship.notice_id) AS total_notices
FROM categories AS category

LEFT JOIN notice_categories AS relationship
    ON relationship.category_id = category.id

GROUP BY
    category.id,
    category.name

HAVING COUNT(relationship.notice_id) >= 2

ORDER BY
    total_notices DESC,
    category.name;


-- ============================================================
-- 5. SUBCONSULTA: FONTES ACIMA DA MÉDIA DE EDITAIS
-- ============================================================

SELECT
    source.name,

    (
        SELECT COUNT(*)
        FROM notices AS notice
        WHERE notice.source_id = source.id
    ) AS total_notices

FROM sources AS source

WHERE (
    SELECT COUNT(*)
    FROM notices AS notice
    WHERE notice.source_id = source.id
) > (
    SELECT AVG(source_total)
    FROM (
        SELECT
            COUNT(*)::NUMERIC AS source_total
        FROM notices
        GROUP BY source_id
    ) AS totals
)

ORDER BY
    source.name;


-- ============================================================
-- 6. EXECUÇÕES DE COLETA
-- ============================================================

SELECT
    source.name,
    run.status,
    run.records_found,
    run.records_inserted,
    run.records_updated,
    run.records_rejected,

    EXTRACT(
        EPOCH FROM (
            run.finished_at - run.started_at
        )
    ) AS duration_seconds

FROM collection_runs AS run

INNER JOIN sources AS source
    ON source.id = run.source_id

ORDER BY
    run.started_at DESC;


-- ============================================================
-- 7. PLANO DE EXECUÇÃO
-- ============================================================

ANALYZE notices;

EXPLAIN (
    ANALYZE,
    BUFFERS
)
SELECT
    id,
    title,
    registration_deadline
FROM notices
WHERE status = 'open'
ORDER BY registration_deadline;