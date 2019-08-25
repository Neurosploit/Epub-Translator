__author__ = 'sha256'

from bs4 import BeautifulSoup, NavigableString
from epubtranslator.updatablezipfile import UpdateableZipFile
from zipfile import ZIP_DEFLATED
import re
import shutil
from epubtranslator.threadedconvert import ThreadedConvert

class ConversionEngine(object):

    def convert(self, text, fromlang, tolang):
        raise NotImplementedError("Conversion Engine must be subclassed")


class BookProcessor(object):

    def __init__(self, conversion_engine, progress_callback=None):
        self._conversion_engine = conversion_engine
        self._callback = progress_callback

    def set_file(self, src_file, dest_file, fromlang, tolang):
        self._filepath = src_file
        self._destfile = dest_file
        self.fromlang = fromlang
        self.tolang = tolang

    def get_html_files_ref(self):
        htmlfiles = []

        with UpdateableZipFile(self._filepath, 'r') as f:
            foo = f.open('META-INF/container.xml')
            print(foo)
            soup = BeautifulSoup(foo, 'html.parser')
            foo.close()
            contentfile = dict(soup.find('rootfile').attrs)['full-path']
            # soup.close()

            root = re.sub(r'[^/]*(.opf)', '', contentfile)

            foo = f.open(contentfile)
            soup = BeautifulSoup(foo, 'html.parser')
            for item in soup.findAll('item'):
                itemdict = dict(item.attrs)
                if itemdict['href'].endswith('html'):
                    htmlfiles.append(root + itemdict['href'])

            foo.close()
            # soup.close()
            f.close()

        return htmlfiles

    def get_converted_html(self, soup):
        for nstring in soup.findAll(text=True):

            if type(nstring) is not NavigableString:
                continue

            if nstring.parent.name == "n":
                nstring.parent.replaceWithChildren()
                continue

            text = str(nstring).strip()

            if text:
                converted = self._conversion_engine.convert(text, self.fromlang, self.tolang)
                nstring.replaceWith(converted)

        return str.encode(str(soup))

    def convert(self):

        if self._destfile is None or self._filepath == self._destfile:
            self._destfile = self._filepath
        else:
            shutil.copyfile(self._filepath, self._destfile)

        htmls = self.get_html_files_ref()

        if self._callback:
            self._callback.update_state("total", len(htmls))

        with UpdateableZipFile(self._destfile, 'a', ZIP_DEFLATED) as f:
            threads = []
            for item in htmls:
                t = ThreadedConvert(self, item, f, self._callback)
                t.start()
                threads.append(t)

            for t in threads:
                t.join()

            f.close()

        if self._callback:
            self._callback.update_state("complete")