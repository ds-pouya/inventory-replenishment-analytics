"""Chronological forecasting with a frozen selection and final evaluation."""
import hashlib
import json
from pathlib import Path
import tomllib

import duckdb
import numpy as np
import pandas as pd

MODELS = ('seasonal_naive_7', 'mean_28', 'calendar_ridge')


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def load_sales(root):
    root = Path(root)
    processed = root / 'data/processed'
    cfg = json.loads((processed / 'build_config.json').read_text())
    with duckdb.connect() as con:
        sales = con.execute('SELECT * FROM read_parquet(?) ORDER BY item_id, day_number',
                            [str(processed / 'daily_sales.parquet')]).df()
    calendar = pd.read_csv(root / cfg['data']['raw_directory'] / cfg['data']['calendar_file'])
    if calendar.d.duplicated().any():
        raise ValueError('Calendar day keys must be unique')
    context = calendar[['d', 'event_name_1', 'event_name_2', 'snap_CA', 'snap_TX', 'snap_WI']]
    sales = sales.merge(context, on='d', how='left', validate='many_to_one', indicator=True)
    if not sales['_merge'].eq('both').all():
        raise ValueError('Missing calendar context')
    sales['event'] = sales[['event_name_1', 'event_name_2']].notna().any(axis=1).astype(float)
    sales['snap'] = [row['snap_' + row['state_id']] for _, row in sales.iterrows()]
    sales['date'] = pd.to_datetime(sales.date)
    return sales, cfg


def design(frame, origin_date, scale):
    """Only calendar information available at forecast origin; no future sales/prices."""
    dates = pd.to_datetime(frame.date)
    weekday = dates.dt.dayofweek.to_numpy()
    annual = 2 * np.pi * (dates.dt.dayofyear.to_numpy() - 1) / 365.25
    trend = (dates - origin_date).dt.days.to_numpy() / scale
    return np.column_stack([np.ones(len(frame)),
        *[(weekday == day).astype(float) for day in range(1, 7)],
        np.sin(annual), np.cos(annual), trend,
        frame.snap.to_numpy(dtype=float), frame.event.to_numpy(dtype=float)])


def forecast_at_origin(group, origin, horizon, spec):
    history = group[group.day_number <= origin].sort_values('day_number')
    future = group[(group.day_number > origin) & (group.day_number <= origin + horizon)].sort_values('day_number')
    if len(history) < 28 or len(future) != horizon:
        raise ValueError('Insufficient history or incomplete forecast horizon')
    y = history.units.to_numpy(dtype=float)
    weekly = np.resize(y[-7:], horizon)
    mean = np.repeat(y[-28:].mean(), horizon)
    days = spec['calendar_ridge']['training_days']
    train = history.tail(days)
    origin_date = history.date.iloc[-1]
    x = design(train, origin_date, days)
    target = train.units.to_numpy(dtype=float)
    penalty = np.eye(x.shape[1]) * spec['calendar_ridge']['ridge_alpha']
    penalty[0, 0] = 0  # Intercept remains unpenalized.
    coefficients = np.linalg.solve(x.T @ x + penalty, x.T @ target)
    ridge = np.maximum(0, design(future, origin_date, days) @ coefficients)
    # No branch in the prediction code reads future.units.
    return future, dict(zip(MODELS, [weekly, mean, ridge]))


def score(frame):
    scores = []
    for (origin, model), group in frame.groupby(['origin', 'model']):
        total = float(group.actual.sum())
        error = (group.actual - group.prediction).abs()
        scores.append({'origin': int(origin), 'model': model,
            'mae': float(error.mean()), 'wape': float(error.sum() / total) if total else None,
            'bias': float((group.prediction - group.actual).mean()),
            'actual_units': total, 'observations': len(group)})
    return scores


def predict_windows(sales, origins, horizon, spec):
    predictions = []
    for item, group in sales.groupby('item_id'):
        for origin in origins:
            future, forecasts = forecast_at_origin(group, origin, horizon, spec)
            for model, values in forecasts.items():
                for day, actual, prediction in zip(future.day_number, future.units, values):
                    predictions.append({'item_id': item, 'origin': origin, 'day_number': int(day),
                                        'model': model, 'actual': float(actual), 'prediction': float(prediction)})
    frame = pd.DataFrame(predictions)
    frame['absolute_error'] = (frame.actual - frame.prediction).abs()
    return frame


def zero_run_profile(sales, cutoff):
    """Training-only diagnostics; zero sales do not identify inventory availability."""
    rows = []
    for item, group in sales[sales.day_number <= cutoff].groupby('item_id'):
        values = group.sort_values('day_number').units.to_numpy()
        longest = current = 0
        runs = 0
        for value in values:
            if value == 0:
                current += 1
                longest = max(longest, current)
            else:
                runs += current >= 28
                current = 0
        runs += current >= 28
        positive = np.flatnonzero(values > 0)
        rows.append({'item_id': item, 'zero_sales_share': float((values == 0).mean()),
            'longest_zero_run_days': longest, 'zero_runs_at_least_28_days': int(runs),
            'leading_zero_days': int(positive[0]) if len(positive) else len(values),
            'trailing_zero_days': int(len(values)-1-positive[-1]) if len(positive) else len(values)})
    return rows


def fingerprints(root):
    root = Path(root)
    cfg = json.loads((root / 'data/processed/build_config.json').read_text())
    paths = [root / 'config/forecasting.toml', root / 'data/processed/build_config.json',
             root / 'data/processed/daily_sales.parquet',
             root / cfg['data']['raw_directory'] / cfg['data']['calendar_file']]
    return {str(path.relative_to(root)): sha(path) for path in paths} | {
        'forecasting_code': sha(Path(__file__))}


def backtest(root):
    root = Path(root)
    out = root / 'data/processed'
    sales, cfg = load_sales(root)
    spec = tomllib.loads((root / 'config/forecasting.toml').read_text())
    if tuple(spec['selection']['candidates']) != MODELS or spec['selection']['metric'] != 'pooled_mae' or spec['selection']['tie_breaker'] != 'model_name_ascending':
        raise ValueError('Unsupported selection specification')
    ev = cfg['evaluation']
    initial, horizon = ev['initial_train_end_day'], ev['horizon_days']
    origins = [initial + fold * horizon for fold in range(ev['validation_windows'])]
    if origins[-1] + horizon != ev['final_holdout_start_day'] - 1:
        raise ValueError('Validation must end immediately before final holdout')
    frame = predict_windows(sales, origins, horizon, spec)
    metrics = score(frame)
    ranking = frame.groupby('model').absolute_error.mean().sort_index().sort_values(kind='stable')
    selection = {'metric': 'pooled_mae', 'tie_breaker': 'model_name_ascending',
        'selected_model': ranking.index[0], 'validation_mae': ranking.to_dict(),
        'validation_end_day': origins[-1] + horizon, 'fingerprints': fingerprints(root)}
    frame.to_parquet(out / 'validation_forecasts.parquet', index=False)
    (out / 'validation_metrics.json').write_text(json.dumps(metrics, indent=2, allow_nan=False))
    (out / 'forecast_selection.json').write_text(json.dumps(selection, indent=2, allow_nan=False))
    (out / 'zero_sales_diagnostics.json').write_text(json.dumps(zero_run_profile(sales, initial), indent=2))
    return metrics


def evaluate(root):
    root = Path(root)
    out = root / 'data/processed'
    # The tracked freeze must exist before any final-period outcomes are scored.
    freeze = json.loads((root / 'docs/FORECAST_SELECTION.json').read_text())
    if freeze['fingerprints'] != fingerprints(root):
        raise ValueError('Data, configuration or forecasting code differs from the frozen selection')
    sales, cfg = load_sales(root)
    ev = cfg['evaluation']
    if ev['final_holdout_end_day'] - ev['final_holdout_start_day'] + 1 != ev['horizon_days']:
        raise ValueError('Final holdout length must equal forecast horizon')
    frame = predict_windows(sales, [ev['final_holdout_start_day'] - 1], ev['horizon_days'],
        tomllib.loads((root / 'config/forecasting.toml').read_text()))
    metrics = score(frame)
    result = {'selected_model': freeze['selected_model'], 'selection_sha256': sha(root / 'docs/FORECAST_SELECTION.json'),
              'holdout_start_day': ev['final_holdout_start_day'], 'holdout_end_day': ev['final_holdout_end_day'],
              'metrics': metrics}
    frame.to_parquet(out / 'final_forecasts.parquet', index=False)
    (out / 'final_metrics.json').write_text(json.dumps(result, indent=2, allow_nan=False))
    return result
