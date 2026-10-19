"""Validate PBIR JSON schemas and RDL XSD; this does not execute reports."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import urllib.request

from jsonschema import Draft7Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
RDL_SCHEMA = 'https://raw.githubusercontent.com/microsoft/RdlMigration/master/RdlMigration.UnitTest/reportdefinition.xsd'


def validate(root, cache):
    cache.mkdir(parents=True, exist_ok=True)
    sources = {}
    def fetch(uri):
        if not (uri.startswith('https://developer.microsoft.com/json-schemas/') or uri == RDL_SCHEMA):
            raise ValueError('Unexpected schema location: ' + uri)
        path = cache / hashlib.sha256(uri.encode()).hexdigest()
        if not path.exists():
            with urllib.request.urlopen(uri, timeout=30) as response:
                path.write_bytes(response.read())
        sources[uri] = hashlib.sha256(path.read_bytes()).hexdigest()
        return path
    def retrieve(uri):
        return Resource.from_contents(json.loads(fetch(uri).read_text()))
    registry = Registry(retrieve=retrieve)
    count = 0
    for path in sorted((root / 'reports/powerbi').rglob('*')):
        if path.suffix not in {'.json', '.pbip', '.pbir', '.pbism'} or '.pbi' in path.parts:
            continue
        document = json.loads(path.read_text())
        if '$schema' not in document:
            continue  # model.bim is engine metadata, not PBIR JSON.
        schema_url = document['$schema']
        schema = json.loads(fetch(schema_url).read_text())
        validator = Draft7Validator(schema, registry=registry)
        errors = sorted(validator.iter_errors(document), key=lambda e: str(e.path))
        if errors:
            raise ValueError(str(path.relative_to(root)) + ': ' + '; '.join(e.message for e in errors))
        count += 1
    subprocess.run(['xmllint', '--nonet', '--noout', '--schema', str(fetch(RDL_SCHEMA)),
                    str(root / 'reports/paginated/InventoryExceptions.rdl')], check=True)
    result = {'pbir_json_documents_validated': count, 'rdl_xsd': 'passed',
              'model_engine_validation': 'pending', 'refresh_and_render': 'pending', 'schema_sha256': sources}
    destination = root / 'outputs/native_schema_validation.json'
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=ROOT / 'outputs/schema-cache')
    args = parser.parse_args()
    result = validate(ROOT, args.cache)
    print(f"Validated {result['pbir_json_documents_validated']} JSON documents and RDL XSD. Runtime checks remain pending.")
