Test Suite
==========

### Encodes Identically to Built-in Base64 and Hex Methods

Encodes the same as base 64

	>>> import base64
	>>> def compare(s, fn1, fn2):
	...     return fn1(s) == fn2(s)
	... 
	>>> def b64_builtin(s):
	...     return base64.b64encode(s)
	... 
	>>> def b64_trilobyte(s):
	...     return Data(s).stringWithEncoding(Base64)
	... 
	>>> compare('', b64_builtin, b64_trilobyte)
	True
	>>> compare('f', b64_builtin, b64_trilobyte)
	True
	>>> compare('fo', b64_builtin, b64_trilobyte)
	True
	>>> compare('foo', b64_builtin, b64_trilobyte)
	True
	>>> compare('foob', b64_builtin, b64_trilobyte)
	True
	>>> compare('fooba', b64_builtin, b64_trilobyte)
	True
	>>> compare('foobar', b64_builtin, b64_trilobyte)
	True

Decodes the same as base 64

	>>> def b64_builtin(s):
	...     return base64.b64decode(s)
	... 
	>>> def b64_trilobyte(s):
	...     return Data(s, Base64).bytes
	... 
	>>> compare('Zg==', b64_builtin, b64_trilobyte)
	True
	>>> compare('Zm8=', b64_builtin, b64_trilobyte)
	True
	>>> compare('Zm9v', b64_builtin, b64_trilobyte)
	True

Encodes the same as the hex built-in

	>>> import binascii
	>>> def hex_builtin(s):
	...     return binascii.hexlify(s).upper()
	... 
	>>> def hex_trilobyte(s):
	...     return Data(s).stringWithEncoding(Base16)
	... 
	>>> compare('', hex_builtin, hex_trilobyte)
	True
	>>> compare('f', hex_builtin, hex_trilobyte)
	True
	>>> compare('fo', hex_builtin, hex_trilobyte)
	True
	>>> compare('foo', hex_builtin, hex_trilobyte)
	True
	>>> compare('foob', hex_builtin, hex_trilobyte)
	True
	>>> compare('fooba', hex_builtin, hex_trilobyte)
	True
	>>> compare('foobar', hex_builtin, hex_trilobyte)
	True

Decodes the same as the hex built-in

	>>> def hex_builtin(s):
	...     return binascii.unhexlify(s)
	... 
	>>> def hex_trilobyte(s):
	...     return Data(s, Base16).bytes
	... 
	>>> compare('', hex_builtin, hex_trilobyte)
	True
	>>> compare('fa', hex_builtin, hex_trilobyte)
	True
	>>> compare('deadface', hex_builtin, hex_trilobyte)
	True
	>>> compare('a7ea7badcafe', hex_builtin, hex_trilobyte)
	True

Should choke on an input string of odd length

	>>> Data('f', Base16)
	Traceback (most recent call last):
	    ...
	ValueError: Illegal input string

Should choke on an input string with illegal chars

	>>> Data('AAAQ', Base16)
	Traceback (most recent call last):
	    ...
	ValueError: Illegal character in input string


### Handles Crockford Base32 Correctly

There's a test suite on [Tatham Oddie's blog](http://blog.tatham.oddie.com.au/2011/03/11/released-crockford-base32-encoder/)

	                         1    1                11
	                       194    62               629
	                   456,789    1CKE             1CKEM
	                   398,373    C515             C515Z
	     3,838,385,658,376,483    3D2ZQ6TVC93      3D2ZQ6TVC935
	18,446,744,073,709,551,615    FZZZZZZZZZZZZ    FZZZZZZZZZZZZB


### Empty Byte Strings

An empty byte string translates to an empty Base64 representation.

	>>> Data('')
	Data('', Base64)
	
	>>> Data('', Base64).bytes
	''


### Base4 Encoding

This is a silly base 4 encoding that looks like gene sequences. I couldn't
find an appropriate way to work it into the docs, but I liked the idea so I
decided to make it a test.

	>>> class BasePair (Encoding):
	...     alphabet = 'ACTG'
	...     base = 4
	...     replacements = {' ': '', '-': '', '\n': '', '\r': ''}
	...     
	...     @classmethod
	...     def _canonicalRepr(clz, string):
	...         return super(BasePair, clz)._canonicalRepr(string.upper())
	
	>>> enc = Data('7uwfEbAipb8K0w==', Base64)
	>>> enc.stringWithEncoding(BasePair)
	'GTGTGTGAACGGACACTGAAATATTTCCTGGGAATTGCAG'
	
	>>> Data('ctgatccc aagctgtg gatcttcc cagggcgg tgttgaga', BasePair)
	Data('bJUNu8mlT9+6zA==', Base64)


### Phonetic Encoding

This is a doctest to verify that a byte string converted to a Phonetic-
encoded string will decode into the original byte string.

	>>> byteString = ''.join(chr(i) for i in range(256))
	>>> e = Data(byteString)
	>>> string = e.stringWithEncoding(Phonetic)
	>>> f = Data(string, Phonetic)
	>>> f.bytes == byteString
	True

Custom wordlists can be used.

	>>> class ExchangeNames(Phonetic):
	...     pass
	... 
	>>> ExchangeNames.setWordList([
	... 'academy', 'adams', 'alpine', 'amherst', 'andrew', 'atlantic', 'atlas',
	... 'atwater', 'atwood', 'avenue', 'axminster', 'axtel', 'baldwin', 'belmont',
	... 'beverly', 'bridge', 'broadway', 'butler', 'capital', 'castle', 'cedar',
	... 'central', 'chapel', 'cherry', 'chestnut', 'churchill', 'circle',
	... 'clearbrook', 'clifford', 'clinton', 'congress', 'crestwood', 'cypress',
	... 'davenport', 'davis', 'deerfield', 'dewey', 'diamond', 'dickens', 'drake',
	... 'drexel', 'dudley', 'dunkirk', 'dupont', 'eastgate', 'edgewood', 'edison',
	... 'elliot', 'elmwood', 'emerson', 'empire', 'endicott', 'essex', 'evergreen',
	... 'exeter', 'fairfax', 'federal', 'fieldbrook', 'fieldstone', 'fillmore',
	... 'flanders', 'fleetwood', 'forest', 'foxcroft', 'franklin', 'frontier',
	... 'fulton', 'garden', 'garfield', 'general', 'geneva', 'gibson', 'gilbert',
	... 'gladstone', 'glendale', 'globe', 'goldenrod', 'granite', 'greenbriar',
	... 'greenfield', 'gridley', 'grover', 'hamilton', 'harrison', 'hazel', 'hemlock',
	... 'hempstead', 'hickory', 'hillcrest', 'hillside', 'hobart', 'homestead',
	... 'hopkins', 'howard', 'hudson', 'hunter', 'huxley', 'hyacinth', 'hyatt',
	... 'idlewood', 'jackson', 'jefferson', 'jordan', 'juniper', 'juno', 'kellogg',
	... 'keystone', 'kimball', 'kingsdale', 'lafayette', 'lakeside', 'lambert',
	... 'lawrence', 'lehigh', 'lenox', 'liberty', 'lincoln', 'linden', 'locust',
	... 'logan', 'longacre', 'lowell', 'ludlow', 'luther', 'lyndhurst', 'madison',
	... 'main', 'market', 'mayfair', 'medford', 'melrose', 'mercury', 'midway',
	... 'milton', 'mission', 'mitchell', 'mohawk', 'montrose', 'morris', 'murdock',
	... 'murray', 'museum', 'mutual', 'myrtle', 'national', 'neptune', 'newton',
	... 'niagara', 'normandy', 'northfield', 'oldfield', 'oliver', 'olympia',
	... 'orange', 'orchard', 'oriole', 'orleans', 'osborne', 'overbrook', 'owen',
	... 'oxbridge', 'oxford', 'palace', 'parkway', 'pennsylvania', 'pershing',
	... 'pilgrim', 'pioneer', 'plateau', 'plaza', 'pleasant', 'plymouth', 'poplar',
	... 'porter', 'prescott', 'president', 'prospect', 'pyramid', 'randolph',
	... 'raymond', 'redwood', 'regent', 'republic', 'riverside', 'rockwell', 'rogers',
	... 'saratoga', 'shadyside', 'sherwood', 'skyline', 'southfield', 'spring',
	... 'spruce', 'state', 'sterling', 'stillwell', 'story', 'sunset', 'swathmore',
	... 'swift', 'swinburne', 'sycamore', 'talbot', 'taylor', 'temple', 'tennyson',
	... 'terminal', 'terrace', 'thornwell', 'tilden', 'townsend', 'tremont',
	... 'triangle', 'trinity', 'trojan', 'tucker', 'tulip', 'turner', 'tuxedo',
	... 'twilight', 'twinbrook', 'twinoaks', 'ulrick', 'ulster', 'ulysses',
	... 'underhill', 'union', 'university', 'uptown', 'valley', 'vandyke', 'vernon',
	... 'victoria', 'viking', 'vinewood', 'volunteer', 'wabash', 'walker', 'walnut',
	... 'warwick', 'waverly', 'webster', 'wellington', 'wells', 'westmore',
	... 'whitehall', 'whitney', 'william', 'wilson', 'windsor', 'woodland', 'worth',
	... 'yardley', 'yellowstone', 'yorktown', 'yukon'
	... ])
	>>> d = Data('grumpy wizards')
	>>> s = d.stringWithEncoding(ExchangeNames)
	>>> s
	'juniper lenox linden lafayette lawrence lowell cypress logan
	kellogg ludlow hyacinth lenox jackson liberty'
	>>> e = Data(s, ExchangeNames)
	>>> e.bytes == 'grumpy wizards'
	True
