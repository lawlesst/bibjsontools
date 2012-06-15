"""
Converting OpenURLs to BibJSON and back.
"""

import urllib
import urlparse
import sys
try:
    import json
except ImportError:
    import simplejson as json


class OpenURLParser(object):

    def __init__(self, openurl, query_dict=None):
        if query_dict:
            self.data = query_dict
        else:
            self.query = openurl
            self.data = urlparse.parse_qs(openurl)

    def _find_key(self, key_list, this_dict=None):
        """
        Utility to get the first matching value from a list of possible keys.
        """
        #Default to the data dict.
        if not this_dict:
            this_dict = self.data
        for k in key_list:
            v = this_dict.get(k, None)
            if v:
                return v[0]
        return

    def _find_repeating_key(self, key_list, this_dict=None):
        """
        Utility to get a unique list of values from a set of keys.
        """
        out = []
        #Default to the data dict.
        if not this_dict:
            this_dict = self.data
        for k in key_list:
            v = this_dict.get(k, None)
            if v:
                out += v
        return set(out)

    def _find_key_values(self, key_list, this_dict=None):
        """
        Utility to return a list of key,value tuples from a list of possible keys.
        """
        #Default to the data dict.
        if not this_dict:
            this_dict = self.data
        out = []
        for k in key_list:
            v = this_dict.get(k, None)
            if v:
                out.append((k, v))
        return out

    @property
    def type(self):
        """
        Determine the type of citation.  Defaults to book.
        """
        #Defaulting to type of book.  
        btype = 'book'
        genre = self._find_key(['rft.genre', 'genre'])
        if genre:
            if genre == 'bookitem':
                btype = 'inbook'
            else:
                #Catch openurls where there is extra characters
                #To do - switch to regex
                if 'book' in genre:
                    return 'book'
                elif 'article' in genre:
                    return 'article'
        else:
            #Try to guess based on incoming values.
            if self._find_key(['rft.atitle', 'atitle']):
                btype = 'article'
            elif self._find_key(['rft.btitle', 'btitle']):
                btype = 'book'
        return btype

    def identifiers(self):
        """
        Pull the identifiers.  This should be common to all types.
        """
        out = []
        #Identifiers - using both the standard and what's found in typical OpenURLs
        ids = self._find_key_values(['rft.id',
                                     'rft_id',
                                     'id',
                                     'doi',
                                     'pmid',
                                     'pid',
                                     'rfe_dat'])
        for k, values in ids:
            for v in values:
                d = {}
                d['id'] = None
                d['type'] = None
                #DOIS and PMIDS in the id
                if (k == 'rft.id') or (k == 'rft_id') or (k == 'id'):
                    if v.startswith('info:doi/'):
                        #referent['doi'] = v.lstrip('info:doi/')
                        d['type'] = 'doi'
                        d['id'] = "doi:%s" % v.lstrip('info:doi/')
                    elif v.startswith('info:pmid/'):
                        d['type'] = 'pmid'
                        d['id'] = v
                    #Handle pubmed IDs coming in like this pmid:18539564
                    elif v.startswith('pmid'):
                        d['type'] = 'pmid'
                        d['id'] = 'info:%s' % v.replace(':', '/')
                #OCLC
                #elif (((k == 'rfe_dat') or (k =='pid')) and ('accessionnumber' in v)):
                #    d['type'] = 'oclc'
                #    d['id'] = v.replace('<accessionnumber>', '').replace('</accessionnumber>', '')
                #Other ids from the wild
                elif k == 'pmid':
                    d['type'] = 'pmid'
                    d['id'] = v
                elif k == 'doi':
                    d['type'] = 'doi'
                    d['id'] = "doi:%s" % v

                #If we found an id add it to the output.
                if d['id']:
                    out.append(d)
        #ISBNS and ISSNs are more straightforward so will handle them separately.
        for isbn in self._find_repeating_key(['rft.isbn', 'isbn']):
            out.append({'type': 'isbn',
                        'id': isbn})
        for issn in self._find_repeating_key(['rft.issn', 'issn']):
            out.append({'type': 'issn',
                        'id': issn})
        for eissn in self._find_repeating_key(['rft.eissn', 'eissn']):
            out.append({'type': 'eissn',
                        'id': issn})
        #OCLCs
        oclc = pull_oclc(self.data)
        if (oclc) and (oclc not in out):
            out.append({'type': 'oclc', 'id': oclc})
        return out

    def titles(self):
        out = {}
        #Article or book titles will be set to bibjson title.
        out['title'] = self._find_key(['rft.atitle',
                                       'atitle',
                                       'rft.btitle',
                                       'btitle'])
        #Book titles and unknowns could also be in title 
        if (not out['title']) and (self.type == 'book' or self.type == 'unknown'):
            out['title'] = self._find_key(['rft.title',
                                            'title'])
        #Journal title
        if self.type in ['article', 'inbook']:
            jtitle = self._find_key(['rft.jtitle',
                                     'jtitle',
                                     'rft.btitle',
                                     'btitle',
                                     'rft.title',
                                     'title'])
            if jtitle:
                ti = {'name': jtitle}
                #Try to pull short title code.
                stitle = self.data.get('rft.stitle', None)
                if not stitle:
                    stitle = self.data.get('stitle', None) 
                if stitle:
                    ti['shortcode'] = stitle[0] 
                out['journal'] = ti
        return out

    def authors(self):
        """
        Pull authors.  Less straightforward than you might think.  
        For now, we won't worry about first and last names.
        """
        out = []
        authors = self._find_key_values([
                                        'rft.au',
                                        'au',
                                        'rft.aulast',
                                        'aulast'])
        for k,values in authors:
            for v in values:
                if (k == 'rft.au') or (k == 'au') or\
                    (k == 'rft.aulast') or (k == 'aulast'):
                    #If it's a full name, set here.  
                    if (k == 'rft.au') or (k == 'au'): 
                        au = {'name': v}
                    else:
                        au = {}
                    aulast = self._find_key(['rft.aulast', 'aulast'])
                    if aulast:
                        au['lastname'] = aulast
                    aufirst = self._find_key(['rft.aufirst', 'aufirst'])
                    if aufirst:
                        au['firstname'] = aufirst
                    
                    #Put the full name together now if we can. 
                    if not au.has_key('name'):
                        #If there isn't a first and last name, just use last.
                        last = au.get('lastname', '')
                        first = au.get('firstname', '')
                        name = "%s, %s" % (last, first.strip())
                        au['name'] = name.rstrip(', ')
                    #Don't duplicate authors
                    if au not in out:
                        out.append(au)
        return out

    def pages(self):
        """
        Try to set start, end page and pages.
        """
        out = {}
        #Pages
        out['pages'] = self._find_key(['rft.pages', 'pages'])
        start = self._find_key(['rft.spage', 'spage'])
        end = self._find_key(['rft.epage', 'epage'])
        if (not out['pages']):
            if start:
                #Default end_page is EOA - end of article
                if not end:
                    end = 'EOA'
                #Default end page to end of article
                pages = "%s - %s" % (start, end)
                out['pages'] = pages.strip()
        
        out['end_page'] = end
        out['start_page'] = start

        return out
    
    def rfr(self):
        """
        Get the referring site.
        """
        #try the usual suspects
        r = self._find_key(['rfr_id', 'sid', 'id'])
        if r:
            
            return r


    def parse(self):
        """
        Create and return the bibjson.
        """
        #from pprint import pprint
        #pprint(self.data)
        d = {}
        d['type'] = self.type
        #Referrer
        d['_rfr'] = self.rfr()
        d['identifier'] = self.identifiers()
        d.update(self.titles())
        d['author'] = self.authors()
        #Publisher
        d['publisher'] = self._find_key(['rft.pub', 'pub', 'rft.publisher', 'publisher'])
        #Place - not sure how BibJSON would officially handle this
        d['place_of_publication'] = self._find_key(['rft.place', 'place'])
        #Volume
        d['volume'] = self._find_key(['rft.volume', 'volume'])
        #Issue
        d['issue'] = self._find_key(['rft.issue', 'issue'])
        #Date/Year
        year = self._find_key(['rft.date', 'date'])
        if year:
            d['year'] = year[:4]
        #Pages
        d.update(self.pages())
        #Remove empty keys
        for k,v in d.items():
            if not v:
                del d[k]
        #add the original openurl
        d['_openurl'] = BibJSONToOpenURL(d).parse()
        return d
        
def from_openurl(query):
    """
    Alias/shortcut to parse the provided query.
    """
    b = OpenURLParser(query)
    return b.parse()

def from_dict(request_dict):
    """
    Alias/shortcut to handle dictionary inputs. 
    Use for this is passing Django request.GET as dict.
    """
    b = OpenURLParser('', query_dict=request_dict)
    return b.parse() 

class BibJSONToOpenURL(object):
    def __init__(self, bibjson):
        self.data = bibjson

    def parse(self):
        #return self.data
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
        bib = self.data
        out = {}
        out['ctx_ver'] = 'Z39.88-2004'
        btype = bib['type']
        title = bib.get('title')
        #By default we will treat unknowns as articles for now.
        if (btype == 'article'):
            out['rft_val_fmt'] = 'info:ofi/fmt:kev:mtx:journal'
            out['rft.atitle'] = title
            jrnl = bib.get('journal', {})
            out['rft.jtitle'] = jrnl.get('name', '')
            out['rft.stitle'] = jrnl.get('shortcode')
            out['rft.genre'] = 'article'
        elif (btype == 'book') or (btype == 'bookitem'):
            out['rft_val_fmt'] = 'info:ofi/fmt:kev:mtx:book'
            out['rft.btitle'] = title
            out['rft.genre'] = 'book'
            if bib['type'] == 'inbook':
                out['rft.genre'] = 'bookitem'
                jrnl = bib.get('journal', {})
                out['rft.btitle'] = jrnl.get('name')
                #For Illiad add as title
                out['title'] = jrnl.get('name')
                out['rft.atitle'] = bib['title']
        else:
            #Try to fill in a title for unkowns
            out['rft.genre'] = 'unknown'
            out['rft.title'] = bib.get('title')
            jrnl = bib.get('journal', {})
            out['rft.jtitle'] = jrnl.get('name')
            out['rft.stitle'] = jrnl.get('shortcode')

        out['rfr_id'] = "info:sid/%s" % (bib.get('bul:rfr', ''))

        #Do the common attributes
        out['rft.date'] = bib.get('year', '')[:4]
        authors = bib.get('author', [])
        for auth in authors:
            full = auth.get('name')
            last = auth.get('lastname')
            if full:
                out['rft.au'] = full
            elif last:
                out['rft.aulast'] = last
        out['rft.volume'] = bib.get('volume')
        out['rft.issue'] = bib.get('issue')
        out['rft.spage'] = bib.get('start_page')
        out['rft.end_page'] = bib.get('end_page')
        out['rft.pages'] = bib.get('pages')
        out['rft.pub'] = bib.get('publisher')
        out['rft.place'] = bib.get('place_of_publication')
        identifiers = bib.get('identifier', [])
        for idt in identifiers:
            if idt['type'] == 'issn':
                out['rft.issn'] = idt['id']
            elif idt['type'] == 'isbn':
                out['rft.isbn'] = idt['id']
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
        #Remove empty keys
        for k,v in out.items():
            if (not v) or (v == ''):
                del out[k]
        #Handle unicode and url quoting.
        #See - http://stackoverflow.com/questions/120951/how-can-i-normalize-a-url-in-python
        #http://stackoverflow.com/a/8152242
        kevs = []
        for k,v in out.iteritems():
            if isinstance(v, unicode):
                v = v.encode('utf-8', 'ignore')
            _k = urllib.quote_plus(k, safe='/')
            _v = urllib.quote_plus(v, safe='/')
            kevs.append('%s=%s' % (_k, _v))
        return '&'.join(kevs)



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
    #Try pid
    spot = odict.get('pid', ['null'])[0]
    if spot.rfind('accession') > -1:
        match = oclc_reg.search(spot)
        if match:
            oclc = match.group()
            return oclc
    #rfe_dat - these are probably OCLC numbers in most cases.
    dat = odict.get('rfe_dat')
    if (dat) and ('accessionnumber' in dat[0]):
        match = oclc_reg.search(dat[0])
        if match:
            return match.group()
    return oclc

def to_openurl(bib):
    out = BibJSONToOpenURL(bib)
    return out.parse()
