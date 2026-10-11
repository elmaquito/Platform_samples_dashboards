select model_id, model_name, category, manufacturer, unit_price::numeric(10,2) as unit_price
from {{ source('raw', 'dim_hardware_models') }}
