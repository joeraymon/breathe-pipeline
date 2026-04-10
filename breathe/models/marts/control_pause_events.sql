select
    logged_at,
    severity_level as duration_s,
    note
from {{ ref('stg_breathe') }}
where entry_type = 'control_pause'
order by logged_at
