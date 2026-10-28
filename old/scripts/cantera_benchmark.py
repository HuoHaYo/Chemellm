"""Compare packaged NASA thermodynamics with archived NIST Shomate sources."""
import hashlib
import json
import math
import sys
from pathlib import Path

import cantera as ct
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from app.cantera_backend import GasEquilibriumInput, GasReactorInput, solve, integrate

ROOT=Path(__file__).resolve().parent.parent


def shomate(source,T):
    import re
    segments=source["coefficients"]
    coefficients=None
    for segment in segments:
        low,high=map(float,re.findall(r"\d+\.?\d*",segment["range_text_K"]))
        if low<=T<=high:coefficients=segment;break
    if coefficients is None:raise ValueError("Temperature outside archived Shomate range")
    a,b,c,d,e,f,g,h=[coefficients[k] for k in 'ABCDEFGH'];t=T/1000
    cp=a+b*t+c*t*t+d*t**3+e/t**2
    # WebBook enthalpy equation is H(T)-H(298.15); add its H formation
    # coefficient back to obtain a consistent absolute formation basis.
    enthalpy=(a*t+b*t*t/2+c*t**3/3+d*t**4/4-e/t+f)*1000
    entropy=a*math.log(t)+b*t+c*t*t/2+d*t**3/3-e/(2*t*t)+g
    return cp,enthalpy,entropy


def evaluate():
    protocol_path=ROOT/'docs/CANTERA_BENCHMARK_PROTOCOL.json'
    protocol=json.loads(protocol_path.read_text(encoding='utf-8'))
    for source in protocol['sources'].values():
        assert hashlib.sha256((ROOT/source['source_file']).read_bytes()).hexdigest()==source['sha256']
    limits=protocol['tolerances'];results=[]
    for T in protocol['temperatures_K']:
        reference={name:shomate(source,T) for name,source in protocol['sources'].items()}
        gas=ct.Solution('gri30.yaml');gas.TP=T,protocol['pressure_Pa']
        cp_errors={name:float(abs(gas.standard_cp_R[gas.species_index(name)]*ct.gas_constant/1000-values[0])/values[0]) for name,values in reference.items()}
        stoich={'CO':-1,'H2O':-1,'CO2':1,'H2':1}
        dh=sum(stoich[n]*reference[n][1] for n in stoich)
        ds=sum(stoich[n]*reference[n][2] for n in stoich)
        kp=math.exp(-(dh-T*ds)/(ct.gas_constant/1000*T))
        nasa_dh=float(sum(stoich[n]*gas.standard_enthalpies_RT[gas.species_index(n)] for n in stoich)*ct.gas_constant*T/1000)
        nasa_dg=sum(stoich[n]*gas.standard_gibbs_RT[gas.species_index(n)] for n in stoich)
        nasa_kp=math.exp(-nasa_dg)
        result=solve('equilibrium',GasEquilibriumInput(mechanism='wgs4',constraint='TP',temperature_K=T,
                    pressure_Pa=protocol['pressure_Pa'],composition=protocol['initial_relative_moles']))
        x=result['final']['mole_fractions']
        # Delta n = 0; total initial relative moles remains 2.2.
        extent=x['CO2']*2.2-.1
        expected=(math.sqrt(kp)-.1)/(1+math.sqrt(kp))
        errors={'species_Cp_relative':cp_errors,'reaction_enthalpy_absolute_J_mol':abs(nasa_dh-dh),
                'Kp_relative':abs(nasa_kp-kp)/kp,'reaction_extent_absolute_mol_per_initial_CO_mol':abs(extent-expected)}
        checks={'species_cp':max(cp_errors.values())<=limits['species_Cp_relative'],
                'reaction_enthalpy':errors['reaction_enthalpy_absolute_J_mol']<=limits['reaction_enthalpy_absolute_J_mol'],
                'Kp':errors['Kp_relative']<=limits['Kp_relative'],
                'extent':abs(extent-expected)<=limits['reaction_extent_absolute_mol_per_initial_CO_mol'],
                'numerical_validation':result['validation']['passed']}
        results.append({'temperature_K':T,'reference_Kp':kp,'cantera_Kp':nasa_kp,'reference_extent':expected,'cantera_extent':extent,
                        'errors':errors,'checks':checks,'passed':all(checks.values())})
    analytic=[]
    for constraint in ['constant_pressure','constant_volume']:
        for energy in ['adiabatic','isothermal']:
            gas=ct.Solution(str(ROOT/'docs/sources/cantera-first-order.yaml'))
            p=GasReactorInput(constraint=constraint,energy=energy,temperature_K=800,end_time_s=2,samples=60)
            result=integrate(gas,p)
            t=np.array([r['time_s'] for r in result['trajectory']]);expected=np.exp(-2*t)
            a=np.array([r['mole_fractions']['A'] for r in result['trajectory']])
            capacity=20000 if constraint=='constant_pressure' else 20000-ct.gas_constant
            temperatures=np.full_like(t,800.) if energy=='isothermal' else 800+1000000/capacity*(1-expected)
            error_x=float(max(abs(a-expected)));error_T=float(max(abs(np.array([r['temperature_K'] for r in result['trajectory']])-temperatures)))
            passed=error_x<=limits['analytic_first_order_mole_fraction_absolute'] and error_T<=limits['analytic_reactor_temperature_absolute_K'] and result['validation']['passed']
            analytic.append({'constraint':constraint,'energy':energy,'max_mole_fraction_error':error_x,'max_temperature_error_K':error_T,'passed':passed})
    return {'passed':all(r['passed'] for r in results+analytic),'cantera_version':ct.__version__,
            'protocol_sha256':hashlib.sha256(protocol_path.read_bytes()).hexdigest(),'protocol':protocol,'thermodynamic_cases':results,'analytic_cases':analytic,
            'limitations':['Public development qualification, not a held-out LLM evaluation.',
                          'NASA and NIST correlations may share original thermochemical measurements; this is not a fully independent experiment.',
                          'Manufactured first-order fixture only validates numerical integration, not real kinetics.',
                          'No experimental ignition/combustion, catalyst, styrene kinetics, VLE/LLE or full plant validation is asserted.']}


def main():
    result=evaluate();path=ROOT/'data/qa/cantera-benchmark.json';path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({'passed':result['passed'],'thermodynamic_cases':[(r['temperature_K'],r['passed']) for r in result['thermodynamic_cases']],
                      'analytic_cases':[(r['constraint'],r['energy'],r['passed']) for r in result['analytic_cases']],'report':str(path)}))
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
