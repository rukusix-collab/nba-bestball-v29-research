import unittest,hashlib,json,tempfile,pathlib,csv
from source_custody import source_rows,verify,inspect_response
from qualification import positive_minutes_iso,label_from_boxscore,appearance_exposure,report_filename_timestamp,snapshot_valid,transaction_admissible,row_admissible

class TestRealAdmission(unittest.TestCase):
 def test_source_requests(self):
  x=list(source_rows());self.assertEqual(len(x),2462)
  self.assertEqual(len({x1['native_game_id'] for x1 in x if x1['native_game_id']}),2460)
 def test_original_missing(self):
  with tempfile.TemporaryDirectory() as d:self.assertEqual(verify(pathlib.Path(d),next(source_rows())),'NOT_ACQUIRED')
 def test_minute_valid(self):
  self.assertAlmostEqual(positive_minutes_iso('PT30M10.50S'),30.175)
 def test_minute_zero(self):self.assertEqual(positive_minutes_iso('PT00M00.00S'),0)
 def test_minute_bad(self):self.assertIsNone(positive_minutes_iso('oops'))
 def test_label_active_dnp(self):self.assertEqual(label_from_boxscore({'played':'0','status':'ACTIVE','statistics':{'minutes':'PT00M00.00S'}}),'LISTED_NONAPPEARANCE')
 def test_label_inactive_dnp(self):self.assertEqual(label_from_boxscore({'played':'0','status':'INACTIVE','statistics':{'minutes':'PT00M00.00S'}}),'LISTED_NONAPPEARANCE')
 def test_label_played(self):self.assertEqual(label_from_boxscore({'played':'1','status':'ACTIVE','statistics':{'minutes':'PT10M01.00S'}}),'LISTED_PLAYED')
 def test_label_ambiguous(self):self.assertEqual(label_from_boxscore({'played':'1','status':'ACTIVE','statistics':{'minutes':'PT00M00.00S'}}),'LISTED_UNRESOLVED')
 def test_unlisted_never_negative(self):self.assertEqual(appearance_exposure({'verified':True,'rostered':True},None,True),'UNKNOWN')
 def test_service_extracted_never_negative(self):self.assertEqual(appearance_exposure({'verified':True,'rostered':True},{'played':'0','status':'ACTIVE','statistics':{'minutes':'PT00M00.00S'}},False),'UNKNOWN')
 def test_no_verified_roster(self):self.assertEqual(appearance_exposure({'rostered':True},{'played':'0','status':'ACTIVE','statistics':{'minutes':'PT00M00.00S'}},True),'UNKNOWN')
 def test_date_effective_not_rostered(self):self.assertEqual(appearance_exposure({'verified':True,'rostered':False},None,True),'NOT_ELIGIBLE')
 def test_date_effective_gleague(self):self.assertEqual(appearance_exposure({'verified':True,'rostered':True,'available_to_NBA':False},None,True),'NOT_ELIGIBLE')
 def test_rostered_played(self):self.assertEqual(appearance_exposure({'verified':True,'rostered':True},{'played':'1','statistics':{'minutes':'PT02M01S'}},True),'APPEARED')
 def test_rostered_dnp(self):self.assertEqual(appearance_exposure({'verified':True,'rostered':True},{'played':'0','status':'ACTIVE','statistics':{'minutes':'PT00M00S'}},True),'ELIGIBLE_NONAPPEARANCE')
 def test_source_invalid_game_id(self):
  with self.assertRaises(ValueError):inspect_response(json.dumps({'game':{'gameId':'bad','gameStatus':3}}).encode(),'NBA_FINAL_BOXSCORE','0022501208')
 def test_report_2026_time(self):
  t=report_filename_timestamp('https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-02-05_10_30AM.pdf')
  self.assertEqual(t.isoformat(),'2026-02-05T15:30:00+00:00')
 def test_report_2024_hour_only(self):
  t=report_filename_timestamp('https://ak-static.cms.nba.com/referee/injury/Injury-Report_2024-11-15_02PM.pdf')
  self.assertIsNone(t)
 def test_report_not_submitted(self):
  self.assertFalse(snapshot_valid('https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-02-05_10_30AM.pdf',True,True,'2026-02-06T00:00:00Z',True,False))
 def test_report_posttip(self):
  self.assertFalse(snapshot_valid('https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-02-05_10_30AM.pdf',True,True,'2026-02-05T14:00:00Z',True,True))
 def test_report_not_custodied(self):
  self.assertFalse(snapshot_valid('https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-02-05_10_30AM.pdf',False,True,'2026-02-06T00:00:00Z',True,True))
 def test_transaction_no_orig_sha(self):
  self.assertFalse(transaction_admissible({'player_nba_id':1,'team_nba_id':2,'event_type':'TRADE_IN','effective_utc':'2025-02-01T00:00:00Z','publisher_source_url':'https://nba.com','original_source_verified':True}))
 def test_model_training_no_prediction(self):self.assertFalse(row_admissible('APPEARED',True,True,False))
 def test_model_training_no_roster(self):self.assertFalse(row_admissible('UNKNOWN',True,True,True))
 def test_model_training_qualified_synthetic(self):self.assertTrue(row_admissible('APPEARED',True,True,True))

if __name__=='__main__':unittest.main()
