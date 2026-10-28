"""Capture an engineering run without resuming it or supplying extra answers.

The browser storage-state file is private and is never copied into evidence.
This observer makes read-only API calls unless --bundle is explicitly selected;
the resulting project ZIP is a QA capture, not an extra model-generated design.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='http://127.0.0.1:18004')
    parser.add_argument('--state', default='data/qa/engineering-delivery/browser-auth.json')
    parser.add_argument('--project')
    parser.add_argument('--project-name')
    parser.add_argument('--run')
    parser.add_argument('--output', default='data/qa/engineering-delivery')
    parser.add_argument('--bundle', action='store_true')
    args = parser.parse_args()
    state = json.loads(Path(args.state).read_text(encoding='utf-8-sig'))
    cookies = httpx.Cookies()
    for item in state['cookies']:
        cookies.set(item['name'], item['value'], domain=item['domain'], path=item['path'])
    base = args.base.rstrip('/')
    with httpx.Client(base_url=base, cookies=cookies, timeout=90, follow_redirects=False) as client:
        def get(url):
            response = client.get(url)
            response.raise_for_status()
            return response.json()

        if args.run:
            run = get('/api/runs/' + args.run)
            project_id = run['project_id']
        else:
            projects = get('/api/projects')
            chosen = next((p for p in projects if p['id'] == args.project or
                           args.project_name and p['name'] == args.project_name), None)
            if not chosen:
                raise SystemExit('Specify an existing --project or exact --project-name')
            project_id = chosen['id']
            runs = get('/api/projects/' + project_id + '/runs')
            if not runs:
                artifacts = get('/api/projects/' + project_id + '/artifacts')
                print(json.dumps({'project_id': project_id, 'status': 'not_submitted',
                                  'artifacts': [{'id': a['id'], 'name': a['name']} for a in artifacts]}, ensure_ascii=False))
                return
            run = get('/api/runs/' + runs[0]['id'])
        run_id = run['id']
        folder = Path(args.output) / run_id
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

        def save(name, value):
            (folder / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

        save('run-' + stamp + '.json', run)
        save('run-latest.json', run)
        audit = get('/api/projects/' + project_id + '/engineering?include_values=true&run_id=' + run_id)
        artifacts = get('/api/projects/' + project_id + '/artifacts')
        save('engineering-latest.json', audit)
        save('artifacts-latest.json', artifacts)
        events = run['events']
        results = [e['payload'] for e in events if e['type'] == 'tool_result']
        summary = {
            'captured_at': stamp, 'project_id': project_id, 'run_id': run_id,
            'status': run['status'], 'iterations': run['result'].get('iterations', 0),
            'tool_calls': run['result'].get('tool_calls', 0),
            'active_seconds': run['result'].get('active_seconds', 0),
            'model': (audit.get('frozen_run') or {}).get('model'),
            'events': len(events), 'last_event': events[-1] if events else None,
            'tool_counts': dict(Counter(r['name'] for r in results)),
            'failed_tools': [{'name': r['name'], 'result': r.get('result')} for r in results if r.get('failed')],
            'objects': len(audit['objects']), 'deliverables': len(audit['deliverables']),
            'artifacts': [{'id': a['id'], 'name': a['name'], 'kind': a['kind']} for a in artifacts],
            'blocker_counts': dict(Counter(b['kind'] for b in audit['blockers'])),
            'engineering_ready': audit['ready'], 'extra_user_answers':
            sum(e['type'] in {'awaiting_user', 'resumed', 'tool_reconciled'} for e in events),
        }
        if args.bundle:
            if run['status'] in {'queued', 'running'}:
                raise SystemExit('Refusing a final QA bundle while the run is still live')
            response = client.post('/api/projects/' + project_id + '/bundle')
            response.raise_for_status()
            artifact = response.json()
            response = client.get(artifact['download_url'])
            response.raise_for_status()
            target = folder / 'final-project-qa-capture.zip'
            target.write_bytes(response.content)
            summary['qa_bundle'] = {'path': str(target), 'sha256': hashlib.sha256(response.content).hexdigest(),
                                    'origin': 'post-run QA API capture; not model-authored engineering content'}
        save('observation-latest.json', summary)
        # Full tool outputs are in the saved files; keep routine console observations small.
        printable = {**summary, 'last_event': {k: v for k, v in (summary['last_event'] or {}).items() if k != 'payload'}}
        print(json.dumps(printable, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
