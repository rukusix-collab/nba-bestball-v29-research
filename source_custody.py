"""S19A network-enabled first-party NBA acquisition; NEVER treats extracted pages as raw publisher bytes.
No acquisition is performed merely by importing this module. Raw receipts store self-observed timestamps,
which are not independent witnesses. Preserve failure logs; never mark failed requests acquired.
"""
import argparse,csv,datetime as dt,hashlib,json,os,pathlib,time,urllib.error,urllib.request

SEASONS={'2024':'2024-25','2025':'2025-26'}
SCHEDULE='https://data.nba.com/data/10s/v2015/json/mobile_teams/nba/{}/league/00_full_schedule.json'
BOX='https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/liveData/boxscore/boxscore_{}.json'


def source_rows():
    for year, season in SEASONS.items():
        yield {'source_type':'NBA_SEASON_SCHEDULE','season':season,'native_game_id':'','url':SCHEDULE.format(year),'acquisition_state':'NOT_ACQUIRED'}
        for n in range(1,1231):
            gid=f'002{year[2:]}{n:05d}'
            yield {'source_type':'NBA_FINAL_BOXSCORE','season':season,'native_game_id':gid,'url':BOX.format(gid),'acquisition_state':'NOT_ACQUIRED'}


def utcnow():return dt.datetime.now(dt.timezone.utc).isoformat(timespec='milliseconds')


def inspect_response(body, source_type, game_id):
    d=json.loads(body)
    if source_type=='NBA_SEASON_SCHEDULE':
        if not isinstance(d.get('lscd'),list):raise ValueError('Not a native NBA schedule')
    elif source_type=='NBA_FINAL_BOXSCORE':
        g=d.get('game')
        if not isinstance(g,dict) or str(g.get('gameId'))!=game_id or g.get('gameStatus')!=3:
            raise ValueError('Missing or unfinished/mismatched game ID')
        for side in ['homeTeam','awayTeam']:
            if not isinstance(g.get(side,{}).get('players'),list):raise ValueError('Missing player list')
    else:raise ValueError('Unknown source class')
    return d


def capture(row,base: pathlib.Path, timeout=25, max_bytes=10_000_000):
    """Atomic raw acquisition, exact bytes plus HTTP metadata. No original-byte attestations if GET fails."""
    year=row['season'].split('-')[0]
    filename=('schedule.json' if row['source_type']=='NBA_SEASON_SCHEDULE' else row['native_game_id']+'.json')
    target=base/year/('schedules' if row['source_type']=='NBA_SEASON_SCHEDULE' else 'boxscores')/filename
    receipt=target.with_name(target.name+'.receipt.json')
    if target.exists() or receipt.exists():raise FileExistsError('Immutable source target already exists, verify manually or choose new root')
    req=urllib.request.Request(row['url'],headers={'User-Agent':'NBA-BestBall-V29-R9-S19A-research/1.0','Accept':'application/json','Accept-Encoding':'identity'})
    began=utcnow()
    with urllib.request.urlopen(req,timeout=timeout) as resp:
        status=resp.status;hdr=list(resp.headers.items());final=resp.geturl();body=resp.read(max_bytes+1)
        received=utcnow()
    if status!=200 or not body or len(body)>max_bytes:raise ValueError(f'Non-200, empty or oversized body: {status} bytes={len(body)}')
    inspect_response(body,row['source_type'],row['native_game_id'])
    target.parent.mkdir(parents=True,exist_ok=True)
    temp=target.with_name(target.name+'.tmp')
    with open(temp,'xb') as f:
        f.write(body);f.flush();os.fsync(f.fileno())
    os.replace(temp,target)
    data={'source_url':row['url'],'final_url':final,'source_type':row['source_type'],'native_game_id':row['native_game_id'],
          'season':row['season'],'http_status':status,'http_response_headers':hdr,'request_started_utc':began,
          'response_completed_utc':received,'body_sha256':hashlib.sha256(body).hexdigest(),'body_byte_count':len(body),
          'publisher_original_body_direct_get':True,'timestamp_independently_witnessed':False,
          'provenance':'User-agent direct origin HTTP request; timestamp locally observed, not independently attested.'}
    with open(receipt,'x') as f:json.dump(data,f,indent=2,sort_keys=True)
    return data


def verify(root,row):
    year=row['season'].split('-')[0]; filename=('schedule.json' if row['source_type']=='NBA_SEASON_SCHEDULE' else row['native_game_id']+'.json')
    path=root/year/('schedules' if row['source_type']=='NBA_SEASON_SCHEDULE' else 'boxscores')/filename
    receipt=path.with_name(path.name+'.receipt.json')
    if not path.exists() or not receipt.exists():return 'NOT_ACQUIRED'
    m=json.loads(receipt.read_text());b=path.read_bytes()
    if (m.get('body_sha256') !=hashlib.sha256(b).hexdigest() or m.get('body_byte_count')!=len(b)
        or m.get('source_url')!=row['url'] or m.get('http_status')!=200
        or m.get('publisher_original_body_direct_get') is not True):return 'FAILED_INTEGRITY'
    try:inspect_response(b,row['source_type'],row['native_game_id'])
    except Exception:return 'FAILED_SCHEMA'
    return 'ORIGINAL_BYTES_LOCAL_RECEIPT'


def run(base,limit=None,delay=0.6):
    base=pathlib.Path(base);base.mkdir(parents=True,exist_ok=True)
    attempts=0; consecutive_failures=0; outcomes={'SUCCESS':0,'FAILED':0,'ALREADY_PRESENT':0,'STOPPED_EARLY':False}
    for row in source_rows():
        if limit is not None and attempts>=limit:break
        if verify(base,row)=='ORIGINAL_BYTES_LOCAL_RECEIPT':outcomes['ALREADY_PRESENT']+=1;continue
        attempts+=1
        try:
            capture(row,base); outcomes['SUCCESS']+=1; consecutive_failures=0
        except Exception as exc:
            outcomes['FAILED']+=1;consecutive_failures+=1
            with (base/'FAILURES.ndjson').open('a') as f:
                f.write(json.dumps({'at_utc':utcnow(),'url':row['url'],'exception_class':type(exc).__name__,'message':str(exc)})+'\n')
        if consecutive_failures>=5:
            outcomes['STOPPED_EARLY']=True
            break  # fail-closed: no uncontrolled request storm on a blocked origin or revoked access
        time.sleep(delay)
    return outcomes


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--limit',type=int);parser.add_argument('--delay',type=float,default=.6)
    a=parser.parse_args();print(json.dumps(run(a.out,a.limit,a.delay)))
