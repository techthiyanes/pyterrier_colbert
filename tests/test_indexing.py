import unittest
import pandas as pd
import tempfile
class TestIndexing(unittest.TestCase):

    def test_indexing_1doc(self):
        #minimum test case size is 100 docs, 40 Wordpiece tokens, and nx > k. we found 200 worked
        import pyterrier as pt
        from pyterrier_colbert.indexing import ColBERTIndexer
        checkpoint="http://www.dcs.gla.ac.uk/~craigm/colbert.dnn.zip"
        import os
        indexer = ColBERTIndexer(
            checkpoint, 
            os.path.dirname(self.test_dir),os.path.basename(self.test_dir), 
            chunksize=3,
            gpu=False)

        iter = pt.get_dataset("vaswani").get_corpus_iter()
        indexer.index([ next(iter) for i in range(200) ])

        import pyterrier_colbert.pruning as pruning
            
        for factory in [indexer.ranking_factory()]:

            for pipe, has_score, name in [
                (factory.end_to_end(), True, "E2E"),
                (factory.prf(False), True, "PRF rank"),
                (factory.prf(True), True, "PRF rerank"),
                (factory.set_retrieve(), False, "set_retrieve"),
                (factory.ann_retrieve_score() , True, "approx"),
                ((
                    factory.query_encoder() 
                    >> pruning.query_embedding_pruning_first(factory, 9) 
                    >> factory.set_retrieve(query_encoded=True)
                    >> factory.index_scorer(query_encoded=False) 
                    ), True, "QEP first"),
                ((
                    factory.query_encoder() 
                    >> pruning.query_embedding_pruning(factory, 9) 
                    >> factory.set_retrieve(query_encoded=True)
                    >> factory.index_scorer(query_encoded=False) 
                    ), True, "QEP ICF"),
                ((
                    factory.query_encoder() 
                    >> pruning.query_embedding_pruning_special(CLS=True) 
                    >> factory.set_retrieve(query_encoded=True)
                    >> factory.index_scorer(query_encoded=False) 
                    ), True, "QEP CLS"),
            ]:
                with self.subTest(name):
                    print("Running subtest %s" % name)
                    dfOut = pipe.search("chemical reactions")                
                    self.assertTrue(len(dfOut) > 0)
                    
                    if has_score:
                        self.assertTrue("score" in dfOut.columns)
                    else:
                        self.assertFalse("score" in dfOut.columns)

            dfOut = factory.end_to_end().search("chemical reactions")
            self.assertTrue(len(dfOut) > 0)

            dfOut = factory.prf(False).search("chemical reactions")
            self.assertTrue(len(dfOut) > 0)

            dfOut = factory.prf(True).search("chemical reactions")
            self.assertTrue(len(dfOut) > 0)

            dfOut = factory.ann_retrieve_score().search("chemical reactions")
            self.assertTrue(len(dfOut) > 0)
            self.assertTrue("score" in dfOut.columns)

            dfOut = factory.ann_retrieve_score().search("chemical reactions")
            self.assertTrue(len(dfOut) > 0)
            self.assertTrue("score" in dfOut.columns)




    def setUp(self):
        import pyterrier as pt
        if not pt.started():
            pt.init()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        try:
            shutil.rmtree(self.test_dir)
        except:
            pass