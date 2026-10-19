"""Export the simulation ledger and author native report definitions."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

import pandas as pd

SCHEMA = 'https://developer.microsoft.com/json-schemas/'
REPORT_SCHEMA = SCHEMA + 'fabric/item/report/'
COLUMNS = {
    'Ledger': {'scenario_id': 'string', 'policy': 'string', 'item_id': 'string',
               'date': 'dateTime', 'demand_proxy_units': 'int64', 'fulfilled_units': 'int64',
               'lost_units': 'int64', 'ending_stock': 'int64', 'ordered_units': 'int64'},
    'Scenario': {'scenario_id': 'string'},
    'Policy': {'policy': 'string'},
    'Product': {'item_id': 'string'},
    'Date': {'date': 'dateTime'},
}
MEASURES = {
    'Demand proxy units': ('SUM(Ledger[demand_proxy_units])', '#,0'),
    'Fulfilled units': ('SUM(Ledger[fulfilled_units])', '#,0'),
    'Unmet proxy units': ('SUM(Ledger[lost_units])', '#,0'),
    'Unit fill rate': ('DIVIDE(SUM(Ledger[fulfilled_units]), SUM(Ledger[demand_proxy_units]))', '0.00%'),
    'Average closing inventory': ('AVERAGEX(VALUES(\'Date\'[date]), CALCULATE(SUM(Ledger[ending_stock])))', '#,0.0'),
    'Ordered units': ('SUM(Ledger[ordered_units])', '#,0'),
}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def guarded_measure(expression):
    """Default to base scenario; suppress ambiguous scenario/policy totals."""
    return ("VAR ChosenScenario = SELECTEDVALUE(Scenario[scenario_id], "
            'IF(NOT ISFILTERED(Scenario[scenario_id]), "L7_R7_I14"))\n'
            'RETURN IF(NOT ISBLANK(ChosenScenario) && HASONEVALUE(Policy[policy]),\n'
            f'    CALCULATE({expression}, TREATAS({{ChosenScenario}}, Scenario[scenario_id])))')


def export_tables(ledger, destination):
    """Keep detailed data local; native definitions only contain metadata."""
    ledger = ledger[list(COLUMNS['Ledger'])].copy()
    keys = ['scenario_id', 'policy', 'item_id', 'date']
    if ledger.empty or ledger[keys].isna().any().any() or ledger.duplicated(keys).any():
        raise ValueError('Ledger must have non-null, unique scenario-policy-item-date keys')
    numeric = list(c for c, t in COLUMNS['Ledger'].items() if t == 'int64')
    if ledger[numeric].isna().any().any() or (ledger[numeric] < 0).any().any() or (ledger[numeric] % 1 != 0).any().any():
        raise ValueError('Inventory quantities must be non-negative integers')
    if (ledger['fulfilled_units'] + ledger['lost_units'] != ledger['demand_proxy_units']).any():
        raise ValueError('Demand accounting mismatch')
    tables = {'Ledger': ledger.sort_values(keys)}
    for name in ('Scenario', 'Policy', 'Product', 'Date'):
        cols = list(COLUMNS[name])
        tables[name] = ledger[cols].drop_duplicates().sort_values(cols)
    destination.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, frame in tables.items():
        path = destination / f'{name}.csv'
        frame.to_csv(path, index=False, date_format='%Y-%m-%d', lineterminator='\n')
        manifest[name] = {'rows': len(frame), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    write_json(destination / 'manifest.json', manifest)
    return manifest


def powerbi(root):
    folder = root / 'reports/powerbi'
    model_folder = folder / 'Inventory.SemanticModel'
    report = folder / 'Inventory.Report'
    write_json(folder / 'Inventory.pbip', {
        '$schema': SCHEMA + 'fabric/pbip/pbipProperties/1.0.0/schema.json',
        'version': '1.0', 'artifacts': [{'report': {'path': 'Inventory.Report'}}],
        'settings': {'enableAutoRecovery': True}})
    write_json(model_folder / 'definition.pbism', {
        '$schema': SCHEMA + 'fabric/item/semanticModel/definitionProperties/1.0.0/schema.json',
        'version': '1.0', 'settings': {}})
    tables = []
    for name, columns in COLUMNS.items():
        m_types = {'string': 'type text', 'int64': 'Int64.Type', 'dateTime': 'type date'}
        types = ', '.join('{"' + c + '", ' + m_types[t] + '}' for c, t in columns.items())
        expression = [
            'let',
            f'    Source = Csv.Document(File.Contents(DataFolder & "/{name}.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
            '    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
            '    Typed = Table.TransformColumnTypes(Headers, {' + types + '}, "en-US")',
            'in', '    Typed']
        table = {'name': name, 'columns': [
            {'name': c, 'dataType': t, 'sourceColumn': c, 'summarizeBy': 'none',
             'isHidden': name == 'Ledger'} for c, t in columns.items()],
            'partitions': [{'name': name, 'mode': 'import', 'source': {'type': 'm', 'expression': expression}}]}
        if name == 'Ledger':
            table['measures'] = [{'name': n, 'expression': guarded_measure(e), 'formatString': f}
                                 for n, (e, f) in MEASURES.items()]
        tables.append(table)
    write_json(model_folder / 'model.bim', {
        'name': 'Inventory', 'compatibilityLevel': 1601,
        'model': {'culture': 'en-US', 'defaultPowerBIDataSourceVersion': 'powerBI_V3',
                  'expressions': [{'name': 'DataFolder', 'kind': 'm',
                      'expression': '"C:/inventory-data/native" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'}],
                  'tables': tables,
                  'relationships': [{'name': 'Ledger_' + n, 'fromTable': 'Ledger', 'fromColumn': next(iter(COLUMNS[n])),
                      'toTable': n, 'toColumn': next(iter(COLUMNS[n])), 'crossFilteringBehavior': 'oneDirection'}
                      for n in ('Scenario', 'Policy', 'Product', 'Date')]}})
    write_json(report / 'definition.pbir', {'$schema': REPORT_SCHEMA + 'definitionProperties/2.0.0/schema.json',
        'version': '4.0', 'datasetReference': {'byPath': {'path': '../Inventory.SemanticModel'}}})
    definition = report / 'definition'
    write_json(definition / 'version.json', {'$schema': REPORT_SCHEMA + 'definition/versionMetadata/1.0.0/schema.json', 'version': '2.0.0'})
    write_json(definition / 'report.json', {'$schema': REPORT_SCHEMA + 'definition/report/2.0.0/schema.json',
        'themeCollection': {}, 'settings': {'defaultFilterActionIsDataFilter': True}})
    write_json(definition / 'pages/pages.json', {'$schema': REPORT_SCHEMA + 'definition/pagesMetadata/1.0.0/schema.json',
        'pageOrder': ['PolicyComparison', 'ProductExceptions'], 'activePageName': 'PolicyComparison'})
    def field(table, column, measure=False):
        return {'field': {'Measure' if measure else 'Column': {'Expression': {'SourceRef': {'Entity': table}}, 'Property': column}},
                'queryRef': table + '.' + column}
    def visual(page, name, kind, x, y, w, h, roles):
        write_json(definition / f'pages/{page}/visuals/{name}/visual.json', {
            '$schema': REPORT_SCHEMA + 'definition/visualContainer/2.1.0/schema.json', 'name': name,
            'position': {'x': x, 'y': y, 'width': w, 'height': h, 'z': 0, 'tabOrder': y + x},
            'visual': {'visualType': kind, 'query': {'queryState': {
                role: {'projections': values} for role, values in roles.items()}}}})
    for page, title in [('PolicyComparison', 'Inventory policy comparison | simulated sales replay'),
                        ('ProductExceptions', 'Product service exceptions | simulated sales replay')]:
        write_json(definition / f'pages/{page}/page.json', {
            '$schema': REPORT_SCHEMA + 'definition/page/1.0.0/schema.json',
            'name': page, 'displayName': title, 'displayOption': 'FitToPage', 'width': 1280, 'height': 720})
        visual(page, 'ScenarioSelection', 'slicer', 24, 16, 380, 120, {'Values': [field('Scenario', 'scenario_id')]})
        visual(page, 'ProductSelection', 'slicer', 430, 16, 826, 120, {'Values': [field('Product', 'item_id')]})
    visual('PolicyComparison', 'PolicyMetrics', 'tableEx', 24, 160, 1232, 200, {'Values': [field('Policy', 'policy')] + [
        field('Ledger', n, True) for n in ['Unit fill rate', 'Average closing inventory', 'Unmet proxy units', 'Ordered units']]})
    visual('PolicyComparison', 'InventoryTrend', 'lineChart', 24, 390, 1232, 300, {
        'Category': [field('Date', 'date')], 'Series': [field('Policy', 'policy')],
        'Y': [field('Ledger', 'Average closing inventory', True)]})
    visual('ProductExceptions', 'ProductMetrics', 'tableEx', 24, 160, 1232, 530, {'Values': [
        field('Product', 'item_id'), field('Policy', 'policy')] + [field('Ledger', n, True)
        for n in ['Demand proxy units', 'Unit fill rate', 'Unmet proxy units', 'Average closing inventory']]})


RDL_NS = 'http://schemas.microsoft.com/sqlserver/reporting/2016/01/reportdefinition'
ET.register_namespace('', RDL_NS)


def paginated(root):
    def element(parent, name, text=None, **attrs):
        child = ET.SubElement(parent, '{' + RDL_NS + '}' + name, attrs)
        if text is not None:
            child.text = str(text)
        return child
    report = ET.Element('{' + RDL_NS + '}Report')
    element(report, 'Description', 'Simulated inventory exceptions. Historical fulfilled sales proxy demand; all inventory inputs are hypothetical.')
    sources = element(report, 'DataSources')
    properties = element(element(sources, 'DataSource', Name='InventoryModel'), 'ConnectionProperties')
    element(properties, 'DataProvider', 'PBIDATASET')
    element(properties, 'ConnectString', 'Data Source=pbiazure://api.powerbi.com/;Initial Catalog=sobe_wowvirtualserver-SEMANTIC_MODEL_ID;Integrated Security=ClaimsToken')
    parameters = element(report, 'ReportParameters')
    for name, default, values in [
        ('Scenario', 'L7_R7_I14', [f'L{l}_R7_I{i}' for l in [3,7,14] for i in [7,14,28]]),
        ('Policy', 'order_up_to', ['fixed_cover','order_up_to'])]:
        param = element(parameters, 'ReportParameter', Name=name)
        element(param, 'DataType', 'String')
        element(element(element(param, 'DefaultValue'), 'Values'), 'Value', default)
        element(param, 'Prompt', name)
        valid = element(element(param, 'ValidValues'), 'ParameterValues')
        for value in values:
            element(element(valid, 'ParameterValue'), 'Value', value)
    fields = [('Item', 'String'), ('Demand', 'Int64'), ('Unmet', 'Int64'), ('Fill', 'Double'), ('Stock', 'Double')]
    datasets = element(report, 'DataSets')
    dataset = element(datasets, 'DataSet', Name='Exceptions')
    query = element(dataset, 'Query')
    element(query, 'DataSourceName', 'InventoryModel')
    qparams = element(query, 'QueryParameters')
    for name in ['Scenario', 'Policy']:
        element(element(qparams, 'QueryParameter', Name=name), 'Value', f'=Parameters!{name}.Value')
    dax = '''EVALUATE
VAR Products = SUMMARIZECOLUMNS(
    Product[item_id],
    TREATAS({@Scenario}, Scenario[scenario_id]),
    TREATAS({@Policy}, Policy[policy]),
    "Demand", [Demand proxy units], "Unmet", [Unmet proxy units],
    "Fill", [Unit fill rate], "Stock", [Average closing inventory])
RETURN SELECTCOLUMNS(FILTER(Products, [Unmet] > 0),
    "Item", Product[item_id], "Demand", [Demand], "Unmet", [Unmet], "Fill", [Fill], "Stock", [Stock])
ORDER BY [Unmet] DESC, [Item] ASC'''
    element(query, 'CommandText', dax)
    field_nodes = element(dataset, 'Fields')
    for name, _ in fields:
        element(element(field_nodes, 'Field', Name=name), 'DataField', '[' + name + ']')
    sections = element(report, 'ReportSections')
    section = element(sections, 'ReportSection')
    body = element(section, 'Body')
    items = element(body, 'ReportItems')
    def textbox(parent, name, value, header=False):
        box = element(parent, 'Textbox', Name=name)
        element(box, 'CanGrow', 'true')
        p = element(element(box, 'Paragraphs'), 'Paragraph')
        run = element(element(p, 'TextRuns'), 'TextRun')
        element(run, 'Value', value)
        style = element(run, 'Style')
        element(style, 'FontSize', '10pt')
        if header:
            element(style, 'FontWeight', 'Bold')
        style = element(box, 'Style')
        element(style, 'PaddingLeft', '4pt'); element(style, 'PaddingTop', '3pt')
        return box
    title = textbox(items, 'Title', 'Inventory exception report', True)
    for n, v in [('Top','0in'),('Left','0in'),('Height','0.3in'),('Width','7.2in')]: element(title,n,v)
    subtitle = textbox(items, 'Scope', '=Parameters!Scenario.Value & " | " & Parameters!Policy.Value & " | products with unmet proxy units > 0"')
    for n, v in [('Top','0.35in'),('Left','0in'),('Height','0.3in'),('Width','7.2in')]: element(subtitle,n,v)
    note = textbox(items, 'Caveat', 'Retrospective sales replay, 25 Apr–22 May 2016. Hypothetical inventory inputs. Unmet units are simulated; selling prices do not establish profit.')
    for n, v in [('Top','0.7in'),('Left','0in'),('Height','0.45in'),('Width','7.2in')]: element(note,n,v)
    table = element(items, 'Tablix', Name='ExceptionList')
    tb = element(table, 'TablixBody')
    columns = element(tb, 'TablixColumns')
    for width in ['2in','1.2in','1.2in','1.2in','1.6in']:
        element(element(columns, 'TablixColumn'), 'Width', width)
    rows = element(tb, 'TablixRows')
    for row_index in range(2):
        row = element(rows, 'TablixRow'); element(row, 'Height', '0.3in')
        cells = element(row, 'TablixCells')
        for (name, typ), label in zip(fields, ['Product','Sales proxy','Unmet units','Unit fill','Avg stock']):
            cell = element(element(cells, 'TablixCell'), 'CellContents')
            value = label if row_index == 0 else f'=Fields!{name}.Value'
            box = textbox(cell, f'{name}_{row_index}', value, row_index == 0)
            if row_index == 1 and typ != 'String':
                element(box.find('{' + RDL_NS + '}Style'), 'Format', 'P2' if name == 'Fill' else ('N1' if name == 'Stock' else 'N0'))
    members = element(element(table, 'TablixColumnHierarchy'), 'TablixMembers')
    for _ in fields: element(members, 'TablixMember')
    members = element(element(table, 'TablixRowHierarchy'), 'TablixMembers')
    header = element(members, 'TablixMember')
    element(header, 'KeepWithGroup', 'After'); element(header, 'RepeatOnNewPage', 'true')
    detail = element(members, 'TablixMember'); element(detail, 'Group', Name='DetailRows')
    element(table, 'DataSetName', 'Exceptions')
    element(table, 'NoRowsMessage', 'No products with simulated unmet units for this selection.')
    for n,v in [('Top','1.3in'),('Left','0in'),('Height','0.6in'),('Width','7.2in')]: element(table,n,v)
    element(body, 'Height', '2in'); element(section, 'Width', '7.2in')
    page = element(section, 'Page')
    footer = element(page, 'PageFooter'); element(footer, 'Height','0.3in')
    footer_items = element(footer, 'ReportItems')
    number = textbox(footer_items, 'PageNumber', '= "Page " & Globals!PageNumber & " of " & Globals!TotalPages')
    for n,v in [('Top','0in'),('Left','0in'),('Height','0.3in'),('Width','7.2in')]: element(number,n,v)
    for n,v in [('PageHeight','11.7in'),('PageWidth','8.3in'),('LeftMargin','0.5in'),('RightMargin','0.5in'),('TopMargin','0.5in'),('BottomMargin','0.5in')]: element(page,n,v)
    element(report, 'Language','en-US')
    ET.indent(report, space='  ')
    path = root / 'reports/paginated/InventoryExceptions.rdl'
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(report).write(path, encoding='utf-8', xml_declaration=True)


def reconcile_exports(root):
    """Compare the actual CSV bytes' metrics with the published simulation."""
    ledger = pd.read_csv(root / 'data/processed/native/Ledger.csv')
    expected = json.loads((root / 'docs/SIMULATION_RESULTS.json').read_text())['results']
    expected_keys = {(row['scenario_id'], row['policy']) for row in expected}
    actual_keys = set(ledger[['scenario_id', 'policy']].itertuples(index=False, name=None))
    if actual_keys != expected_keys:
        raise ValueError('Exported scenario-policy coverage differs from published results')
    results = []
    for row in expected:
        group = ledger[(ledger.scenario_id == row['scenario_id']) & (ledger.policy == row['policy'])]
        fill = float(group.fulfilled_units.sum() / group.demand_proxy_units.sum())
        stock = float(group.groupby('date').ending_stock.sum().mean())
        unmet = int(group.lost_units.sum())
        if abs(fill - row['unit_fill_rate']) > 1e-12 or abs(stock - row['average_ending_inventory']) > 1e-10 or unmet != row['lost_units']:
            raise ValueError('Native export reconciliation failed: ' + row['scenario_id'] + '/' + row['policy'])
        results.append({'scenario_id': row['scenario_id'], 'policy': row['policy'],
                        'unit_fill_rate': fill, 'average_closing_inventory': stock, 'unmet_proxy_units': unmet})
    write_json(root / 'outputs/native_reconciliation.json', results)
    return results


def build(root):
    manifest = export_tables(pd.read_parquet(root / 'data/processed/simulation_daily.parquet'), root / 'data/processed/native')
    reconcile_exports(root)
    powerbi(root)
    paginated(root)
    return manifest
