select installation_id, asset_id, software_name,
       monthly_license_cost::numeric(10,2) as monthly_license_cost, installed_at::date as installed_at
from {{ source('raw', 'fact_software_installations') }}
