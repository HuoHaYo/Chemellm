import json
import zipfile

from app.competition import REQUIREMENTS
from scripts.competition_item_gate import evaluate_bundle


def test_missing_evidence_fails_every_item_instead_of_vacuous_ready(tmp_path):
    bundle = tmp_path / 'empty-project.zip'
    manifest = {
        'engineering': {
            'requirements': [{'code': code, 'title': title, 'mandatory': mandatory,
                              'deliverables': ['planned'], 'files_checked': True,
                              'professional_review': 'not_reviewed'}
                             for code, title, _, mandatory in REQUIREMENTS],
            'deliverables': [{'key': 'planned', 'files_checked': True, 'issues': [],
                              'data': {'files': [], 'requirement_codes': [item[0] for item in REQUIREMENTS]}}],
            'blockers': [], 'frozen_run': {'run_id': 'missing-run'},
        },
        'artifacts': [], 'document_snapshots': [], 'frozen_runs': [], 'events': [], 'runs': [],
    }
    with zipfile.ZipFile(bundle, 'w') as archive:
        archive.writestr('manifest.json', json.dumps(manifest))
    report = evaluate_bundle(bundle)
    assert report['registered_requirement_count'] == 35
    assert report['source_pdf_bytes_and_all_35_exact_quotes'] is False
    assert report['item_gate_passed'] == 0 and report['item_gate_total'] == 35
    assert report['one_conversation_allowed'] is False
    assert {row['gate'] for row in report['requirements']} == {'fail'}


def test_per_item_ledger_contains_all_required_and_conditional_codes():
    assert sum(row[3] for row in REQUIREMENTS) == 31
    assert sum(not row[3] for row in REQUIREMENTS) == 4
