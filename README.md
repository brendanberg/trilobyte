# Trilobyte

Trilobyte is a collection of classes for storing binary data and converting it
into various base-encoded strings for text representations useful for over-the-
wire transmission.

The library's core consists of the `Data` class, which is an opaque wrapper
class for byte strings. (Using string notation for binary data is perhaps one
of Python's more problematic quirks, but we do not question the BDFL.) In
addition, the `Encoding` class provides an abstract interface for various
encoding implementations. Trilobyte provides classes that implement base 16,
Doug Crockford's base 32, Flickr's base 58, and base 64 encodings.

This document describes the motivation and implementation of the Trilobyte
library.

## Data Programming Guide

Data objects are opaque wrappers for a string of bytes. Its constructor takes
an encoded string and an encoding specifier. (Encoding specifiers are
discussed later.)

	>>> d = Data('ba58b7c4fbe6c19a', Base16)

Data objects have a `stringWithEncoding` method that takes an encoding object
that determines the output encoding. The code snippet below shows how to create
a Base58 encoded string from Data instance `d` above. 

	>>> d.stringWithEncoding(Base58)
	'xaN7oqjfR4Y'

By omitting the encoding object in the `Data()` constructor, you can create a
Data object with a raw byte string you may already have. (For example, the
expression `uuid4().bytes` results in a raw byte string that can be wrapped in
a Data object.

	>>> uid = Data('\x97\x88\xf7V\xd4\x9aHE\x84=\xba\xec\xef\x08\xb88')
	>>> uid.stringWithEncoding(Base32)
	'1RQ04EZV5T7P24AJ4TTHBFF24Q'

By default, calling `str()` on a Data object will result in a base 64 encoded
string representation of the internal byte string.

	>>> str(uid)
	'l4j3VtSaSEWEPbrs7wi4OA=='

## The Data Class

The `Data` class is a thin wrapper around byte strings. As we saw previously,
the constructor has two forms. With one argument, it treats the `string`
argument as a binary byte string. If the optional `encoding` argument is
specified, the encoding object first decodes the string into a byte string.

Instances of `Data` objects provide a `stringWithEncoding()` method which also
takes an `encoding` argument. It returns the base-encoded representation of the
byte string using the specified encoding.

## The Encoding Class

Subclasses of `Encoding` must declare their alphabet and base, and may
optionally declare a dictionary of replacements. Encodings define two class
methods, `encode()` and `decode()`, which convert a byte string to a
base-encoded string and convert a base-encoded string into a byte string,
respectively.

Additionally, a private `_canonicalRepr()` class method allows the encoding
classes to be forgiving of some non-standard input. (Some base-encoded strings
are not case-sensitive, and may accept either upper- or lowercase inputs.)

### A brief tour of Base32

Looking briefly at the `Base32` encoding subclass, it defines class's `base`
property as 32, and provides the following alphabet:

	'0123456789ABCDEFGHJKMNPQRSTVWXYZ'

Note that the letters 'I', 'L', and 'O' are missing from the Base32 alphabet.
As Doug Crockford describes in his [Base32 specification][spec] these
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

When we canonicalize an input string like `LMPO5-QRKXY-DIGCT`, we effectively
remove hyphens and spaces, and we replace any 'I' or 'L' with the numeral '1',
and any 'O' with the numeral '0'.

Encoding and decoding the canonical string is now handled by the `Encoding`
base implementation of `encode()` and `decode()`.

[spec]: (http://www.crockford.com/wrmg/base32.html)