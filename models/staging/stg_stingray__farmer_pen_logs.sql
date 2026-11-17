with

source as (
    select * from {{ source('stingray', 'farmer_pen_log') }}
),

typed as (
    select
        cast(source.log_id as integer) as log_id,
        trim(source.pen_id) as pen_id,
        cast(source.log_ts as timestamp) as logged_at_local,
        cast(source.fish_count as integer) as fish_count,
        trim(source.entered_by) as entered_by,
        nullif(trim(source.comment), '') as log_comment
    from source
),

final as (
    select
        typed.log_id,
        typed.pen_id,
        -- log_ts is naive local wall time: interpret it in the configured zone, then
        -- project to UTC so the result is independent of the session timezone.
        timezone(
            'UTC',
            timezone('{{ var("farmer_log_timezone") }}', typed.logged_at_local)
        ) as logged_at,
        typed.logged_at_local,
        cast(typed.logged_at_local as date) as logged_local_date,
        typed.fish_count,
        typed.entered_by,
        typed.log_comment
    from typed
)

select * from final
