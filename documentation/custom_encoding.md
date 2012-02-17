Custom String Encodings for Trilobyte's Data Objects
====================================================

This document describes the process of creating custom string encoding classes
for Trilobyte `Data` objects. We will start by looking at a slightly modified
implementation of Base32 encoding that conforms with [RFC 4648][rfc], followed
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

Another simple subclass is 

### RFC 4648 Base32 Encoding

[RFC 4648][rfc] describes a version of Base32 encoding that is stricter than
Doug Crockford's version. Still, it may be helpful to have an Encoding class
that's able to handle this variant. The `Base32_4648` class defined below is a
simple implementation of this standard.

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

[rfc]: (http://tools.ietf.org/html/rfc4648)
