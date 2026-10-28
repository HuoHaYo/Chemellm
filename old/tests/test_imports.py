import subprocess
import sys
from app.config import ROOT

def test_reaction_module_imports_independently():
    result=subprocess.run([sys.executable,"-c","import app.reaction; import app.calculations; assert 'reaction_thermo' in app.calculations.REGISTRY"],cwd=ROOT,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr
