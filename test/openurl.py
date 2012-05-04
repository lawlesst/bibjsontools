import unittest

from bibjsontools import from_openurl, to_openurl

class TestBibJSONOpenURL(unittest.TestCase):
    
    def test_book_from_worldcat(self):
        q = 'rft.pub=W+H+Freeman+%26+Co&rft.btitle=Introduction+to+Genetic+Analysis.&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&isbn=9781429233231&req_dat=%3Csessionid%3E0%3C%2Fsessionid%3E&title=Introduction+to+Genetic+Analysis.&pid=%3Caccession+number%3E277200522%3C%2Faccession+number%3E%3Cfssessid%3E0%3C%2Ffssessid%3E&rft.date=2008&genre=book&rft_id=urn%3AISBN%3A9781429233231&openurl=sid&rfe_dat=%3Caccessionnumber%3E277200522%3C%2Faccessionnumber%3E&rft.isbn=9781429233231&url_ver=Z39.88-2004&date=2008&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&id=doi%3A&rft.genre=book'
        bib = from_openurl(q)
        self.assertEqual(bib['type'], 'book')
        self.assertEqual(bib['title'],
                        'Introduction to Genetic Analysis.')
        self.assertEqual(bib['year'], '2008')
        self.assertTrue({'type': 'oclc',
                          'id': '277200522'} in bib['identifier'])
        
    def test_article(self):
        q = 'volume=16&genre=article&spage=538&sid=EBSCO:aph&title=Current+Pharmaceutical+Design&date=20100211&issue=5&issn=13816128&pid=&atitle=Targeting+%ce%b17+Nicotinic+Acetylcholine+Receptors+in+the+Treatment+of+Schizophrenia.'
        bib = from_openurl(q)
        self.assertEqual(bib['journal']['name'],
                         'Current Pharmaceutical Design')
        self.assertEqual(bib['year'],
                         '2010')
        self.assertTrue({'type': 'issn',
                         'id': '13816128'} in bib['identifier'])
        
    def test_article_stitle(self):
        q = 'rft_val_fmt=info:ofi/fmt:kev:mtx:journal&rfr_id=info:sid/www.isinet.com:WoK:UA&rft.spage=30&rft.issue=1&rft.epage=42&rft.title=INTEGRATIVE%20BIOLOGY&rft.aulast=Castillo&url_ctx_fmt=info:ofi/fmt:kev:mtx:ctx&rft.date=2009&rft.volume=1&url_ver=Z39.88-2004&rft.stitle=INTEGR%20BIOL&rft.atitle=Manipulation%20of%20biological%20samples%20using%20micro%20and%20nano%20techniques&rft.au=Svendsen%2C%20W&rft_id=info:doi/10%2E1039%2Fb814549k&rft.auinit=J&rft.issn=1757-9694&rft.genre=article'
        
        bib = from_openurl(q)
        self.assertEqual(bib['title'], 
                         'Manipulation of biological samples using micro and nano techniques')
        self.assertEqual(bib['journal']['shortcode'],
                         'INTEGR BIOL')
        
    def test_article_no_full_author(self):
        q = 'issn=1040676X&aulast=Wallace&title=Chronicle%20of%20Philanthropy&pid=<metalib_doc_number>000117190</metalib_doc_number><metalib_base_url>http://sfx.brown.edu:8331</metalib_base_url><opid></opid>&sid=metalib:EBSCO_APH&__service_type=&volume=17&genre=&sici=&epage=23&atitle=Where%20Should%20the%20Money%20Go%3F&date=2005&isbn=&spage=9&issue=24&id=doi:&auinit=&aufirst=%20Nicole'
    
    def test_bad_title(self):
        #This open url has a book title and a journal title.
        #Should do some type of override to handle logical inconsistencies
        q = 'rft_val_fmt=info:ofi/fmt:kev:mtx:journal&rfr_id=info:sid/www.isinet.com:WoK:UA&rft.spage=488&rft.issue=11-1&rft.epage=490&rft.title=JOURNAL%20OF%20THE%20AMERICAN%20CERAMIC%20SOCIETY&rft.aulast=DOLE&url_ctx_fmt=info:ofi/fmt:kev:mtx:ctx&rft.date=1977&rft.volume=60&rft.btitle=JOURNAL%20OF%20THE%20AMERICAN%20CERAMIC%20SOCIETY&url_ver=Z39.88-2004&rft.atitle=ELASTIC%20PROPERTIES%20OF%20MONOCLINIC%20HAFNIUM%20OXIDE%20AT%20ROOM-TEMPERATURE&rft.au=WOOGE%2C%20C&rft.auinit=S&rft.issn=0002-7820&rft.genre=article'

    def test_to_openurl_article(self):
        q = 'issn=1175-5652&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AMEDLINE&req_dat=<sessionid>0<%2Fsessionid>&pid=<accession+number>678061209<%2Faccession+number><fssessid>0<%2Ffssessid>&rft.date=2010&volume=8&date=2010&rft.volume=8&rfe_dat=<accessionnumber>678061209<%2Faccessionnumber>&url_ver=Z39.88-2004&atitle=The+missing+technology%3A+an+international+comparison+of+human+capital+investment+in+healthcare.&genre=article&epage=71&spage=361&id=doi%3A&rft.spage=361&rft.sici=1175-5652%282010%298%3A6<361%3ATMTAIC>2.0.TX%3B2-O&aulast=Frogner&rft.issue=6&rft.epage=71&rft.jtitle=Applied+health+economics+and+health+policy&rft.aulast=Frogner&title=Applied+health+economics+and+health+policy&rft.aufirst=BK&rft_id=urn%3AISSN%3A1175-5652&sici=1175-5652%282010%298%3A6<361%3ATMTAIC>2.0.TX%3B2-O&sid=FirstSearch%3AMEDLINE&rft.atitle=The+missing+technology%3A+an+international+comparison+of+human+capital+investment+in+healthcare.&issue=6&rft.issn=1175-5652&rft.genre=article&aufirst=BK'
        bib = from_openurl(q)
        #Round trip the query
        ourl = to_openurl(bib)
        bib2 = from_openurl(ourl)
        self.assertEqual(bib['type'],
                         bib2['type'])
        self.assertEqual(bib['title'],
                          bib2['title'])
        self.assertEqual(bib['journal']['name'],
                         bib2['journal']['name'])
        self.assertEqual(bib['year'],
                         bib2['year'])

    def test_to_openurl_pmid(self):
        #Round trip the query
        q = 'rft_val_fmt=info:ofi/fmt:kev:mtx:journal&rfr_id=info:sid/pss.sagepub.com&rft.spage=569&rft.issue=4&rft.epage=582&rft.aulast=Nolen-Hoeksema&ctx_tim=2010-11-27T19:38:39.6-08:00&url_ctx_fmt=info:ofi/fmt:kev:mtx:ctx&rft.volume=100&url_ver=Z39.88-2004&rft.stitle=J%20Abnorm%20Psychol&rft.auinit1=S.&rft.atitle=Responses%20to%20depression%20and%20their%20effects%20on%20the%20duration%20of%20depressive%20episodes.&ctx_ver=Z39.88-2004&rft_id=info:pmid/1757671&rft.jtitle=Journal%20of%20abnormal%20psychology&rft.genre=article'
        bib = from_openurl(q)
        #pprint(bib)
        ourl = to_openurl(bib)
        #print ourl
        bib2 = from_openurl(ourl)
        #pprint(bib2)
        self.assertEqual(bib['journal']['shortcode'],
                         bib2['journal']['shortcode'])
        
        
def suite():
    suite = unittest.makeSuite(TestBibJSONOpenURL, 'test')
    return suite

if __name__ == '__main__':
    unittest.main()