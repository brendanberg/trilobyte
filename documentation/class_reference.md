Trilobyte Class Reference
=========================

The following sections outline the inner workings of the Trilobyte library.


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
