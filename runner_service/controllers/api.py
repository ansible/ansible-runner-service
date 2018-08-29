import os

from flask_restful import Resource
from flask import render_template, Response
from .utils import log_request

import logging
logger = logging.getLogger(__name__)


class API(Resource):
    """ Show available API endpoints (this page)"""
    app = None

    @log_request(logger)
    def get(self):

        app = API.app
        routes = []

        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                method_list = [m for m in sorted(list(rule.methods))
                               if m not in ["HEAD", "OPTIONS"]]
                doc_string = app.view_functions[rule.endpoint].__doc__

                details = dict()

                tgt = app.view_functions[rule.endpoint].view_class
                for method in method_list:
                    func = tgt.__dict__.get(method.lower())
                    if func.__doc__:
                        doc_as_list = [_d.lstrip()
                                       for _d in func.__doc__.split('\n')]
                        details[func.__name__.upper()] = doc_as_list

                routes.append(
                    {"route": rule.rule,
                     "description": doc_string,
                     "details": details,
                     "methods": method_list
                     }
                )

        srtd_routes = sorted(routes, key=lambda k: k['route'])
        template = os.path.join("api.html")
        return Response(render_template(template,
                                        routes=srtd_routes),
                        mimetype='text/html')
