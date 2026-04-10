with source as (
    select * from raw_breathe
),

renamed as (
    select
        timestamp::timestamp as logged_at,
        -- session_id groups wim_hof rounds submitted together.
        -- Assumes all rounds in one session are submitted atomically (same second).
        cast(timestamp::timestamp as varchar) as session_id,
        type as entry_type,
        level as severity_level,
        label as severity_label,
        case
            when note = '' then null
            else note
        end as note
    from source
)

select * from renamed