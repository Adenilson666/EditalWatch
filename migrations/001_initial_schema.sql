BEGIN;

CREATE TABLE sources (
    id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    name VARCHAR(150) NOT NULL,

    base_url TEXT NOT NULL,

    source_type VARCHAR(20) NOT NULL,

    terms_url TEXT,

    robots_url TEXT,

    collection_allowed BOOLEAN NOT NULL
        DEFAULT FALSE,

    policy_checked_at TIMESTAMPTZ,

    is_active BOOLEAN NOT NULL
        DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_sources_name
        UNIQUE (name),

    CONSTRAINT ck_sources_source_type
        CHECK (
            source_type IN (
                'api',
                'html',
                'browser',
                'file'
            )
        )
);


CREATE TABLE collection_runs (
    id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    source_id BIGINT NOT NULL,

    started_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    finished_at TIMESTAMPTZ,

    status VARCHAR(20) NOT NULL
        DEFAULT 'running',

    records_found INTEGER NOT NULL
        DEFAULT 0,

    records_inserted INTEGER NOT NULL
        DEFAULT 0,

    records_updated INTEGER NOT NULL
        DEFAULT 0,

    records_rejected INTEGER NOT NULL
        DEFAULT 0,

    error_message TEXT,

    CONSTRAINT fk_collection_runs_source
        FOREIGN KEY (source_id)
        REFERENCES sources (id)
        ON DELETE RESTRICT,

    CONSTRAINT ck_collection_runs_status
        CHECK (
            status IN (
                'running',
                'success',
                'partial',
                'failed'
            )
        ),

    CONSTRAINT ck_collection_runs_counts
        CHECK (
            records_found >= 0
            AND records_inserted >= 0
            AND records_updated >= 0
            AND records_rejected >= 0
        ),

    CONSTRAINT ck_collection_runs_dates
        CHECK (
            finished_at IS NULL
            OR finished_at >= started_at
        )
);


CREATE TABLE notices (
    id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    source_id BIGINT NOT NULL,

    external_id VARCHAR(255),

    title TEXT NOT NULL,

    organization VARCHAR(255),

    notice_number VARCHAR(100),

    publication_date DATE,

    registration_deadline DATE,

    url TEXT NOT NULL,

    status VARCHAR(30) NOT NULL
        DEFAULT 'unknown',

    content_hash CHAR(64) NOT NULL,

    first_seen_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    last_seen_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    last_collection_run_id BIGINT,

    raw_payload JSONB NOT NULL
        DEFAULT '{}'::JSONB,

    CONSTRAINT fk_notices_source
        FOREIGN KEY (source_id)
        REFERENCES sources (id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_notices_last_collection_run
        FOREIGN KEY (last_collection_run_id)
        REFERENCES collection_runs (id)
        ON DELETE SET NULL,

    CONSTRAINT uq_notices_source_url
        UNIQUE (source_id, url),

    CONSTRAINT uq_notices_source_hash
        UNIQUE (source_id, content_hash),

    CONSTRAINT ck_notices_status
        CHECK (
            status IN (
                'unknown',
                'open',
                'closed',
                'suspended',
                'cancelled'
            )
        ),

    CONSTRAINT ck_notices_seen_dates
        CHECK (
            last_seen_at >= first_seen_at
        ),

    CONSTRAINT ck_notices_registration_deadline
        CHECK (
            registration_deadline IS NULL
            OR publication_date IS NULL
            OR registration_deadline >= publication_date
        )
);


CREATE TABLE categories (
    id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    name VARCHAR(100) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_categories_name
        UNIQUE (name)
);


CREATE TABLE notice_categories (
    notice_id BIGINT NOT NULL,

    category_id BIGINT NOT NULL,

    CONSTRAINT pk_notice_categories
        PRIMARY KEY (
            notice_id,
            category_id
        ),

    CONSTRAINT fk_notice_categories_notice
        FOREIGN KEY (notice_id)
        REFERENCES notices (id)
        ON DELETE CASCADE,

    CONSTRAINT fk_notice_categories_category
        FOREIGN KEY (category_id)
        REFERENCES categories (id)
        ON DELETE CASCADE
);


CREATE UNIQUE INDEX uq_notices_source_external_id
    ON notices (
        source_id,
        external_id
    )
    WHERE external_id IS NOT NULL;


CREATE INDEX idx_collection_runs_source_started_at
    ON collection_runs (
        source_id,
        started_at DESC
    );


CREATE INDEX idx_notices_publication_date
    ON notices (
        publication_date DESC
    );


CREATE INDEX idx_notices_registration_deadline
    ON notices (
        registration_deadline
    );


CREATE INDEX idx_notices_status
    ON notices (
        status
    );


CREATE INDEX idx_notices_last_seen_at
    ON notices (
        last_seen_at DESC
    );


CREATE INDEX idx_notices_raw_payload
    ON notices
    USING GIN (raw_payload);


COMMIT;