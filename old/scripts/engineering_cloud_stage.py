"""Stage additive engineering QA beside the original service, never replace its data.

Run on the existing Linux host: python3 engineering_cloud_stage.py SOURCE.zip
Credentials are read in memory from the existing container and saved only in a
0600 QA env file on the host. They are never printed or copied into evidence.
"""
import hashlib
import argparse
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT=Path('/opt/chemellm-engineering-qa/20261021')
NAME='chemellm-engineering-20261021'
ORIGINAL='chemellm-linux-qa-chemellm-1'


def command(*args):
    return subprocess.check_output(list(args),universal_newlines=True).strip()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--label', default='20261021', help='Unique lowercase letters/digits/hyphens; existing deployments are never overwritten')
    parser.add_argument('--port', type=int, default=18004)
    options=parser.parse_args()
    if not re.fullmatch('[a-z0-9][a-z0-9-]{3,48}', options.label) or not 18000 <= options.port <= 18999:
        raise SystemExit('Invalid QA label or loopback port')
    root=Path('/opt/chemellm-engineering-qa')/options.label
    name='chemellm-engineering-'+options.label
    # All mutations stay under the new isolated QA root. Existing source and
    # data directories cause an immediate refusal, including partial staging.
    if root.exists():
        raise SystemExit('Refusing to reuse an existing QA root')
    root.mkdir(parents=True)
    before=json.loads(command('docker','inspect',ORIGINAL))[0]
    source=options.source.resolve()
    target=root/'source'
    if target.exists():
        raise SystemExit('Refusing to overwrite an existing frozen QA source')
    with zipfile.ZipFile(source) as archive:
        for info in archive.infolist():
            resolved=(target/info.filename).resolve()
            if resolved != target.resolve() and target.resolve() not in resolved.parents:
                raise SystemExit('Invalid archive member')
        archive.extractall(target)
    runtime=target/'chemellm'
    for relative,expected in json.loads((runtime/'SHA256SUMS.json').read_text()).items():
        assert hashlib.sha256((runtime/relative).read_bytes()).hexdigest()==expected,relative
    data=root/'data'
    data.mkdir()
    os.chown(data,10001,10001)
    env=dict(item.split('=',1) for item in before['Config']['Env'] if '=' in item)
    preserved={key:value for key,value in env.items() if key.startswith(('MODEL_','OLLAMA_','CHEMELLM_AUTH_'))}
    assert preserved['MODEL_BALANCED']=='deepseek-flash'
    preserved.update(CHEMELLM_DATA_DIR='/app/data',MAX_AGENT_ITERATIONS='8',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
    secret_file=root/'qa.env'
    descriptor=os.open(secret_file,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(descriptor,'w') as handle:
        handle.write('\n'.join(k+'='+v for k,v in preserved.items())+'\n')
    args=['docker','run','-d','--name',name,'--memory','650m','--memory-swap','1200m','--cpus','1','--env-file',str(secret_file),
          '-p','127.0.0.1:'+str(options.port)+':8000','-v',str(data)+':/app/data']
    for folder in ['app','web','scripts','docs','tests']:
        args+=['-v',str(runtime/folder)+':/app/'+folder+':ro']
    for name in ['pyproject.toml','README.md','26化工设计大赛题目.pdf']:
        args+=['-v',str(runtime/name)+':/app/'+name+':ro']
    args += [before['Config']['Image']]
    container=command(*args)
    after=json.loads(command('docker','inspect',ORIGINAL))[0]
    evidence={'qa_container':container,'name':name,'port':options.port,'source_zip_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
              'original_before':{'id':before['Id'],'running':before['State']['Running'],'mounts':before['Mounts']},
              'original_after':{'id':after['Id'],'running':after['State']['Running'],'mounts':after['Mounts']},
              'data_isolation':str(data),'model':preserved['MODEL_BALANCED']}
    assert evidence['original_before']==evidence['original_after']
    (root/'stage-result.json').write_text(json.dumps(evidence,indent=2))
    print(json.dumps(evidence))


if __name__=='__main__':
    main()
