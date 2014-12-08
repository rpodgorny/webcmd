#!/usr/bin/python3

'''
webcmd.

Usage:
  webcmd --port=<port>
'''

__version__ = '0.0'

import cherrypy
from mako.template import Template
import subprocess
import os
import traceback
import docopt
import logging


class Server():
	def __init__(self, cmds):
		self.cmd_map = {}
		cmds_ids = []
		for title, cmd in cmds:
			cmd_id = len(self.cmd_map)
			self.cmd_map[cmd_id] = cmd
			cmds_ids.append((title, cmd_id))
		#endfor

		self.lines = []
		cmds_ids_to_go = cmds_ids.copy()
		while cmds_ids_to_go:
			self.lines.append(cmds_ids_to_go[:2])
			cmds_ids_to_go = cmds_ids_to_go[2:]
		#endwhile

		t = Template(filename='index.tmpl')
		self.index_html = t.render(lines=self.lines)
	#enddef

	@cherrypy.expose
	def index(self):
		return self.index_html
	#enddef

	@cherrypy.expose
	def run(self, cmd_id):
		cmd = self.cmd_map[int(cmd_id)]

		logging.debug('will execute "%s"' % cmd)
		out = subprocess.check_output(cmd, shell=True)

		cherrypy.response.headers['Content-Type']= 'text/plain'
		return out
	#enddef
#endclass


def read_commands(fn):
	ret = []

	with open(fn, 'r') as f:
		for line in f.readlines():
			if not ':' in line:
				raise Exception('malformed line: "%s"' % line)
			#endif

			title, command = line.split(':', maxsplit=1)
			title = title.strip()
			command = command.strip()

			ret.append((title, command))
		#endfor
	#endwith

	return ret
#enddef


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
#enddef


if __name__ == '__main__':
	main()
#endif
