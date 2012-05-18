"""
Convert from BibJSON to RIS.
Adapted from https://github.com/okfn/bibserver/blob/master/parserscrapers_plugins/RISParser.py
"""

from bibjsontools import from_openurl

FIELD_MAP = {
	'access date': 'Y2',
	'accession number': 'AN',
	'alternate title': 'J2',
	'author': 'AU',
	'call number': 'CN',
	'caption': 'CA',
	'custom 3': 'C3',
	'custom 4': 'C4',
	'custom 5': 'C5',
	'custom 7': 'C7',
	'custom 8': 'C8',
	'database provider': 'DP',
	'date': 'DA',
	'doi': 'DO',
	'epub date': 'ET',
	'figure': 'L4',
	'file attachments': 'L1',
	'institution': 'AD',
	'issn': 'SN',
	'issue': 'IS',
	'journal': 'JF',
	'keyword': 'KW',
	'label': 'LB',
	'language': 'LA',
	'name of database': 'DB',
	'nihmsid': 'C6',
	'note': 'AB',
	'notes': 'N1',
	'number': 'IS',
	'number of volumes': 'NV',
	'original publication': 'OP',
	'pages': 'SP',
	'place published': 'CY',
	'pmcid': 'C2',
	'publisher': 'PB',
	'reprint edition': 'RP',
	'reviewed item': 'RI',
	'secondary title': 'T2',
	'section': 'SE',
	'short title': 'ST',
	'start page': 'M2',
	'subsidiary author': 'A4',
	'tertiary author': 'A3',
	'tertiary title': 'T3',
	'title': 'TI',
	'translated author': 'TA',
	'translated title': 'TT',
	'type ': 'TY',
	'url': 'UR',
	'volume': 'VL',
	'year': 'PY'
}

def convert(bib):
	"""
	Convert BibJSON to the RIS format for import into various utilities.
	To do: add some test cases. 
	"""
	ris = {}
	if bib['type'] == 'article':
		ris['TY'] = 'JOUR'
	elif bib['type'] == 'book':
		ris['TY'] = 'BOOK'
	else:
		ris['TY'] = 'GENERIC'

	for k,v in bib.items():
		if k == 'author':
			for author in v:
				name = author.get('name')
				if name:
					ris['AU'] = name
		elif k == 'journal':
			ris['JF'] = v.get('name')
		elif k == 'identifier':
			for idt in v:
				this = idt['id']
				if idt['type'] == 'doi':
					ris['DO'] = this
				elif idt['type'] == 'issn':
					ris['SN'] = this
				elif idt['type'] == 'isbn':
					ris['SN'] = this
				#elif idt['type'] == 'pmid':
				#	ris[]
		else:
			ris_k = FIELD_MAP.get(k, None)
			if ris_k:
				ris_v = bib.get(k)
				ris[ris_k] = ris_v

	out = ''
	for k,v in ris.items():
		out += "%s  - %s\n" % (k, v)
	return out