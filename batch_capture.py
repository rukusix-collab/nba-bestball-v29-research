"""GitHub Actions and Colab wrapper for immutable R9-S19A original source capture.
No network access without explicit CLI invocation. Existing source_custody.py preserved unchanged.
"""
import argparse, hashlib, json, pathlib, sys, time, urllib.parse, datetime
from source_custody import capture, source_rows, verify


def selection(mode, start=0, count=5):
    rows=list(source_rows())
    if len(rows)!=2462:
        raise RuntimeError(f'Historical inventory changed unexpectedly: {len(rows)}')
    if mode=='smoke':
        # 2024 schedule, 2025 schedule, 2025 native game #0022501208
        return [(i,rows[i]) for i in (0, 1231, 2439)]
    if not 0<=start<len(rows) or not 1<=count<=100:
        raise ValueError('batch index 0..2461 and count 1..100 required')
    return [(i, rows[i]) for i in range(start,min(start+count,len(rows)))]


def run(mode, out, start=0, count=5, delay=1.0):
    if delay<0.5:
        raise ValueError('Use conservative delay >= 0.5 seconds')
    out=pathlib.Path(out); out.mkdir(parents=True,exist_ok=True)
    outcomes=[];consecutive_failures=0
    for index,row in selection(mode,start,count):
        at=datetime.datetime.now(datetime.timezone.utc).isoformat()
        state=verify(out,row)
        if state=='ORIGINAL_BYTES_LOCAL_RECEIPT':
            outcomes.append({'index':index,'url':row['url'],'status':'PRESENT_AND_REVERIFIED'})
            continue
        if state in ('FAILED_INTEGRITY','FAILED_SCHEMA'):
            outcomes.append({'index':index,'url':row['url'],'status':'UNQUALIFIED_EXISTING_FILE','detail':state})
            consecutive_failures+=1
            continue
        try:
            receipt=capture(row,out,timeout=35)
            # The saved original S19A code verifies status, body JSON, native game ID,
            # original response bytes and checksum; assert original host after redirects too.
            origin=urllib.parse.urlparse(row['url']).hostname
            final=urllib.parse.urlparse(receipt['final_url']).hostname
            if final != origin:
                # Override the original helper's provisional receipt claim: changed-host
                # responses are not certified publisher-origin bytes.
                year=row['season'].split('-')[0]
                basename=('schedule.json' if row['source_type']=='NBA_SEASON_SCHEDULE' else row['native_game_id']+'.json')
                receipt_path=out/year/('schedules' if row['source_type']=='NBA_SEASON_SCHEDULE' else 'boxscores')/(basename+'.receipt.json')
                held=json.loads(receipt_path.read_text())
                held['publisher_original_body_direct_get']=False
                held['provenance']='UNQUALIFIED: final URL redirected outside expected publisher host'
                receipt_path.write_text(json.dumps(held,indent=2,sort_keys=True))
                raise RuntimeError('Response redirect left original source host; receipts NOT admitted')
            outcomes.append({'index':index,'url':row['url'],'status':'ORIGINAL_BYTES_LOCAL_RECEIPT',
                             'sha256':receipt['body_sha256'],'byte_count':receipt['body_byte_count'],
                             'request_started_utc':receipt['request_started_utc'],
                             'response_completed_utc':receipt['response_completed_utc'],
                             'independently_witnessed':False})
            consecutive_failures=0
        except Exception as exc:
            message=f'{type(exc).__name__}: {exc}'
            outcomes.append({'index':index,'url':row['url'],'status':'FAILED','error':message,'at_utc':at})
            with (out/'FAILURES.ndjson').open('a',encoding='utf-8') as fp:
                fp.write(json.dumps(outcomes[-1])+'\n')
            consecutive_failures+=1
        if consecutive_failures>=5:
            break
        time.sleep(delay)
    counts={}
    for x in outcomes:counts[x['status']]=counts.get(x['status'],0)+1
    summary={'mode':mode,'start':start,'count_requested':count,'requested_records':len(selection(mode,start,count)),
             'records_checked':len(outcomes),'counts':counts,'independently_witnessed_timestamp':False,
             'original_capture_completed':False,'full_eligibility_census_qualified':False,
             'notes':'Only source_custody original-byte receipts with integrity verification meet LOCAL evidence tier; historical prediction admission remains blocked.'}
    (out/'CAPTURE_SUMMARY.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    with (out/'CAPTURE_OUTCOMES.ndjson').open('a',encoding='utf-8') as fp:
        for x in outcomes:fp.write(json.dumps(x)+'\n')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['smoke','batch'],default='smoke')
    p.add_argument('--out',required=True);p.add_argument('--start-index',type=int,default=0)
    p.add_argument('--count',type=int,default=5);p.add_argument('--delay',type=float,default=1.0)
    a=p.parse_args()
    result=run(a.mode,a.out,a.start_index,a.count,a.delay)
    print(json.dumps(result,indent=2))
    sys.exit(1 if result['counts'].get('FAILED') or result['counts'].get('UNQUALIFIED_EXISTING_FILE') else 0)
