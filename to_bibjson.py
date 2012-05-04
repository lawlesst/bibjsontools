"""
Attempts to parse raw OpenURLs to the BibJSON convention.
"""

import urllib
import urlparse
import sys
import json
from pprint import pprint


def pull_oclc(odict):
    """
    Pull OCLC numbers from incoming FirstSearch/Worldcat urls.
    """
    import re
    oclc_reg = re.compile('\d+')
    oclc = None
    if odict.get('rfr_id', ['null'])[0].rfind('firstsearch') > -1:
        oclc = odict.get('rfe_dat', ['null'])[0]
        match = oclc_reg.search(oclc)
        if match:
            oclc = match.group()
    return oclc

def initialize_id():
    """
    Helper to simply return dict with k,v that BibJSON expects.
    """
    d = {}
    d['id'] = None
    d['type'] = None
    return d

def pull_and_map(key_list, cite):
    """
    Given a list of keys and a dictionary.  Return the first found value.
    """
    for k in key_list:
        val = cite.get(k, None)
        if val:
            return val[0].strip()
    return 


def openurl(query):
    """
    An attempt to map raw OpenURLs to BibJSON convention.  
     
    Loosely based of this nice PHP openurl parser from Rod Page:
    http://code.google.com/p/bioguid/source/search?q=openurl&origq=openurl&btnG=Search+Trunk
    """
    #Load query into dictionary
    cite = urlparse.parse_qs(query)
    #Default
    referent = {}
    referent['_query'] = query
    #Some fields will have multiple values
    referent['author'] = []
    referent['identifier'] = []
    type = None

    #Deterimine a citation type first - 
    if cite.get('rft.atitle') or cite.get('atitle'):
        type = 'article'
    elif cite.get('rft.btitle') or cite.get('btitle'):
        type = 'book'
    else:
        type = 'unknown'


    #Initialize an identifier
    id = initialize_id()
    for k,value_list in cite.items():
        for v in value_list:
            #Get type
            if k == 'genre':
                type = v
#            elif k == 'rft_val_fmt':
#                if type is None:
#                    if v == 'info:ofi/fmt:kev:mtx:journal':
#                        type = 'article'
#                    elif v == 'info:ofi/fmt:kev:mtx:book':
#                        type = 'book'
            #Article title
            elif(k == 'rft.atitle') or (k == 'atitle'):
                referent['title'] = v
            #Book title
            elif k == ('rft.btitle') or (k == 'btitle'):
                referent['title'] = v
            #Journal title
            elif (type == 'article') and ((k == 'rft.jtitle') or (k == 'rft.title') or (k == 'title')):
                #referent['secondary_title'] = v
                ti = {'name': v}
                #Try to pull short title code.
                stitle = cite.get('rft.stitle', None)
                if not stitle:
                    stitle = cite.get('stitle', None) 
                if stitle:
                    ti['shortcode'] = stitle[0] 
                referent['journal'] = ti
                type = 'article'
            #Issn
            elif (k == 'rft.issn') or (k == 'issn'):
                id['type'] = 'issn'
                id['id'] = v
            #ISBN
            elif (k == 'rft.isbn') or (k == 'isbn'):
                id['type'] = 'isbn'
                id['id'] = v
            #Publisher - doesn't seem to be standard but found in the wild.
            elif (k == 'rft.pub') or (k == 'pub'):
                referent['publisher'] = v
            #Identifiers
            elif (k == 'rft.id') or (k == 'rft_id') or (k == 'id'):
                if v.startswith('info:doi/'):
                    #referent['doi'] = v.lstrip('info:doi/')
                    id['type'] = 'doi'
                    id['id'] = "doi:%s" % v.lstrip('info:doi/')
                elif v.startswith('info:pmid/'):
                    id['type'] = 'pmid'
                    id['id'] = v
                #From the wild: id=pmid:21080734&sid=Entrez:PubMed
                elif v.startswith('pmid:'):
                    #referent['pmid'] = v.lstrip('pmid:')
                    id['type'] = 'pmid'
                    id['id'] = v.lstrip('pmid:')
            #Other ids from the wild
            elif k == 'pmid':
                id['type'] = 'pmid'
                id['id'] = v
            elif k == 'doi':
                id['type'] = 'doi'
                id['id'] = "doi:%s" % v
            #OCLC - non standard
            #Authors
            elif (k == 'rft.au') or (k == 'au') or\
                 (k == 'rft.aulast') or (k == 'aulast'):
                #If it's a full name, set here.  
                if (k == 'rft.au') or (k == 'au'): 
                    au = {'name': v}
                else:
                    au = {}
                    
                aulast = pull_and_map(['rft.aulast', 'aulast'],
                                      cite)
                if aulast:
                    au['lastname'] = aulast
                aufirst = pull_and_map(['rft.aufirst', 'aufirst'],
                                       cite)
                if aufirst:
                    au['firstname'] = aufirst
                
                #Put the full name together now if we can. 
                if not au.has_key('name'):
                    if au.has_key('lastname'):
                        if au.has_key('firstname'):
                            au['name'] = "%s %s" % (au['firstname'],
                                                    au['lastname'])
                if au not in referent['author']:
                    referent['author'].append(au)
            #Volume
            elif (k == 'rft.volume') or (k == 'volume'):
                referent['volume'] = v
            #Issue
            elif (k == 'rft.issue') or (k == 'issue'):
                referent['issue'] = v
            #Date/Year
            elif (k == 'rft.date') or (k == 'date'):
                referent['year'] = v[:4]
            #Pages are gross
            elif (k == 'rft.pages') or (k == 'pages'):
                referent['pages'] = v 
            elif (k == 'rft.spage') or (k == 'spage'):
                referent['start_page'] = v 
            elif (k == 'rft.epage') or (k == 'epage'):
                referent['end_page'] = v
            #Look at the type term
            elif k == 'type':
                if v == 'book':
                    if type != 'book':
                        type = 'book'
                elif v == 'article':
                    if type != 'book':
                        type = 'article'
                else:
                    referent['sub_type'] = v
            #Referers or sids
            if (k == 'rfr_id') or (k == 'sid'):
                referent['bul:rfr'] = v
                
            #Add any identifiers picked up on this pass
            if (id['type']) and (id['id']):
                #Make sure this pair isn't already there.
                if id not in referent['identifier']:
                    referent['identifier'].append(id)
                    #Re-initialize an identifier so that it's blank on the next trip
                    id = initialize_id()
    
    referent['type'] = type
    #Add a title if we don't have one - this will be for cases where a format can't be 
    #determined.
    if not referent.get('title', None):
        referent['title'] = cite.get('title', [''])[0]
    #Add oclc ids - non standard so handle here
    oclc = pull_oclc(cite)
    if oclc:
        referent['identifier'].append({'type': 'oclc',
                                       'id': oclc})
    #add pages if we can.
    if (referent.has_key('start_page')) and (referent.has_key('end_page')):
        referent['pages'] = "%s--%s" % (referent['start_page'],
                                        referent['end_page'])
    referent['_openurl'] = to_openurl(referent)
    return referent

def to_openurl(bib): 
    """
    Convert bibjson to an OpenURL.
    start_page => 361
    bul:rfr => FirstSearch:MEDLINE
    title => The missing technology: an international comparison of human capital investment in healthcare.
    type => article
    journal => {'name': 'Applied health economics and health policy'}
    author => [{'lastname': 'Frogner', 'name': 'BK Frogner', 'firstname': 'BK'}]
    volume => 8
    year => 2010
    identifier => [{'type': 'issn', 'id': '1175-5652'}, {'type': 'oclc', 'id': '678061209'}]
    issue => 6
    pages => 361--71
    end_page => 71
    """
    out = {}
    out['ctx_ver'] = 'Z39.88-2004'
    if bib['type'] == 'article':
        out['rft_val_fmt'] = 'info:ofi/fmt:kev:mtx:journal'
        out['rfr_id'] = "info:sid/%s" % (bib.get('bul:rfr', ''))
        out['rft.atitle'] = bib['title']
        jrnl = bib.get('journal')
        out['rft.title'] = jrnl.get('name')
        out['rft.jtitle'] = out['rft.title']
        out['rft.stitle'] = jrnl.get('shortcode')
        out['rft.date'] = bib.get('year')
        #out['rft.au'] = filter(lambda x: x.get('author')[0].get('name')
        authors = bib.get('author')
        for auth in authors:
            full = auth.get('name')
            last = auth.get('lastname')
            if full:
                out['rft.au'] = full
                break
            elif last:
                out['rft.aulast'] = last
                break
            else:
                break
        out['rft.volume'] = bib.get('volume')
        out['rft.issue'] = bib.get('issue')
        out['rft.spage'] = bib.get('start_page')
        out['rft.end_page'] = bib.get('end_page', 'EOA')
        out['rft.pages'] = bib.get('pages')
        if out['rft.pages'] is None:
            out['rft.pages'] = '%s - %s' % (out['rft.spage'], out['rft.end_page'])
        identifiers = bib.get('identifier', [])
        for idt in identifiers:
            if idt['type'] == 'issn':
                out['rft.issn'] = idt['id']
            elif idt['type'] == 'eissn':
                out['rfit.eissn'] = idt['id']
            elif idt['type'] == 'doi':
                out['rft_id'] = 'info:doi/%s' % idt['id']
            elif idt['type'] == 'pmid':
                #don't add the info:pmid if not necessary
                v = idt['id']
                if v.startswith('info:pmid'):
                    out['rft_id'] = v
                else:
                    out['rft_id'] = 'info:pmid/%s' % idt['id']
            elif idt['type'] == 'oclc':
                out['rft_id'] = 'http://www.worldcat.org/oclc/%s' % idt['id']
        out['rft.genre'] = 'article'
        return urllib.urlencode(out)
    else:
        return {}


import unittest
class TestBibJSON(unittest.TestCase):
    
    def test_book_from_worldcat(self):
        q = 'rft.pub=W+H+Freeman+%26+Co&rft.btitle=Introduction+to+Genetic+Analysis.&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&isbn=9781429233231&req_dat=%3Csessionid%3E0%3C%2Fsessionid%3E&title=Introduction+to+Genetic+Analysis.&pid=%3Caccession+number%3E277200522%3C%2Faccession+number%3E%3Cfssessid%3E0%3C%2Ffssessid%3E&rft.date=2008&genre=book&rft_id=urn%3AISBN%3A9781429233231&openurl=sid&rfe_dat=%3Caccessionnumber%3E277200522%3C%2Faccessionnumber%3E&rft.isbn=9781429233231&url_ver=Z39.88-2004&date=2008&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&id=doi%3A&rft.genre=book'
        bib = openurl(q)
        self.assertEqual(bib['type'], 'book')
        self.assertEqual(bib['title'],
                        'Introduction to Genetic Analysis.')
        self.assertEqual(bib['year'], '2008')
        self.assertTrue({'type': 'oclc',
                          'id': '277200522'} in bib['identifier'])
        #pprint(bib)
        #pprint(urlparse.parse_qs(q))
        
    def test_article(self):
        q = 'volume=16&genre=article&spage=538&sid=EBSCO:aph&title=Current+Pharmaceutical+Design&date=20100211&issue=5&issn=13816128&pid=&atitle=Targeting+%ce%b17+Nicotinic+Acetylcholine+Receptors+in+the+Treatment+of+Schizophrenia.'
        bib = openurl(q)
        self.assertEqual(bib['journal']['name'],
                         'Current Pharmaceutical Design')
        self.assertEqual(bib['year'],
                         '2010')
        self.assertTrue({'type': 'issn',
                         'id': '13816128'} in bib['identifier'])
        
    def test_article_stitle(self):
        q = 'rft_val_fmt=info:ofi/fmt:kev:mtx:journal&rfr_id=info:sid/www.isinet.com:WoK:UA&rft.spage=30&rft.issue=1&rft.epage=42&rft.title=INTEGRATIVE%20BIOLOGY&rft.aulast=Castillo&url_ctx_fmt=info:ofi/fmt:kev:mtx:ctx&rft.date=2009&rft.volume=1&url_ver=Z39.88-2004&rft.stitle=INTEGR%20BIOL&rft.atitle=Manipulation%20of%20biological%20samples%20using%20micro%20and%20nano%20techniques&rft.au=Svendsen%2C%20W&rft_id=info:doi/10%2E1039%2Fb814549k&rft.auinit=J&rft.issn=1757-9694&rft.genre=article'
        
        bib = openurl(q)
        self.assertEqual(bib['title'], 
                         'Manipulation of biological samples using micro and nano techniques')
        self.assertEqual(bib['journal']['shortcode'],
                         'INTEGR BIOL')
        #pprint(bib)
        #pprint(urlparse.parse_qs(q))
        
    def test_article_no_full_author(self):
        q = 'issn=1040676X&aulast=Wallace&title=Chronicle%20of%20Philanthropy&pid=<metalib_doc_number>000117190</metalib_doc_number><metalib_base_url>http://sfx.brown.edu:8331</metalib_base_url><opid></opid>&sid=metalib:EBSCO_APH&__service_type=&volume=17&genre=&sici=&epage=23&atitle=Where%20Should%20the%20Money%20Go%3F&date=2005&isbn=&spage=9&issue=24&id=doi:&auinit=&aufirst=%20Nicole'
    
    def test_bad_title(self):
        #This open url has a book title and a journal title.
        #Should do some type of override to handle logical inconsistencies
        q = 'rft_val_fmt=info:ofi/fmt:kev:mtx:journal&rfr_id=info:sid/www.isinet.com:WoK:UA&rft.spage=488&rft.issue=11-1&rft.epage=490&rft.title=JOURNAL%20OF%20THE%20AMERICAN%20CERAMIC%20SOCIETY&rft.aulast=DOLE&url_ctx_fmt=info:ofi/fmt:kev:mtx:ctx&rft.date=1977&rft.volume=60&rft.btitle=JOURNAL%20OF%20THE%20AMERICAN%20CERAMIC%20SOCIETY&url_ver=Z39.88-2004&rft.atitle=ELASTIC%20PROPERTIES%20OF%20MONOCLINIC%20HAFNIUM%20OXIDE%20AT%20ROOM-TEMPERATURE&rft.au=WOOGE%2C%20C&rft.auinit=S&rft.issn=0002-7820&rft.genre=article'

    def test_to_openurl_article(self):
        q = 'issn=1175-5652&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AMEDLINE&req_dat=<sessionid>0<%2Fsessionid>&pid=<accession+number>678061209<%2Faccession+number><fssessid>0<%2Ffssessid>&rft.date=2010&volume=8&date=2010&rft.volume=8&rfe_dat=<accessionnumber>678061209<%2Faccessionnumber>&url_ver=Z39.88-2004&atitle=The+missing+technology%3A+an+international+comparison+of+human+capital+investment+in+healthcare.&genre=article&epage=71&spage=361&id=doi%3A&rft.spage=361&rft.sici=1175-5652%282010%298%3A6<361%3ATMTAIC>2.0.TX%3B2-O&aulast=Frogner&rft.issue=6&rft.epage=71&rft.jtitle=Applied+health+economics+and+health+policy&rft.aulast=Frogner&title=Applied+health+economics+and+health+policy&rft.aufirst=BK&rft_id=urn%3AISSN%3A1175-5652&sici=1175-5652%282010%298%3A6<361%3ATMTAIC>2.0.TX%3B2-O&sid=FirstSearch%3AMEDLINE&rft.atitle=The+missing+technology%3A+an+international+comparison+of+human+capital+investment+in+healthcare.&issue=6&rft.issn=1175-5652&rft.genre=article&aufirst=BK'
        bib = openurl(q)
        #Round trip the query
        ourl = to_openurl(bib)
        bib2 = openurl(ourl)
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
        bib = openurl(q)
        #pprint(bib)
        ourl = to_openurl(bib)
        #print ourl
        bib2 = openurl(ourl)
        #pprint(bib2)
        self.assertEqual(bib['journal']['shortcode'],
                         bib2['journal']['shortcode'])
        
    


       
        
if __name__ == '__main__':
    unittest.main()     
    

