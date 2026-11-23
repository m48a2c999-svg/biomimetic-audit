#!/bin/bash
# biomimetic-audit 사례 보강 계산: 솔방울 원리를 충실히 옮긴 습도 응답 수동 제어(HB/HL/HV, 민감도 HBN/HB2)와 기준(S1c).
# calc 브랜치(badtm)와 같은 EnergyPlus 23.2.0, 같은 입력·조건(@c: epd 1.0, cop 2.0, end-use 출력)으로 계산한다.
set -eu
K=$1; B=$GITHUB_WORKSPACE/sim/sb; export BUNDLE=$B
cd $B/mb/py
python3 sim_sb10.py job_bioh_$K.json $(nproc) || true
python3 - $K <<'PY'
import pickle, glob, json, sys, os, numpy as np
K=sys.argv[1]; B=os.environ['BUNDLE']; out={}
H=[]
for f in sorted(glob.glob(B+'/mb/res_sb10/*.pkl')):
    R=pickle.load(open(f,'rb')); key=os.path.basename(f)[:-4]
    d={k:R.get(k) for k in ('EUI','area','peak_kW','UDI','PMV_ok','err','monthly_el_kWh','monthly_gas_kWh','Cooling:Electricity','Heating:NaturalGas','InteriorLights:Electricity')}
    out[key]=d
    if R.get('hourly_kW') is not None: H.append((key, np.asarray(R['hourly_kW'],dtype=np.float32)))
os.makedirs('/tmp/o',exist_ok=True)
json.dump(out,open(f'/tmp/o/bioh_{K}.json','w'),default=float)
np.savez_compressed(f'/tmp/o/bioh_{K}_hourly.npz', keys=np.array([k for k,_ in H]), kw=np.stack([v for _,v in H]) if H else np.zeros((0,8760),np.float32))
print('runs',len(out),'ok',sum(1 for v in out.values() if v['EUI'] is not None))
PY
