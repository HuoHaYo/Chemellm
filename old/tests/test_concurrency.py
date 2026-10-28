import subprocess
import sys

def test_cold_process_concurrent_property_and_solver_calls():
    code='''
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from app.db import init_db
from app.calculations import calculate
init_db()
jobs=[("properties",{"compound":"styrene"}),("properties",{"compound":"ethylbenzene"}),
    ("material_balance",{}),("flash",{}),("aqueous_flash",{}),("column_mesh",{})]
barrier=Barrier(len(jobs))
def run(job):
    barrier.wait()
    return calculate(*job)
with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
    results=list(pool.map(run,jobs))
assert 104<results[0]["properties"]["MW"]["value"]<104.2
assert 106<results[1]["properties"]["MW"]["value"]<106.2
assert all(result["validation"]["passed"] for result in results[2:])
print("cold concurrent engine calls passed")
'''
    r=subprocess.run([sys.executable,"-X","utf8","-c",code],capture_output=True,text=True,encoding="utf-8",timeout=60)
    assert r.returncode==0,r.stdout+r.stderr
