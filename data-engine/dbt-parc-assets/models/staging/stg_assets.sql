select asset_id, serial_number, model_id, user_id, status,
       purchase_date::date as purchase_date, warranty_end_date::date as warranty_end_date
from {{ source('raw', 'fact_assets') }}
