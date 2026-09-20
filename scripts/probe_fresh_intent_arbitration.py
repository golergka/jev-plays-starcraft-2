"""Compare purchase choices with and without previously elicited Jev goals."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev

async def main():
    prior_path, output = map(Path, sys.argv[1:3])
    prior = json.loads(prior_path.read_text())
    rows = {r['time']: r for r in map(json.loads, Path(prior['source']).read_text().splitlines()) if r['event']=='jev'}
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    model = Jev(lambda *a, **k: None, 'fresh-intent-arbitration-probe', max_calls=9)
    result = {'source':prior['source'], 'intent_source':str(prior_path),
              'method':'Reuse the three exact recorded states but elicit fresh intentions before each paired allocation comparison. Fresh baseline versus identical purchase question with Jev goals added to state. All choices retained, including Save. Alternating order, one pair per state. Fresh goals are hypothetical, not observations or forced orders. No gameplay commands.', 'pairs':[]}
    for i, old in enumerate(prior['pairs']):
        row = rows[old['time']]
        fresh = await model.ask(row['state'], old['target_questions'])
        goals = [{'question':q['instructions'], 'chosen_intent':q['criteria'][fresh[key]['choice']]}
                 for key,q in old['target_questions'].items()]
        enriched = {**row['state'], 'jev_production_intentions':{
            'goals':goals, 'meaning':'Your previously chosen hypothetical production intentions for this same observation. They may compete for shared resources. Select the next purchase independently; goals do not authorize purchases, eliminate alternatives or prohibit saving.'}}
        pair = {'time':old['time'], 'goals':goals, 'fresh_intents':fresh}; result['pairs'].append(pair)
        for arm in (['baseline','with_intents'] if i%2==0 else ['with_intents','baseline']):
            pair[arm] = await model.ask(row['state'] if arm=='baseline' else enriched, row['questions'])
            choice=pair[arm]['investment']['choice']
            pair[arm+'_description']=row['questions']['investment']['criteria'][choice]
            result.update(calls=model.calls,cost_usd=model.cost)
            output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'calls':model.calls,'cost_usd':model.cost,'choices':[{a:p[a]['investment']['choice'] for a in ['baseline','with_intents']} for p in result['pairs']]}))

if __name__=='__main__': asyncio.run(main())
