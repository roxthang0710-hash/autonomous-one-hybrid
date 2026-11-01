"""Offline scenario arithmetic. Synthetic assumptions are never observed evidence."""
from math import isfinite


def simulate(*, visitors=100, conversion_rate=0.05, price_vnd=0, unit_cost_vnd=0):
    if type(visitors) is not int or not 0 <= visitors <= 1000000:
        raise ValueError('visitors must be an integer between 0 and 1000000')
    for value in (conversion_rate, price_vnd, unit_cost_vnd):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
            raise ValueError('assumptions must be finite numbers')
    if not 0 <= conversion_rate <= 1 or min(price_vnd, unit_cost_vnd) < 0 or max(price_vnd, unit_cost_vnd) > 1000000000:
        raise ValueError('invalid conversion or price assumptions')
    scenarios = []
    for label, multiplier in [('low', 0.5), ('base', 1), ('high', 1.5)]:
        customers = round(visitors * min(1, conversion_rate * multiplier), 2)
        scenarios.append({'scenario': label, 'synthetic_customers': customers,
                          'hypothetical_revenue_vnd': round(customers * price_vnd),
                          'hypothetical_margin_vnd': round(customers * (price_vnd-unit_cost_vnd))})
    return {'mode': 'simulation_only', 'evidence_status': 'unvalidated',
            'assumptions': {'visitors': visitors, 'conversion_rate': conversion_rate,
                            'price_vnd': price_vnd, 'unit_cost_vnd': unit_cost_vnd},
            'scenarios': scenarios, 'actual_spend_vnd': 0, 'actual_revenue_vnd': 0}
