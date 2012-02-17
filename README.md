Trilobyte
=========

Trilobyte is a collection of classes for storing binary data and converting it
into various base-encoded strings for text representations useful for over-the-
wire transmission.

The library's core consists of the `Data` class, which is an opaque wrapper
class for byte strings. (Using string notation for binary data is perhaps one
of Python's more problematic quirks, but we do not question the BDFL.) In
addition, the `Encoding` class provides an abstract interface for various
encoding implementations. Trilobyte provides classes that implement base 16,
Doug Crockford's base 32, Flickr's base 58, and base 64 encodings.

This document describes the motivation behind the Trilobyte library and high-
level use of the objects the library provides.


Data Programming Guide
----------------------

Data objects are opaque wrappers for a string of bytes. The constructor takes
either an encoded string and an encoding specifier, or a raw byte string.
(Encoding specifiers are discussed later.)


### Creating Data Objects from Raw Bytes

Calling the Data constructor with a raw byte string simply wraps the byte
string with a Data object.

	>>> Data('\xcd\tl\xb2y\xd9Ei\xa3\x02\x13\x02\xf44E\xa3')
	Data('zQlssnnZRWmjAhMC9DRFow==', Base64)

Note that the default representation of a Data object uses the base 64 string
representation of its contents. This is typically more compact than Python's
representation of byte strings, since the overhead of hex escaping non-ASCII
characters in the byte string is avoided.

This form of the constructor is useful when dealing with Python libraries that
represent raw binary data as native strings of bytes. For example, an MD5
digest may be encoded as a Base64 string without going through hexadecimal as
an intermediate step.

	>>> from hashlib import md5
	>>> Data(md5('Hello, world!').digest())
	Data('bNNVbesNpUvKBgtMOUeYOQ==', Base64)


### Creating Data Objects from Encoded Strings

When you're provided with data in specific string encodings, the second form
of the constructor is used. Here, you see a Data object instantiated by
calling the constructor with arguments for the encoded string and an encoding
class.

	>>> Data('5d41402abc4b2a76b9719d911017c592', Base16)
	Data('XUFAKrxLKna5cZ2REBfFkg==', Base64)

### Getting String Representations of Data

Data objects have a `stringWithEncoding` method that takes an encoding object
that determines the output encoding. The code snippet below shows how to create
a Base58 encoded string from Data instance `d` above. 

	>>> dat = Data('ba58b7c4fbe6c19a', Base16)
	>>> dat.stringWithEncoding(Base58)
	'xaN7oqjfR4Y'

Likewise, a raw string of bytes may be converted to Doug Crockford's Base32.

	>>> uid = Data('\x97\x88\xf7V\xd4\x9aHE\x84=\xba\xec\xef\x08\xb88')
	>>> uid.stringWithEncoding(Base32)
	'JY4FENPMK944B11XQBPEY25R70'


### Accessing and Comparing Bytes

More info coming soon.


### Manipulating Data Objects

You can append data objects with the Python `+` operator:

	>>> Data('5ee8da1274a740e1', Base16) + Data('aa347f87669901aa', Base16)
	Data('XujaEnSnQOGqNH+HZpkBqg==', Base64)


The Data Class
--------------

The `Data` class is a thin wrapper around byte strings. As we saw previously,
the constructor has two forms. With one argument, it treats the `string`
argument as a binary byte string. If the optional `encoding` argument is
specified, the encoding object first decodes the string into a byte string.

Instances of `Data` objects provide a `stringWithEncoding()` method which also
takes an `encoding` argument. It returns the base-encoded representation of the
byte string using the specified encoding.

By default, calling `str()` on a Data object will result in a base 64 encoded
string representation of the internal byte string.

	>>> str(uid)
	'l4j3VtSaSEWEPbrs7wi4OA=='


The Encoding Class
------------------

Subclasses of `Encoding` must declare their alphabet and base, and may
optionally declare a dictionary of replacements. Encodings define two class
methods, `encode()` and `decode()`, which convert a byte string to a
base-encoded string and convert a base-encoded string into a byte string,
respectively.

Additionally, a private `_canonicalRepr()` class method allows the encoding
classes to be forgiving of some non-standard input. (Some base-encoded strings
are not case-sensitive, and may accept either upper- or lowercase inputs.)


### An Introduction to Base32

Looking briefly at the `Base32` encoding subclass, it defines class's `base`
property as 32, and provides the following alphabet:

	'0123456789ABCDEFGHJKMNPQRSTVWXYZ'

Note that the letters 'I', 'L', and 'O' are missing from the Base32 alphabet.
As Doug Crockford describes in his [Base32 specification](http://www.crockford.com/wrmg/base32.html) these
characters are often confused with the numerals '0' and '1'. (Base32 strings
also ignore hyphens and spaces.)

This is where the `replacements` dictionary comes in. The `_canonicalRepr()`
method iterates through the dictionary's keys and values and replaces
instances of the keys found in the `replacements` dictionary with their
associated values. The Base32 replacements dictionary is shown below:

	{
		'-': '',
		' ': '',
		'I': '1',
		'L': '1',
		'O': '0'
	}

When we canonicalize an input string like `LMPO5-QRKXY-DIGCR`, we simply
remove hyphens and spaces, and replace any occurrences of the letters 'I' or
'L' with the numeral '1', and any occurrences of the letter 'O' with the
numeral '0'. The canonicalized representation of the previous input would
therefore be `1MP05QRKXYD1GCR`.

Encoding and decoding the canonical string is now handled by the `Encoding`
base class's implementation of `encode()` and `decode()`.



### Using Base32 Encodings

As we saw above, the beauty of Base32 is that it's error-resistant. The
following example demonstrates this property.

	>>> normal = Data('110G', Base32)
	>>> silly = Data('ILOG', Base32)
	
	>>> normal == silly
	True

Note that the string we use to create the `silly` Data object uses the letters
'I', 'L', and 'O', which are not part of the Base32 alphabet. When the decode
method canonicalizes the input string, they are converted to the correct
characters before decoding.


### Creating Custom Encodings

A detailed tutorial on creating custom data encodings can be found [here](https://github.com/brendn/Trilobyte/blob/master/documentation/custom_encoding.md).
