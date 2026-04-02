with source as (
    select * from raw_breathe
),

renamed as (
    select
        timestamp::timestamp as logged_at,
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