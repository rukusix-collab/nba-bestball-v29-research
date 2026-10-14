"""Explicit separate evidence gates: source-native labels, roster exposure and pretip features."""
import datetime as dt, re
from zoneinfo import ZoneInfo

STATES=('NOT_ELIGIBLE','ELIGIBLE_NONAPPEARANCE','APPEARED','UNKNOWN')
SOURCE_TIERS=('ORIGINAL_BYTES_LOCAL_RECEIPT','SERVICE_EXTRACTED','UNKNOWN')

def utc_datetime(s):
    if not s:return None
    try:d=dt.datetime.fromisoformat(str(s).replace('Z','+00:00'))
    except ValueError:return None
    if d.tzinfo is None or d.utcoffset() is None:return None
    return d.astimezone(dt.timezone.utc)

def positive_minutes_iso(s):
    if s in ('',None):return None
    match=re.fullmatch(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?',str(s))
    if not match:return None
    h,m,sec=match.groups();return (int(h or 0)*60+int(m or 0)+float(sec or 0)/60)

def label_from_boxscore(player):
    """Descriptive postgame roster-listing observation; not an eligibility label."""
    played=str(player.get('played','')).lower()
    mm=positive_minutes_iso((player.get('statistics') or {}).get('minutes'))
    status=str(player.get('status','')).upper()
    if played=='1' and mm is not None and mm>0:return 'LISTED_PLAYED'
    if played=='0' and mm==0 and status in ('ACTIVE','INACTIVE'):
        return 'LISTED_NONAPPEARANCE'
    return 'LISTED_UNRESOLVED'

def appearance_exposure(roster_evidence, player=None, original_boxscore=False):
    """Date-effective evidence must be qualified by origin receipts before admission.
    Input roster_evidence: e.g. {'rostered':True,'available_to_NBA':True,'verified':True}.
    For projected appearance, injured players remain rostered/eligible exposures if under a valid team contract.
    G-League assigned player may be NOT_ELIGIBLE only when assignment is dated and confirmed.
    """
    if not isinstance(roster_evidence,dict) or roster_evidence.get('verified') is not True:return 'UNKNOWN'
    if roster_evidence.get('rostered') is False or roster_evidence.get('available_to_NBA') is False:return 'NOT_ELIGIBLE'
    if roster_evidence.get('rostered') is not True:return 'UNKNOWN'
    if not original_boxscore or player is None:return 'UNKNOWN'
    label=label_from_boxscore(player)
    if label=='LISTED_PLAYED':return 'APPEARED'
    if label=='LISTED_NONAPPEARANCE':return 'ELIGIBLE_NONAPPEARANCE'
    return 'UNKNOWN'

def report_filename_timestamp(url):
    """Only exact-minute timestamp encoded in filename (ET civil time). Hour-only vintage returns UNKNOWN.
    Older hourly names, e.g. _02PM.pdf, can correspond to a 02:30 PM header.
    Obtain verified original-PDF header time instead; do NOT substitute an invented minute.
    """
    m=re.search(r'Injury-Report_(\d{4}-\d{2}-\d{2})_(\d{2})(?:_(\d{2}))?(AM|PM)\.pdf$',url)
    if not m:return None
    date,hour,minute,ampm=m.groups()
    if minute is None:return None
    hour=int(hour)%12 + (12 if ampm=='PM' else 0)
    try:d=dt.datetime.fromisoformat(f'{date}T{hour:02d}:{minute or "00"}:00')
    except ValueError:return None
    return d.replace(tzinfo=ZoneInfo('America/New_York')).astimezone(dt.timezone.utc)

def snapshot_valid(snapshot_url,snapshot_original_sha_verified, report_header_timestamp_matches_filename,
                   game_tip_utc, source_prepublished, team_report_submitted):
    """Requires publisher custody, header/filename concordance and independent time qualification.
    A PDF may mention later games with NOT YET SUBMITTED, which must not be interpreted as zero injuries.
    """
    t=report_filename_timestamp(snapshot_url);tip=utc_datetime(game_tip_utc)
    return bool(snapshot_original_sha_verified and report_header_timestamp_matches_filename
                and source_prepublished and team_report_submitted and t and tip and t<tip)

ALLOWED_TRANSACTION_EVENTS={'CONTRACT_SIGN','CONTRACT_END','TRADE_IN','TRADE_OUT','WAIVER',
                            'TWO_WAY_SIGN','TWO_WAY_END','GLEAGUE_ASSIGN','GLEAGUE_RECALL',
                            'SUSPENSION_START','SUSPENSION_END','NOT_WITH_TEAM_START','NOT_WITH_TEAM_END'}

def transaction_admissible(event):
    return bool(event.get('player_nba_id') and event.get('team_nba_id') and
                event.get('event_type') in ALLOWED_TRANSACTION_EVENTS and utc_datetime(event.get('effective_utc'))
                and event.get('original_source_sha256') and event.get('publisher_source_url')
                and event.get('original_source_verified') is True)

def row_admissible(exposure,original_boxscore,independent_pretip,chronologically_frozen_prediction):
    return exposure in ('APPEARED','ELIGIBLE_NONAPPEARANCE') and all([original_boxscore,independent_pretip,chronologically_frozen_prediction])
