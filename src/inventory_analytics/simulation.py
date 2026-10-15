"""Deterministic lost-sales inventory replay with auditable daily ledgers."""
import json
import math
from numbers import Integral
from pathlib import Path
from statistics import NormalDist
import tomllib

import numpy as np
import pandas as pd

from inventory_analytics.forecasting import fingerprints, forecast_at_origin, load_sales, sha

POLICIES = ('fixed_cover', 'order_up_to')


def whole(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
        raise ValueError(f'{name} must be an integer >= {minimum}')
    return int(value)


def simulate(demand, initial_stock, lead_time, review_period, policy, fixed_quantity=0, targets=None):
    """Receipts -> opening review/order -> demand -> closing stock. No backorders."""
    stock = whole(initial_stock, 'initial_stock')
    lead_time = whole(lead_time, 'lead_time', 1)
    review_period = whole(review_period, 'review_period', 1)
    fixed_quantity = whole(fixed_quantity, 'fixed_quantity')
    values = np.asarray(demand, dtype=float)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all() or (values < 0).any() or (values != np.floor(values)).any():
        raise ValueError('Demand must contain finite nonnegative whole units')
    if policy not in POLICIES:
        raise ValueError('Unknown policy')
    if policy == 'order_up_to':
        levels = np.asarray(targets, dtype=float)
        if levels.shape != values.shape or not np.isfinite(levels).all() or (levels < 0).any():
            raise ValueError('One finite nonnegative target is required per day')
    pending = {}
    rows = []
    total_received = total_fulfilled = total_ordered = 0
    for index, requested in enumerate(values):
        day = index + 1
        opening = stock
        receipts = pending.pop(day, 0)
        stock += receipts
        on_order_before = sum(pending.values())
        position = stock + on_order_before
        review = index % review_period == 0
        target = math.ceil(float(levels[index])) if policy == 'order_up_to' else None
        order = 0
        if review:
            order = fixed_quantity if policy == 'fixed_cover' else max(0, target - stock - on_order_before)
            if order:
                pending[day + lead_time] = pending.get(day + lead_time, 0) + order
        requested = int(requested)
        fulfilled = min(requested, stock)
        stock -= fulfilled
        lost = requested - fulfilled
        on_order = sum(pending.values())
        total_received += receipts
        total_fulfilled += fulfilled
        total_ordered += order
        if opening + receipts - fulfilled != stock or fulfilled + lost != requested:
            raise AssertionError('Daily inventory or demand conservation failed')
        if initial_stock + total_received - total_fulfilled != stock or total_ordered - total_received != on_order:
            raise AssertionError('Cumulative stock or pipeline conservation failed')
        rows.append({'simulation_day': day, 'opening_stock': opening, 'receipts': receipts,
            'review': review, 'target_stock': target, 'inventory_position_before_order': position,
            'ordered_units': order, 'demand_proxy_units': requested, 'fulfilled_units': fulfilled,
            'lost_units': lost, 'ending_stock': stock, 'ending_on_order': on_order})
    return pd.DataFrame(rows)


def summarize(ledger):
    requested = int(ledger.demand_proxy_units.sum())
    fulfilled = int(ledger.fulfilled_units.sum())
    return {'demand_proxy_units': requested, 'fulfilled_units': fulfilled,
        'lost_units': int(ledger.lost_units.sum()), 'unit_fill_rate': fulfilled / requested if requested else None,
        'average_ending_inventory': float(ledger.ending_stock.mean()),
        'ending_stock': int(ledger.ending_stock.iloc[-1]),
        'ending_on_order': int(ledger.ending_on_order.iloc[-1]),
        'ordered_units': int(ledger.ordered_units.sum()),
        'order_count': int((ledger.ordered_units > 0).sum()),
        'shortage_item_days': int((ledger.lost_units > 0).sum())}


def aggregate(ledger):
    """Summed inventory across products averaged over days; volume-weighted fill."""
    result = summarize(ledger)
    daily = ledger.groupby('simulation_day').ending_stock.sum()
    result['average_ending_inventory'] = float(daily.mean())
    last = ledger[ledger.simulation_day == ledger.simulation_day.max()]
    result['ending_stock'] = int(last.ending_stock.sum())
    result['ending_on_order'] = int(last.ending_on_order.sum())
    return result


def read_config(root):
    config = tomllib.loads((Path(root) / 'config/scenarios.toml').read_text())
    base = config['scenario']
    for name in ('lead_time_days', 'review_period_days'):
        whole(base[name], name, 1)
    whole(base['initial_stock_cover_days'], 'initial_stock_cover_days')
    if not 0.5 <= base['service_target'] < 1:
        raise ValueError('service_target must be >= 0.5 and < 1')
    if base['unmet_demand_behavior'] != 'lost_sales' or base['monetary_costs_enabled']:
        raise ValueError('Only lost sales without monetary costs are supported')
    for value in config['sensitivity']['lead_time_days']:
        whole(value, 'sensitivity lead time', 1)
    for value in config['sensitivity']['initial_stock_cover_days']:
        whole(value, 'sensitivity initial cover')
    return config


def run(root):
    root = Path(root)
    out = root / 'data/processed'
    selection_path = root / 'docs/FORECAST_SELECTION.json'
    selection = json.loads(selection_path.read_text())
    if selection['fingerprints'] != fingerprints(root):
        raise ValueError('Forecast inputs differ from the frozen selection')
    config = read_config(root)
    base = config['scenario']
    leads = sorted(set(config['sensitivity']['lead_time_days'] + [base['lead_time_days']]))
    covers = sorted(set(config['sensitivity']['initial_stock_cover_days'] + [base['initial_stock_cover_days']]))
    sales, build = load_sales(root)
    ev = build['evaluation']
    origin = ev['final_holdout_start_day'] - 1
    days = ev['final_holdout_end_day'] - origin
    review = base['review_period_days']
    protection = max(leads) + review
    forecast_length = days + protection - 1
    spec = tomllib.loads((root / 'config/forecasting.toml').read_text())
    model = selection['selected_model']
    validation = pd.read_parquet(out / 'validation_forecasts.parquet')
    errors = validation[validation.model == model].copy()
    expected_start = ev['initial_train_end_day'] + 1
    expected_count = ev['validation_windows'] * ev['horizon_days']
    expected_origins = {ev['initial_train_end_day'] + i * ev['horizon_days'] for i in range(ev['validation_windows'])}
    if set(errors.origin) != expected_origins or errors.day_number.min() != expected_start or errors.day_number.max() != origin:
        raise ValueError('Safety calibration must use the complete pre-simulation validation period')
    if errors.duplicated(['item_id', 'day_number']).any() or not errors.groupby('item_id').size().eq(expected_count).all():
        raise ValueError('Incomplete or duplicate calibration observations')
    if set(errors.item_id) != set(sales.item_id) or not np.isfinite(errors[['actual', 'prediction']].to_numpy()).all():
        raise ValueError('Invalid safety calibration coverage or values')
    errors['residual'] = errors.actual - errors.prediction
    sigma = errors.groupby('item_id').residual.std(ddof=1)
    calendar = pd.read_csv(root / build['data']['raw_directory'] / build['data']['calendar_file'])
    calendar['day_number'] = calendar.d.str[2:].astype(int)
    calendar['date'] = pd.to_datetime(calendar.date)
    if calendar.day_number.duplicated().any():
        raise ValueError('Calendar days must be unique')
    calendar['event'] = calendar[['event_name_1', 'event_name_2']].notna().any(axis=1).astype(float)
    z = NormalDist().inv_cdf(base['service_target'])
    ledgers, product_rows, assumptions = [], [], []
    for item, group in sales.groupby('item_id'):
        past = group[group.day_number <= origin].sort_values('day_number')
        actual = group[(group.day_number > origin) & (group.day_number <= origin + days)].sort_values('day_number')
        if actual.day_number.tolist() != list(range(origin + 1, origin + days + 1)):
            raise ValueError('Simulation needs contiguous replay days')
        state = past.state_id.iloc[0]
        future = calendar[(calendar.day_number > origin) & (calendar.day_number <= origin + forecast_length)].copy()
        if future.day_number.tolist() != list(range(origin + 1, origin + forecast_length + 1)):
            raise ValueError('Insufficient known calendar for full protection windows')
        future['snap'] = future['snap_' + state]
        # Future calendar rows contain no observed demand; the forecast origin stays fixed.
        future['units'] = np.nan
        _, predictions = forecast_at_origin(pd.concat([past, future], ignore_index=True), origin, forecast_length, spec)
        forecasts = predictions[model]
        mean = float(past.units.tail(28).mean())
        fixed_quantity = math.ceil(mean * review)
        daily_sigma = float(sigma.loc[item])
        for lead in leads:
            length = lead + review
            safety = z * daily_sigma * math.sqrt(length)
            targets = [float(forecasts[index:index+length].sum() + safety) for index in range(days)]
            for cover in covers:
                scenario = f'L{lead}_R{review}_I{cover}'
                initial = math.ceil(mean * cover)
                assumptions.append({'scenario_id': scenario, 'item_id': item, 'initial_stock': initial,
                    'mean_daily_sales_before_start': mean, 'fixed_order_quantity': fixed_quantity,
                    'validation_residual_std': daily_sigma, 'safety_buffer_units': safety})
                for policy in POLICIES:
                    ledger = simulate(actual.units.to_numpy(), initial, lead, review, policy, fixed_quantity, targets)
                    ledger['item_id'], ledger['scenario_id'], ledger['policy'] = item, scenario, policy
                    ledger['date'] = actual.date.to_numpy()
                    ledger['day_number'] = actual.day_number.to_numpy()
                    ledgers.append(ledger)
                    product_rows.append({'scenario_id': scenario, 'item_id': item, 'policy': policy, **summarize(ledger)})
    daily = pd.concat(ledgers, ignore_index=True)
    results = []
    base_id = f"L{base['lead_time_days']}_R{review}_I{base['initial_stock_cover_days']}"
    for (scenario, policy), group in daily.groupby(['scenario_id', 'policy']):
        results.append({'scenario_id': scenario, 'policy': policy, 'is_base_case': scenario == base_id,
                        **aggregate(group)})
    manifest = {'scenario_config': config, 'selected_forecast_model': model, 'forecast_origin_day': origin,
        'replay_start_day': origin+1, 'replay_end_day': origin+days,
        'interpretation': 'Retrospective deterministic sales replay; hypothetical inventory inputs; no causal or financial savings estimate.',
        'checks': 'passed: daily stock/demand balance and cumulative stock/pipeline conservation',
        'fingerprints': {'scenarios': sha(root/'config/scenarios.toml'), 'simulation_code': sha(Path(__file__)),
            'frozen_selection': sha(selection_path), 'calibration_forecasts': sha(out/'validation_forecasts.parquet')},
        'results': results}
    daily.to_parquet(out/'simulation_daily.parquet', index=False)
    pd.DataFrame(product_rows).to_parquet(out/'simulation_products.parquet', index=False)
    pd.DataFrame(assumptions).to_parquet(out/'simulation_assumptions.parquet', index=False)
    (out/'simulation_summary.json').write_text(json.dumps(manifest, indent=2, allow_nan=False))
    return manifest
