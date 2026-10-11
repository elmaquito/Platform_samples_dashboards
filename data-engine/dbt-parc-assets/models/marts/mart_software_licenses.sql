select
    i.software_name,
    count(*) as installations,
    sum(i.monthly_license_cost) as monthly_cost,
    sum(i.monthly_license_cost) * 12 as yearly_cost
from {{ ref('stg_software_installations') }} i
group by i.software_name
