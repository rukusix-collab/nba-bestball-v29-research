import unittest
from batch_capture import selection

class TestBatch(unittest.TestCase):
 def test_smoke_targets(self):
  x=selection('smoke');self.assertEqual([p[0] for p in x],[0,1231,2439]);
  self.assertEqual(x[2][1]['native_game_id'],'0022501208')
 def test_first_2024(self):
  x=selection('batch',0,2);self.assertEqual(x[0][1]['source_type'],'NBA_SEASON_SCHEDULE');
  self.assertEqual(x[1][1]['native_game_id'],'0022400001')
 def test_2025_first(self):
  x=selection('batch',1231,2);self.assertEqual(x[1][1]['native_game_id'],'0022500001')
 def test_end(self):
  x=selection('batch',2461,5);self.assertEqual(len(x),1);self.assertEqual(x[0][1]['native_game_id'],'0022501230')
 def test_no_large(self):
  with self.assertRaises(ValueError):selection('batch',0,101)
 def test_negative(self):
  with self.assertRaises(ValueError):selection('batch',-1,10)

if __name__=='__main__':unittest.main()
