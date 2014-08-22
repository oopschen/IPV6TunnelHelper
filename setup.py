import os

from distutils.core import setup


pkg_scripts = "linux/*.sh"
if "nt" == os.name:
    pkg_scripts = "win7/*.bat"


setup(name='X6Tunnel',
      version='0.2.0',
      description='IPV6 Tunnel helper to make life easier. Current support HE(http://tunnelbroker.net/) only.',
      author='Ray',
      author_email='linxray@gmail.com',
      url='https://github.com/oopschen/IPV6TunnelHelper',
      scripts=['xtunnel'],

      package_data={
          'x6tunnel': [pkg_scripts],
          "spiderx.core": ["log.conf.default"],
          },

      packages = [
          'spiderx',
          "spiderx.core",
          "spiderx.xml",
          "spiderx.xml.sax",
          "spiderx.httpclient",
          "spiderx.net",
          "x6tunnel"
        ],

     )
