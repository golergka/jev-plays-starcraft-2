"""Recorded-state comparison of repair-aware purchase contract."""
import asyncio
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

REPLACEMENTS = {
    'This decision controls all new training and construction; no other selection will spend resources this tick. ': 'This decision selects the next new purchase. Other selections cannot start additional purchases in this review, but worker repairs can still consume shared minerals. ',
    'Requests no new unit, structure or upgrade; resources remain available. Does not change existing orders.': 'Requests no new unit, structure or upgrade. Does not change existing orders or stop repairs; ongoing repairs may continue spending minerals.',
    'No other purchase will spend that reserved budget during this commitment. ': 'No other new purchase is allowed during this commitment. This does not reserve minerals against repair spending; ongoing repairs may delay affordability. ',
    'This exclusive reservation ends when the batch finishes, expires, or your strategic priority changes. ': 'This exclusive purchase reservation ends when the batch finishes, expires, or your strategic priority changes. Repairs can still spend minerals while the batch is active. ',
}
def replace(text):
    for old,new in REPLACEMENTS.items(): text=text.replace(old,new)
    return text

async def main():
    source, output = map(Path, sys.argv[1:3])
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    rows = [r for r in rows if r['event']=='jev' and 'investment' in r.get('questions',{})]
    if len(rows)<3: raise ValueError('Need three investment states')
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model=Jev(lambda *a,**k:None,'repair-contract-probe',max_calls=6)
    result={'source':str(source),'method':'First/middle/last eligible recorded requests. Full original state and questions retained; treatment corrects exclusive-spending and reserved-mineral claims to acknowledge ongoing repair spending; no action filtering or tactical recommendation. Alternating order, one pair per state. No gameplay commands; descriptive comparison, not causal performance evidence.','pairs':[]}
    for i,row in enumerate([rows[0],rows[len(rows)//2],rows[-1]]):
        questions=copy.deepcopy(row['questions'])
        q=questions['investment']
        q['instructions']=replace(q['instructions'])
        q['criteria']={k:replace(v) for k,v in q['criteria'].items()}
        pair={'time':row['time'], 'criteria':questions['investment']['criteria']};result['pairs'].append(pair)
        for arm in (['baseline','explicit'] if i%2==0 else ['explicit','baseline']):
            pair[arm]=await model.ask(row['state'], row['questions'] if arm=='baseline' else questions)
            result.update(calls=model.calls,cost_usd=model.cost)
            output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost_usd':model.cost,'choices':[{a:{k:v['choice'] for k,v in p[a].items()} for a in ('baseline','explicit')} for p in result['pairs']]}))

if __name__=='__main__':asyncio.run(main())
