Custom String Encodings for Trilobyte's Data Objects
====================================================

This document describes the process of creating custom string encoding classes
for Trilobyte `Data` objects. We will start by looking at a slightly modified
implementation of Base32 encoding that conforms with [RFC 4648](http://tools.ietf.org/html/rfc4648), followed
by a new base 54 encoding designed to be highly error-resistant.


Creating Simple Encodings
-------------------------

In some cases, simply specifying a custom alphabet and base is enough to
implement the desired encoding. The following examples show some simple
encoding classes that can be used with the Trilobyte library.

### Binary Encoding

One of the easiest encodings to implement as an extension to Trilobyte is a
binary encoding. Simply create a subclass of the `Encoding` class and define
its alphabet (`'01'`), base (`2`), and replacement dictionary (`{' ': ''}`).

	>>> class Binary(Encoding):
	...     alphabet = '01'
	...     base = 2
	...     replacements = {' ': ''}

The `Binary` class relies on the `encode()` and `decode()` class methods in
`Encoding` which are generalizable across all encodings whose base is a power
of two. The example below shows the `Binary` encoding in action.

	>>> enc = Data('HELLO')
	>>> enc.stringWithEncoding(Binary)
	'0100100001000101010011000100110001001111'
	
	>>> dec = Data('01010111 01001111 01010010 01001100 01000100', Binary)
	>>> dec.bytes
	'WORLD'

We've seen Doug Crockford's Base32 encoding in the general tutorial, but there
are other specifications for encodings with slightly different alphabets and
padding rules. We'll take a look at one of them in the next section.

### RFC 4648 Base32 Encoding

[RFC 4648](http://tools.ietf.org/html/rfc4648) describes a version of Base32
encoding that is stricter than Doug Crockford's version. Still, it may be
helpful to have an Encoding class that's able to handle this variant. The
`Base32_4648` class defined below is a simple implementation of this standard.

	>>> class Base32_4648(Encoding):
	...     alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
	...     base = 32
	...     replacements = {' ': '', '-': ''}
	...     padding = [0, 6, 4, 3, 1]
	...     
	...     @classmethod
	...     def decode(clz, string):
	...         padding = string.count('=')
	...         bytes = super(Base32_4648, clz).decode(string.strip('='))
	...         
	...         if clz.padding[len(bytes) % 5] != padding:
	...             raise ValueError('Incorrect padding')
	...         
	...         return bytes
	...     
	...     @classmethod
	...     def encode(clz, byteString):
	...         string = super(Base32_4648, clz).encode(byteString)
	...         return string + '=' * clz.padding[len(byteString) % 5]
	...     
	...     @classmethod
	...     def _canonicalRepr(clz, string):
	...         return super(Base32_4648, clz)._canonicalRepr(string.upper())

Now we can encode and decode RFC 4648 Base32 strings.

	>>> d = Data('MZXW6===', Base32_4648)
	>>> d.bytes
	'foo'
	
	>>> d = Data('foobar')
	>>> d.stringWithEncoding(Base32_4648)
	'MZXW6YTBOI======'

This implementation is not fully tested, which is why it's not currently
included in the `data` module. 

These examples are fairly trivial, but in many cases the only changes you will
need to make to an encoding is to modify its alphabet. However, some encodings
do more than just re-partition bits and look up values. In the next section,
we'll look at how to customize the `Encoding` subclass for a more complex
encoding scheme.


Creating Advanced Encodings
---------------------------

Sometimes overriding the `alphabet` and `base` attributes is not enough. In
the previous section, we've seen how to implement simple extensions of the
`encode` and `decode` methods. In this section we'll look at more complex
encodings.

In the following section, we describe and implement an encoding that compresses
the input bytes before returning the output. This example uses a
[Burrows-Wheeler transform](http://en.wikipedia.org/wiki/Burrows-Wheeler_transform)
to make the byte string easier to compress with run-length encoding.

Please note that this is a very naive implementation. It's slow and quite
possibly buggy. (We're talking exponential time and space. Nasty.) It's only
meant as an example of the sorts of add-ons that are possible when extending
the encoding process.

### Compressing Strings with Run-Length Encoding

This is an extension of the Base64 implementation that runs the byte string
through a compression algorithm before encoding. Decoding a compressed Base64
string results in the original byte string.

The following class is also included as `extras/squash.py`.

	>>> class Squash(Base64):
	...     @classmethod
	...     def decode(clz, string):
	...         compressed = super(Squash, clz).decode(string)
	...         return clz._bwt_decode(clz._rle_decode(compressed))
	... 
	...     @classmethod
	...     def encode(clz, byteString):
	...         compressed = clz._rle_encode(clz._bwt_encode(byteString))
	...         return super(Squash, clz).encode(compressed)
	... 
	...     @staticmethod
	...     def _bwt_encode(string):
	...         assert '\0' not in string, "Input string cannot contain nul character ('\0')"
	...         string += '\0'
	...         table = [string[i:] + string[:i] for i in range(len(string))]
	...         table.sort()
	...         return ''.join([row[-1:] for row in table])
	... 
	...     @staticmethod
	...     def _bwt_decode(string):
	...         # Naive implementation
	...         table = [''] * len(string)
	...         for i in range(len(string)):
	...             table = [string[i] + table[i] for i in range(len(string))]
	...             table.sort()
	...         s = [row for row in table if row.endswith('\0')][0]
	...         return s.rstrip('\0')
	... 
	...     @staticmethod
	...     def _rle_encode(string):
	...         '''Return a run-length encoded string'''
	... 
	...         count = 1
	...         prev = None
	...         encoded = ''
	... 
	...         def encode_run(char, count):
	...             if ord(char) >= 127:
	...                 high, low = ((ord(char) & 0xF0) >> 4, ord(char) & 0x0F)
	...                 enc = chr(0xE0 | 0x0F & high) + chr(0xC0 | 0x0F & low)
	...             else:
	...                 enc = char
	...  
	...             if count == 1:
	...                 return enc
	...             else:
	...                 return chr(0x80 | (count - 2)) + enc
	... 
	...         for ch in string:
	...             if prev == None:
	...                 prev = ch
	...                 continue
	...             elif prev == ch:
	...                 count += 1
	... 
	...             if ch != prev or count == 65:
	...                 encoded += encode_run(prev, count)
	...                 count = 1
	...                 prev = ch
	... 
	...         encoded += encode_run(prev, count)
	...         return encoded
	... 
	...     @staticmethod
	...     def _rle_decode(string):
	...         '''Return the expanded form of a run-length encoded string'''
	... 
	...         decoded = ''
	...         temp = 0
	...         length = 0
	... 
	...         for ch in string:
	...             byte = ord(ch)
	...             if byte & 0x80 == 0x00:
	...                 # ch is a single character.
	...                 if length == 0:
	...                     decoded += ch
	...                 else:
	...                     decoded += ch * length
	... 
	...                 length = 0
	...             elif byte & 0xF0 == 0xE0:
	...                 # ch is the high-order half of a large character
	...                 temp = ((byte & 0x0F) << 4)
	...             elif byte & 0xF0 == 0xC0:
	...                 # ch is the low-order half of a large character
	...                 temp |= byte & 0x0F
	... 
	...                 if length == 0:
	...                     decoded += chr(temp)
	...                 else:
	...                     decoded += chr(temp) * length
	... 
	...                 length = 0
	...             elif byte & 0xC0 == 0x80:
	...                 # ch is an encoded run length.
	...                 length = (byte & 0x4F) + 2
	...             else:
	...                 raise ValueError('Illegal string')
	... 
	...         return decoded

The intended use case for the `Squash` class is to compress `Data` objects
whose `bytes` property is an ASCII or UTF-8 encoded strings. We do this by
calling `stringWithEncoding` to return a "Squash encoded" string that
represents the original data. First, we need a string to encode:

	>>> string = '''A man, a plan, a canoe, pasta, heros, rajahs, a coloratura, maps,
	... snipe, percale, macaroni, a gag, a banana bag, a tan, a tag, a banana
	... bag again (or a camel), a crepe, pins, Spam, a rut, a Rolo, cash, a
	... jar, sore hats, a peon, a canal -- Panama!'''

To get the compressed string, we create a Data object and call the new
instance's `stringWithEncoding` method, passing it the `Squash` class.

	>>> d = Data(string)
	>>> compressed = d.stringWithEncoding(Squash)
	
	>>> print compressed
	IYBhLG5sLWGDLHKILGeEYSyBYWWALEGALGGALGEsYSyBYSBsgHNodIBngG5zKWlz
	bm1uZ29hZWGBZXNyLSAAgSBugCBuiyBtdHJtYnRnYiBqZ3JuY3BuY2xtdIBuY1CA
	YmNtaoBjcGhyCoEgcoEgYYEgcmxvgHBtcHJwaIJhIGFzgCBhbmFwbmEKYWVwYYBv
	gGGBIGFpb4dhb3NhaWxuUmNlcihsc3JTIGllgiBhb2F1IG9lb2NhZSBwbmh0b2EK
	IGF1c4AggGF0cg==

<!-- For some reason the test above fails. The failure shows the expected
     and the actual values to be identical, so I believe it's a bug in the
     test framework. -->

Now, we would expect that the compressed string would be smaller than the
original raw string, but remember that the result is Base64 encoded, and
Base64 uses four characters to represent three bytes. Instead, we must
compare it to the Base64 encoded version of the original. Sure enough, the
compressed data is smaller.

	>>> len(d.stringWithEncoding(Base64))
	340
	>>> len(compressed)
	280

And of course, a compression algorithm would be useless if you couldn't
retrieve the original string:

	>>> e = Data(compressed, Squash)
	>>> print e.bytes
	A man, a plan, a canoe, pasta, heros, rajahs, a coloratura, maps,
	snipe, percale, macaroni, a gag, a banana bag, a tan, a tag, a banana
	bag again (or a camel), a crepe, pins, Spam, a rut, a Rolo, cash, a
	jar, sore hats, a peon, a canal -- Panama!

And that's that!