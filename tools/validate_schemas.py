"""JSON Schema validation in CI, in addition to semantic checks."""
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

root = Path(__file__).resolve().parents[1]
for channel in ('preview', 'stable'):
    for filename, schema_name in ((f'{channel}.json', 'release-feed.schema.json'),
                                  (('versions.json' if channel == 'stable' else 'preview-versions.json'),
                                   'release-history.schema.json')):
        data = json.loads((root / 'site' / 'releases' / filename).read_text(encoding='utf-8'))
        schema = json.loads((root / 'schemas' / schema_name).read_text(encoding='utf-8'))
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(data)
        print(f'OK schema: {filename}')
