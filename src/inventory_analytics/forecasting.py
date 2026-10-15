"""Validation-only demand forecasting; final holdout remains untouched."""
import json
from pathlib import Path
import duckdb
import pandas as pd


def backtest(root):
    root = Path(root)
    processed = root / 'data/processed'
    cfg = json.loads((processed / 'build_config.json').read_text())
    evaluation = cfg['evaluation']
    horizon = evaluation['horizon_days']
    initial = evaluation['initial_train_end_day']
    windows = evaluation['validation_windows']
    if initial + windows * horizon >= evaluation['final_holdout_start_day']:
        raise ValueError('Validation periods overlap final holdout')
    with duckdb.connect() as con:
        sales = con.execute('SELECT item_id, day_number, units FROM read_parquet(?) ORDER BY item_id, day_number',
                            [str(processed / 'daily_sales.parquet')]).df()
    predictions=[]
    for item, group in sales.groupby('item_id'):
        history = dict(zip(group.day_number, group.units))
        for fold in range(windows):
            origin = initial + fold * horizon
            # Both forecasts use only the data available at their common origin.
            weekly = [history[origin - 6 + offset] for offset in range(7)]
            mean28 = sum(history[d] for d in range(origin-27, origin+1))/28
            for step in range(1, horizon+1):
                day=origin+step
                actual=history[day]
                for model, prediction in [('seasonal_naive_7', weekly[(step-1)%7]), ('mean_28', mean28)]:
                    predictions.append({'item_id':item,'origin':origin,'day_number':day,
                        'model':model,'actual':actual,'prediction':prediction})
    frame=pd.DataFrame(predictions)
    frame['absolute_error']=(frame.actual-frame.prediction).abs()
    scores=[]
    for (origin, model), group in frame.groupby(['origin','model']):
        total=float(group.actual.sum())
        scores.append({'origin':int(origin),'model':model,'mae':float(group.absolute_error.mean()),
            'wape':float(group.absolute_error.sum()/total) if total else None,
            'actual_units':total,'observations':len(group)})
    frame.to_parquet(processed/'validation_forecasts.parquet',index=False)
    (processed/'validation_metrics.json').write_text(json.dumps(scores,indent=2,allow_nan=False))
    return scores
