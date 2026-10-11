select user_id, initcap(trim(full_name)) as full_name, lower(trim(email)) as email, department, city
from {{ source('raw', 'dim_users') }}
