"""Read-only, per-requirement acceptance gate for a frozen competition project ZIP."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.competition import GLOBAL_SOURCE_EXCERPTS, REQUIREMENTS, SOURCE_EXCERPTS


def norm(value):
    return re.sub(r"\s+", "", str(value or ""))


def digest(content):
    return hashlib.sha256(content).hexdigest()


def _file_bytes(archive, name):
    try:
        return archive.read(name)
    except KeyError:
        return None


def _walk_generated(value, found):
    if isinstance(value, dict):
        ident = value.get('id')
        if ident and (value.get('download_url') or value.get('preview_url')):
            found.add(ident)
        for child in value.values():
            _walk_generated(child, found)
    elif isinstance(value, list):
        for child in value:
            _walk_generated(child, found)


def _check_source(archive, snapshots, artifacts, runs, requirement):
    source = requirement.get('source')
    if not isinstance(source, dict) or not source.get('quote') or not source.get('source_sha256'):
        return False, '缺少原文引句/哈希绑定'
    if source.get('source_kind') == 'user_request':
        run_id = source.get('source_run_id')
        frozen = runs.get(run_id)
        if not frozen:
            return False, '用户请求来源不在冻结运行中'
        message = frozen.get('snapshot', {}).get('request', {}).get('message', '')
        return (digest(message.encode()) == source['source_sha256'] and source['quote'] in message,
                '用户请求哈希或引句不匹配')
    snapshot = snapshots.get(source.get('snapshot_id'))
    if not snapshot:
        return False, '要求引用的原文快照不存在'
    artifact_id = source.get('artifact_id')
    artifact = artifacts.get(artifact_id)
    if not artifact or artifact_id != snapshot.get('artifact_id'):
        return False, '要求来源原件不一致'
    if source['source_sha256'] != snapshot.get('source_sha256') or source['source_sha256'] != artifact.get('metadata', {}).get('sha256'):
        return False, '要求来源原件哈希不匹配'
    raw = _file_bytes(archive, 'files/' + artifact_id + '/' + artifact['name'])
    if raw is None or digest(raw) != source['source_sha256']:
        return False, '要求来源原件不在成果包或字节哈希变化'
    if digest(snapshot['content'].encode()) != snapshot.get('content_sha256'):
        return False, '要求全文快照内容哈希不匹配'
    try:
        content = json.loads(snapshot['content'])
    except (KeyError, TypeError, json.JSONDecodeError):
        return False, '原文快照不可解析'
    block = next((block for block in content.get('blocks', []) if block.get('id') == source.get('block_id')),
                 None)
    return (bool(block and norm(source['quote']) in norm(block.get('text'))), '要求引句不在指定快照段落中')


def evaluate_bundle(bundle_path):
    bundle_path = Path(bundle_path)
    with zipfile.ZipFile(bundle_path) as archive:
        manifest = json.loads(archive.read('manifest.json'))
        engineering = manifest.get('engineering', {})
        requirement_rows = {item['code']: item for item in engineering.get('requirements', [])}
        deliverables = {item['key']: item for item in engineering.get('deliverables', [])}
        artifacts = {item['id']: item for item in manifest.get('artifacts', [])}
        snapshots = {item['id']: item for item in manifest.get('document_snapshots', [])}
        runs = {item['run_id']: item for item in manifest.get('frozen_runs', [])}
        run_id = engineering.get('frozen_run', {}).get('run_id')
        frozen_run = runs.get(run_id, {})
        input_ids = {item['id'] for item in frozen_run.get('snapshot', {}).get('inputs', [])}
        tool_results = []
        for event_row in manifest.get('events', []):
            if event_row.get('run_id') != run_id or event_row.get('type') != 'tool_result':
                continue
            try:
                tool_results.append(json.loads(event_row['payload']))
            except (KeyError, TypeError, json.JSONDecodeError):
                pass
        generated = set()
        for result in tool_results:
            if not result.get('failed'):
                _walk_generated(result.get('result'), generated)
        resumed = any(event.get('run_id') == run_id and event.get('type') in
                      {'awaiting_user', 'resumed', 'tool_reconciled'} for event in manifest.get('events', []))
        source_pdf = next((item for item in manifest.get('artifacts', []) if item.get('name') == '26化工设计大赛题目.pdf'), None)
        pdf_bytes = _file_bytes(archive, 'files/' + source_pdf['id'] + '/' + source_pdf['name']) if source_pdf else None
        source_pdf_ok = bool(pdf_bytes and digest(pdf_bytes) == source_pdf.get('metadata', {}).get('sha256'))
        pdf_text = ''
        if source_pdf_ok:
            from pypdf import PdfReader
            import io
            pdf_text = norm('\n'.join(page.extract_text() or '' for page in PdfReader(io.BytesIO(pdf_bytes)).pages))
        exact_source_gates = source_pdf_ok and all(norm(fragment) in pdf_text for group in SOURCE_EXCERPTS.values() for fragment in group)
        global_gates = source_pdf_ok and all(norm(fragment) in pdf_text for fragment in GLOBAL_SOURCE_EXCERPTS)
        rows = []
        blocker_rows = engineering.get('blockers', [])
        for code, title, page, mandatory in REQUIREMENTS:
            item = requirement_rows.get(code)
            reasons = []
            if not item:
                source_ok, source_detail = False, '验收快照缺少此要求编码'
                mapped = []
                files_ok = False
                review = 'missing'
                related = []
            else:
                source_ok, source_detail = _check_source(archive, snapshots, artifacts, runs, item)
                mapped = item.get('deliverables', [])
                review = item.get('professional_review', 'missing')
                related = [deliverables[key] for key in mapped if key in deliverables]
                if not mapped or len(related) != len(mapped):
                    reasons.append('未映射到可追溯的现有成果')
                files_ok = bool(related) and all(d.get('files_checked') and not d.get('issues') for d in related)
                if not files_ok:
                    reasons.append('原件/格式/内容自动校验未通过')
                if not source_ok:
                    reasons.append(source_detail)
            related_keys = set(mapped)
            item_blockers = [b for b in blocker_rows if b.get('key') == code or b.get('key') in related_keys]
            if item_blockers:
                reasons.extend(issue for blocker in item_blockers for issue in blocker.get('issues', []))
            linked_artifacts = {f.get('artifact_id') for d in related for f in d.get('data', {}).get('files', [])}
            bad_hashes = []
            for ident in linked_artifacts:
                record = artifacts.get(ident)
                if not record:
                    bad_hashes.append(str(ident) + ':missing-manifest-record')
                    continue
                content = _file_bytes(archive, 'files/' + ident + '/' + record['name'])
                expected = record.get('metadata', {}).get('sha256')
                if content is None or not expected or digest(content) != expected:
                    bad_hashes.append(str(ident) + ':missing-or-changed-bytes')
            hashes_ok = not bad_hashes
            if not hashes_ok:
                reasons.append('文件包字节哈希不匹配')
            autonomous_ok = bool(linked_artifacts) and linked_artifacts <= generated and not (linked_artifacts & input_ids)
            if not autonomous_ok:
                reasons.append('成果未被本次成功工具轨迹证明为新生成')
            if resumed:
                reasons.append('运行依赖追问、恢复或人工处置')
            if review != 'verified':
                reasons.append('专业审核未通过，不得以文件或工具成功替代')
            global_blockers=[b for b in blocker_rows if b.get('kind') in
                             {'frozen_archive','frozen_input','frozen_platform','single_input','engineering_data'}]
            reasons.extend(issue for blocker in global_blockers for issue in blocker.get('issues', []))
            gate_ok = bool(item and source_ok and mapped and files_ok and hashes_ok and autonomous_ok and not resumed
                           and review == 'verified' and not item_blockers and not global_blockers)
            rows.append({
                'code': code, 'title': title, 'mandatory': mandatory, 'source_page': page,
                'source_traceability': 'pass' if source_ok else 'fail', 'deliverable_mapping': mapped,
                'automatic_file_checks': 'pass' if files_ok else 'fail', 'artifact_hashes': 'pass' if hashes_ok else 'fail',
                'autonomous_origin': 'pass' if autonomous_ok else 'fail',
                'professional_review': review, 'gate': 'pass' if gate_ok else 'fail',
                'reasons': list(dict.fromkeys(reasons)),
            })
        missing_codes = sorted(set(code for code, _, _, _ in REQUIREMENTS) - set(requirement_rows))
        passed = sum(row['gate'] == 'pass' for row in rows)
        return {
            'run_id': run_id, 'run_status': next((run.get('status') for run in manifest.get('runs', []) if run.get('id') == run_id), None),
            'source_pdf_sha256': digest(pdf_bytes) if pdf_bytes else None,
            'source_pdf_bytes_and_all_35_exact_quotes': bool(source_pdf_ok and exact_source_gates),
            'global_output_constraints_in_original_pdf': bool(source_pdf_ok and global_gates),
            'registered_requirement_count': len(requirement_rows), 'expected_requirement_count': len(REQUIREMENTS),
            'missing_codes': missing_codes, 'item_gate_passed': passed, 'item_gate_total': len(rows),
            'one_conversation_allowed': bool(passed == len(REQUIREMENTS) and exact_source_gates and global_gates),
            'professional_review_is_separate': True,
            'requirements': rows,
            'scope': 'Read-only item audit: source quote/hash, deliverable mapping, recorded automatic file checks, packaged bytes, successful tool origin, and single-input events. It does not independently prove engineering correctness or expert approval.',
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', type=Path, required=True, help='Frozen project delivery ZIP containing manifest.json and files/')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = evaluate_bundle(args.bundle)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'requirements'}, ensure_ascii=False, indent=2))
    for item in result['requirements']:
        if item['gate'] != 'pass':
            print(item['code'] + ' FAIL: ' + '; '.join(item['reasons']))
    return 0 if result['one_conversation_allowed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
