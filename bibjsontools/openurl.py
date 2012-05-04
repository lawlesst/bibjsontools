"""
Converting OpenURLs to BibJSON and back.
"""

import urllib
import urlparse
import sys
import json

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


def from_openurl(query):
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