#!/usr/bin/python

import sys
import os
import getopt
import requests
from xml.dom.minidom import parseString as parse_xml


class XsdDownloader:
    XSD_NS = "http://www.w3.org/2001/XMLSchema"
    XSD_INTERNAL_DIR = "internal"

    def __init__(self, xsd_url, out_dir=None):
        self.xsd_map = {}
        self.xsd_url = xsd_url
        if not out_dir:
            out_dir = os.path.realpath(os.path.curdir)
        self.out_dir = out_dir

    def download(self):
        inner_dir_path = self.out_dir + "/" + self.XSD_INTERNAL_DIR
        if not os.path.isdir(inner_dir_path):
            os.mkdir(inner_dir_path)

        self.__download_xsd(self.xsd_url)

    def __download_xsd(self, url):
        is_root = self.xsd_url == url

        if url not in self.xsd_map:
            xsd_local_name = self.__get_local_name(url)
            xsd_local_path = self.__get_local_path(xsd_local_name, is_root)

            dom = parse_xml(self.__download_url(url))

            self.xsd_map[url] = xsd_local_name
            self.__resolve_imports(dom, is_root)
            self.__resolve_includes(dom, is_root)

            with open(xsd_local_path, 'wb') as f:
                f.write(dom.toxml('UTF-8'))

        return self.xsd_map[url]

    @staticmethod
    def __download_url(url):
        print "Downloading %s " % url
        return requests.get(url).text.encode('UTF-8')

    def __get_local_name(self, url):
        # get last url segment
        return url.rsplit('/', 1)[-1]

    def __get_local_path(self, name, is_root):
        segments = [self.out_dir]
        if not is_root:
            segments.append(self.XSD_INTERNAL_DIR)
        segments.append(name)

        return "/".join(segments)

    def __resolve_imports(self, dom, is_root=False):
        self.__do_resolve(dom.getElementsByTagNameNS(self.XSD_NS, "import"), is_root)

    def __resolve_includes(self, dom, is_root=False):
        self.__do_resolve(dom.getElementsByTagNameNS(self.XSD_NS, "include"), is_root)

    def __do_resolve(self, externals, is_root):
        for external in externals:
            schema_location = external.attributes["schemaLocation"]

            local_path = self.__download_xsd(schema_location.value)
            if is_root:
                local_path = self.XSD_INTERNAL_DIR + "/" + local_path

            schema_location.value = local_path


class Application:
    def __init__(self):
        self.xsd_url = None
        self.out_dir = None

    def configure(self, argv):
        try:
            opts, args = getopt.getopt(argv[1:], "hu:o:", ["help", "xsd-url=", "output-dir="])
        except getopt.GetoptError:
            self.__usage(argv)
            sys.exit(2)

        for opt, arg in opts:
            if opt == '-h':
                self.__usage(argv)
                sys.exit(0)
            elif opt in ("-u", "--xsd-url"):
                self.xsd_url = arg
            elif opt in ("-o", "--output"):
                self.out_dir = os.path.realpath(arg)

        if not self.xsd_url:
            self.__usage(argv)
            sys.exit(1)

    def run(self):
        downloader = XsdDownloader(self.xsd_url, self.out_dir)
        downloader.download()

    def __usage(self, argv):
        print "%s --xsd-url <XSD_URL> --output-dir <OUTPUT_DIR>" % argv[0]


if __name__ == "__main__":
    app = Application()
    app.configure(sys.argv)
    app.run()
