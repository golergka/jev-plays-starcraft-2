"""Compare sampled/top investment alternatives on recorded states; no game commands."""
import asyncio
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from jev_sc2.jev import Jev


async def main():
    source, output = map(Path, sys.argv[1:3])
    if output.exists():
        raise FileExistsError(output)
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    samples, latest = [], None
    for row in rows:
        if row['event']=='jev' and 'investment' in row['questions']:
            latest = row
        if row['event']=='investment_sample' and latest:
            top, sampled = row['top_choice'], row['sampled_choice']
            criteria = latest['questions']['investment']['criteria']
            if top != sampled and top in criteria and sampled in criteria:
                samples.append((row, latest))
    samples = samples[-3:]
    jev = Jev(lambda *args, **kwargs:None, 'investment-comparison-probe', max_calls=6)
    results = []
    for index, (sample, original) in enumerate(samples):
        question = original['questions']['investment']
        alternatives = [sample['sampled_choice'], sample['top_choice']]
        if index % 2:
            alternatives.reverse()
        mapping = dict(zip(['option_a', 'option_b'], alternatives))
        comparison = {'type':'choice', 'instructions':question['instructions']+
                      ' Compare these two alternatives for the current situation.',
                      'criteria':{key:question['criteria'][choice] for key,choice in mapping.items()}}
        requests = [('full_menu', {'investment':question}), ('comparison', {'investment':comparison})]
        if index % 2:
            requests.reverse()
        result = {'loop':sample['loop'],'resources':original['state'].get('resources'),
                  'recorded_top':sample['top_choice'],'recorded_sample':sample['sampled_choice'],
                  'recorded_probabilities':sample['probabilities'],'mapping':mapping,
                  'descriptions':comparison['criteria']}
        for label, questions in requests:
            result[label] = (await jev.ask(original['state'],questions))['investment']
        results.append(result)
    payload = {'source':str(source),'method':'Last three recorded investment samples differing from top choice; unchanged state; alternate option and request order. No game commands.',
               'results':results,'calls':jev.calls,'cost':jev.cost}
    output.write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps(payload,indent=2))


if __name__=='__main__':
    asyncio.run(main())
