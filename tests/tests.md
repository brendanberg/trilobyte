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
