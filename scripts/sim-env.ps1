# 扩展环境（pyomo / IDAES / rdkit）环境变量与自检
# 用法：在需要仿真/优化的终端里先执行
#   . .\scripts\sim-env.ps1
$root = Split-Path -Parent $PSScriptRoot
$env:IDAES_DATA = Join-Path $root 'data\idaes'
$bin = Join-Path $env:IDAES_DATA 'bin'
if (Test-Path -LiteralPath $bin) {
  $env:PATH = $bin + ';' + $env:PATH
}
$env:PATH = (Join-Path $root '.venv-sim\Scripts') + ';' + $env:PATH
Write-Host "IDAES_DATA = $env:IDAES_DATA"
Write-Host "sim python  = $root\.venv-sim\Scripts\python.exe"
& (Join-Path $root '.venv-sim\Scripts\python.exe') -X utf8 -c @"
from pyomo.environ import ConcreteModel, Var, Constraint, value, SolverFactory
m = ConcreteModel()
m.x = Var(bounds=(0, 10))
m.c = Constraint(expr=m.x**2 == 4)
solver = SolverFactory('ipopt')
print('ipopt available:', solver.available(exception_flag=False))
result = solver.solve(m)
print('x =', value(m.x), '| termination:', result.solver.termination_condition)
"@
