#!/usr/bin/python3

'''
webcmd.

Usage:
  webcmd --port=<port>
'''

__version__ = '1.0'

import cherrypy
from mako.template import Template
import subprocess
import os
import docopt
import logging
import sys


class Server():
	def __init__(self, cmds):
		self.cmd_map = {}
		lines = []
		for row in cmds:
			line = []
			for title, cmd in row:
				cmd_id = len(self.cmd_map)
				self.cmd_map[cmd_id] = cmd
				line.append((title, cmd_id))
			lines.append(line)
		t = Template(filename='index.tmpl')
		self.index_html = t.render(lines=lines)

	@cherrypy.expose
	def index(self):
		return self.index_html

	@cherrypy.expose
	def run(self, cmd_id):
		cmd = self.cmd_map[int(cmd_id)]
		logging.debug('will execute "%s"' % cmd)
		out = subprocess.check_output(cmd, shell=True)
		cherrypy.response.headers['Content-Type'] = 'text/plain'
		return out


def read_commands(fn):
	ret = []
	row = []
	with open(fn, 'r') as f:
		for line in f.readlines():
			line = line.strip()
			if not line or line.startswith('#'):
				continue
			if line == '---':
				ret.append(row)
				row = []
				continue
			if ':' not in line:
				raise Exception('malformed line: "%s"' % line)
			title, command = line.split(':', maxsplit=1)
			title = title.strip()
			command = command.strip()
			row.append((title, command))
	if row:
		ret.append(row)
	return ret


def main():
	args = docopt.docopt(__doc__, version=__version__)

	logging.basicConfig(level='DEBUG')

	port = int(args['--port'])

	cmds = read_commands('commands.txt')

	cherrypy.server.socket_host = '::'
	cherrypy.server.socket_port = port
	#cherrypy.server.thread_pool = 1
	#cherrypy.checker.on = False
	cherrypy.engine.autoreload.unsubscribe()

	# TODO: maybe tweak number of threads
	cherrypy.config.update({
		'engine.autoreload.on': False,
		'tools.proxy.on': True,  # retain the original address if we're being forwarded to
	})

	static_handler = cherrypy.tools.staticdir.handler(section='/', dir='%s/static' % os.getcwd())
	cherrypy.tree.mount(static_handler, '/static')

	cherrypy.quickstart(Server(cmds))
	return 0


if __name__ == '__main__':
	sys.exit(main())
