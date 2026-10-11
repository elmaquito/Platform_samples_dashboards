select
    a.asset_id, a.serial_number, a.status, a.purchase_date, a.warranty_end_date,
    (a.warranty_end_date < current_date) as is_out_of_warranty,
    m.model_name, m.category, m.manufacturer, m.unit_price,
    u.full_name as user_name, u.department, u.city
from {{ ref('stg_assets') }} a
join {{ ref('stg_hardware_models') }} m using (model_id)
left join {{ ref('stg_users') }} u using (user_id)
