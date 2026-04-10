with source as (
    select * from raw_breathe
),

renamed as (
    select
        timestamp::timestamp as logged_at,
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