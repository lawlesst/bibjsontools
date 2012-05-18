
# -*- coding: utf-8 -*-
import unittest

from bibjsontools import ris
from bibjsontools.openurl import from_openurl

def ris_chunker(rtext):
	"""
	Helper for parsing RIS text.
	"""
	return [(e.split(' - ')[0].strip(), e.split(' - ')[1]) for e in rtext.split('\n') if e ]

class TestFromOpenURL(unittest.TestCase):

	def test_book(self):
		q = 'sid=FirstSearch%3AWorldCat&genre=book&isbn=9780385475723&title=The+blind+assassin&aulast=Atwood&aufirst=Margaret&auinitm=Eleanor&id=doi%3A&pid=%3Caccession+number%3E43287739%3C%2Faccession+number%3E%3Cfssessid%3Efsapp2-48452-f3edqijd-fzttco%3C%2Ffssessid%3E%3Cedition%3E1st+ed.+in+the+U.S.A.%3C%2Fedition%3E&url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&req_id=%3Csessionid%3Efsapp2-48452-f3edqijd-fzttco%3C%2Fsessionid%3E&rfe_dat=%3Caccessionnumber%3E43287739%3C%2Faccessionnumber%3E&rft_ref_fmt=info%3Aofi%2Ffmt%3Axml%3Axsd%3Aoai_dc&rft_ref=http%3A%2F%2Fpartneraccess.oclc.org%2Fwcpa%2Fservlet%2FOUDCXML%3Foclcnum%3D43287739&rft_id=info%3Aoclcnum%2F43287739&rft_id=urn%3AISBN%3A9780385475723&rft.aulast=Atwood&rft.aufirst=Margaret&rft.auinitm=Eleanor&rft.btitle=The+blind+assassin&rft.isbn=9780385475723&rft.place=New+York&rft.pub=N.A.+Talese&rft.edition=1st+ed.+in+the+U.S.A.&rft.genre=book'
		bib = from_openurl(q)
		r = ris.convert(bib)
		chunks = ris_chunker(r)
		self.assertTrue(('TI', 'The blind assassin') in chunks)

	def test_journal(self):
		q = 'volume=26&genre=article&spage=293&sid=EBSCO:aph&title=Natural+Resources+Forum&date=20021101&issue=4&issn=01650203&pid=&atitle=Forest+products+and+traditional+peoples%3a+Economic%2c+biological%2c+and+cultural+considerations.'
		bib = from_openurl(q)
		r = ris.convert(bib)
		chunks = ris_chunker(r)
		self.assertTrue(('JF', 'Natural Resources Forum') in chunks)
		self.assertTrue(('SN', '01650203') in chunks)
		self.assertTrue(('SP', '293') in chunks)

	def test_author(self):
		q = 'rft.author=Smith,John&rft.title=A book&rft.genre=book&doi=1234'
		bib = from_openurl(q)
		r = ris.convert(bib)
		chunks = ris_chunker(r)
		self.assertTrue(('DO', 'doi:1234') in chunks)
		self.assertTrue(('TI', 'A book') in chunks)
		self.assertTrue(('TY', 'BOOK') in chunks)



def suite():
    suite1 = unittest.makeSuite(TestFromOpenURL, 'test')
    return suite1

if __name__ == '__main__':
    unittest.main()



