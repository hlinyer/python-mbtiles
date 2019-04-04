import tornado.ioloop
import tornado.web
import os
import configparser
from mbtiles import MbtileSet

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('''
        <h1> Sample URLs </h1>
        <ul>
          <li> <a href="/test/6/10/40.png">PNG</a> (/test/6/10/40.png)</li>
          <li> <a href="/test/6/10/40.json">UTFGrid JSON</a> (/test/6/10/40.json)</li>
          <li> <a href="/test/6/10/40.json?callback=test">UTFGrid JSONP wrapped in "test()" callback</a> (/test/6/10/40.png?callback=test)</li>
        </ul>
        ''')

class MbtilesHandler(tornado.web.RequestHandler):
    def initialize(self, ext, mbtiles):
        self.ext = ext
        self.mbtiles = mbtiles
        self.tileset = MbtileSet(mbtiles=mbtiles)

    def get(self, z, x, y):
        origin = self.get_arguments('origin')
        try:
            origin = origin[0]
        except IndexError:
            origin = 'bottom' 

        if origin == 'top':
            # invert y axis to top origin
            ymax = 1 << int(z);
            y = ymax - int(y) - 1;

        tile = self.tileset.get_tile(z, x, y) 
        if self.ext == 'png':
            self.set_header('Content-Type', 'image/png')
            self.write(tile.get_png())
        elif self.ext == 'json':
            callback = self.get_arguments('callback')
            try:
                callback = callback[0]
            except IndexError:
                callback = None

            self.set_header('Content-Type', 'application/json')
            if callback:
                self.write("%s(%s)" % (callback, tile.get_json()))
            else:
                self.write(tile.get_json())


if __name__ == "__main__":
    urls = [(r"/", MainHandler),]

    thisdir = os.path.abspath(os.path.dirname(__file__))
    tilesets = []

    # get tilesets from configuration
    config = configparser.ConfigParser()
    try:
        config.read('mbtiles_bases.conf')
    except Exception as e:
        exit('no configuration file found, exiting...')
    for database in config:
        if database != 'DEFAULT':
            try:
                base_name = config.get(database,'name')
                base_path = config.get(database,'path')
                base_formats = config.get(database,'formats')
                tilesets.append((base_name, os.path.join(thisdir, base_path), base_formats.split(',')))
            except Exception as e:
                exit('Wrong configuration for base ' + database + '. Check the configuration files. ' + e)

    for t in tilesets:
        for ext in t[2]:
            urls.append(
                (r'/%s/([0-9]+)/([0-9]+)/([0-9]+).%s' % (t[0],ext), 
                    MbtilesHandler, 
                    {"ext": ext, "mbtiles": t[1]}
                )
            )

    application = tornado.web.Application(urls, debug=True)
    application.listen(8090)
    tornado.ioloop.IOLoop.instance().start()
