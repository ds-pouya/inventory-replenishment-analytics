"""Aggregate dashboard metrics and interpret inventory tradeoffs."""
import math

import pandas as pd

from inventory_analytics.simulation import aggregate

POLICY_LABELS = {'fixed_cover': 'Fixed cover', 'order_up_to': 'Order-up-to'}
MODEL_LABELS = {'seasonal_naive_7': 'Previous week', 'mean_28': '28-day average',
                'calendar_ridge': 'Calendar ridge'}


def policy_metrics(ledger):
    return pd.DataFrame([{'policy': policy, **aggregate(group)}
                         for policy, group in ledger.groupby('policy')])


def decision_summary(metrics, threshold):
    if not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError('Fill threshold must be between zero and one')
    indexed = metrics.set_index('policy')
    if not set(POLICY_LABELS).issubset(indexed.index):
        raise ValueError('Both policies are required for a comparison')
    fixed, order = indexed.loc['fixed_cover'], indexed.loc['order_up_to']
    stock_change = ((order.average_ending_inventory / fixed.average_ending_inventory) - 1) * 100 if fixed.average_ending_inventory > 0 else None
    fill_change = (order.unit_fill_rate - fixed.unit_fill_rate) * 100 if pd.notna(fixed.unit_fill_rate) and pd.notna(order.unit_fill_rate) else None
    eligible = metrics[metrics.unit_fill_rate.notna() & (metrics.unit_fill_rate >= threshold)]
    winner = None
    if metrics.unit_fill_rate.isna().all():
        title = 'No requested units in this selection'
        detail = 'Fill rate is undefined when the replay contains no requested units.'
    elif eligible.empty:
        title = 'Neither policy meets the planning threshold'
        detail = f'Both simulated fill rates fall below {threshold:.1%}. Review the stock/service tradeoff before choosing a policy.'
    else:
        winner = eligible.sort_values(['average_ending_inventory', 'policy']).iloc[0].policy
        title = f'{POLICY_LABELS[winner]} meets the threshold with less stock' if len(eligible) > 1 else f'{POLICY_LABELS[winner]} is the only policy meeting the threshold'
        if len(eligible) > 1 and eligible.average_ending_inventory.nunique() == 1:
            title = 'Both policies meet the threshold with equal stock'
        detail = f'At a {threshold:.1%} planning threshold, this is the lowest-stock qualifying alternative among the two displayed policies. It is not a cost-optimal recommendation.'
    return {'title': title, 'detail': detail, 'winner': winner,
            'stock_change_pct': stock_change, 'fill_change_pp': fill_change}


def forecast_metrics(frame):
    rows = []
    for model, group in frame.groupby('model'):
        error = (group.prediction - group.actual).abs()
        total = float(group.actual.sum())
        rows.append({'model': model, 'mae': float(error.mean()),
                     'wape': float(error.sum() / total) if total else None,
                     'bias': float((group.prediction - group.actual).mean())})
    return pd.DataFrame(rows)
