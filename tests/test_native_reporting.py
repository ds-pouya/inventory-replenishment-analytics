"""Native reporting contracts using synthetic inventory observations."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from inventory_analytics.native_reporting import COLUMNS, RDL_NS, export_tables, paginated, powerbi


class NativeReportingTests(unittest.TestCase):
    def ledger(self):
        rows = []
        for item, demand, fulfilled, stock in [('A', 10, 9, 2), ('B', 100, 50, 30)]:
            for day in ['2020-01-01', '2020-01-02']:
                rows.append({'scenario_id': 'L7_R7_I14', 'policy': 'fixed_cover', 'item_id': item,
                             'date': pd.Timestamp(day), 'demand_proxy_units': demand,
                             'fulfilled_units': fulfilled, 'lost_units': demand - fulfilled,
                             'ending_stock': stock, 'ordered_units': 0})
        return pd.DataFrame(rows)

    def test_exports_preserve_grain_dates_and_weighted_metrics(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            manifest = export_tables(self.ledger(), destination)
            actual = pd.read_csv(destination / 'Ledger.csv')
            self.assertEqual(manifest['Ledger']['rows'], 4)
            self.assertEqual(manifest['Product']['rows'], 2)
            self.assertEqual(actual['date'].iloc[0], '2020-01-01')
            self.assertAlmostEqual(actual.fulfilled_units.sum() / actual.demand_proxy_units.sum(), 59 / 110)
            self.assertEqual(actual.groupby('date').ending_stock.sum().mean(), 32)
            # Row ordering must not change exported bytes or file hashes.
            self.assertEqual(manifest, export_tables(self.ledger().iloc[::-1], destination))

    def test_duplicate_and_unbalanced_rows_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = self.ledger()
            with self.assertRaises(ValueError):
                export_tables(pd.concat([ledger, ledger.iloc[[0]]]), Path(directory))
            for invalid in [-1, 1.5, float('nan')]:
                invalid_ledger = self.ledger()
                invalid_ledger.loc[0, 'ending_stock'] = invalid
                with self.assertRaises(ValueError):
                    export_tables(invalid_ledger, Path(directory))
            ledger.loc[0, 'lost_units'] = 100
            with self.assertRaises(ValueError):
                export_tables(ledger, Path(directory))

    def test_native_model_and_visual_bindings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            powerbi(root)
            folder = root / 'reports/powerbi'
            database = json.loads((folder / 'Inventory.SemanticModel/model.bim').read_text())
            tables = {t['name']: t for t in database['model']['tables']}
            self.assertEqual(set(tables), set(COLUMNS))
            self.assertEqual(len(database['model']['relationships']), 4)
            measures = {m['name'] for m in tables['Ledger']['measures']}
            for path in folder.rglob('visual.json'):
                document = json.loads(path.read_text())
                for role in document['visual']['query']['queryState'].values():
                    for projection in role['projections']:
                        kind, binding = next(iter(projection['field'].items()))
                        entity = binding['Expression']['SourceRef']['Entity']
                        valid = measures if kind == 'Measure' else COLUMNS[entity]
                        self.assertIn(binding['Property'], valid)
            for measure in tables['Ledger']['measures']:
                self.assertIn('HASONEVALUE(Policy[policy])', measure['expression'])
                self.assertIn('TREATAS({ChosenScenario}', measure['expression'])
            self.assertEqual(len(list(folder.rglob('visual.json'))), 7)

    def test_rdl_fields_parameters_pagination_and_no_embedded_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paginated(root)
            tree = ET.parse(root / 'reports/paginated/InventoryExceptions.rdl')
            ns = {'r': RDL_NS}
            self.assertEqual(len(tree.findall('.//r:ReportParameter', ns)), 2)
            self.assertEqual(len(tree.findall('.//r:Field', ns)), 5)
            query = tree.find('.//r:CommandText', ns).text
            self.assertIn('FILTER(Products, [Unmet] > 0)', query)
            self.assertIn('ORDER BY [Unmet] DESC, [Item] ASC', query)
            self.assertEqual(tree.find('.//r:RepeatOnNewPage', ns).text, 'true')
            self.assertIsNone(tree.find('.//r:XmlData', ns))
            page = tree.find('.//r:Page', ns)
            width = lambda tag: float(page.find('r:' + tag, ns).text.removesuffix('in'))
            self.assertGreaterEqual(width('PageWidth') - width('LeftMargin') - width('RightMargin'), 7.2)


if __name__ == '__main__':
    unittest.main()
