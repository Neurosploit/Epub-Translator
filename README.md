Epub Translator using Azure Cognitive API translation
=======

See `runner.py` for example usage.
Create your own azurecongnitiveapi.key file in the epubtranslator folder with the api key on a single line to start using it (see gitignore).
Translates 33k characters a minute with limit of 2 million characters a month on free tier.
For further documentation on translation api limits see: https://docs.microsoft.com/en-us/azure/cognitive-services/translator/request-limits

Convert an epub book to another language or just replace some words with another.

Subclass `ConversionEngine` class and define your rules for translation.

An example ConversionEngine that transforms all worlds in the book to lower case would be:

    class SimpleConversionEngine(ConversionEngine):
    
        def convert(self, text):
         
            return text.lower()
            

All texts inside `<p>`, `<div>` etc tags are passed to `convert()` method, Text of one tag at a time.


Known issues
-----
- Multithreading is a bit buggy, not translating chapters sometimes.
- Does not translate table of contents yet.


Requirements
----
BeautifulSoup 4

Notes
----
- Be aware it's machine translation it isn't perfect but it's readable.
- For personal and educational use only. The author does not condone or is responsible for another individual using the software to translate a work/text (epub) without having permissions to do so.

Licence
----
BSD Licence
