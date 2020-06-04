# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:         sfp__stor_es
# Purpose:      SpiderFoot plug-in for storing events to Elasticsearch instance
#
# Author:      Krishnasis Mandal <krishnasis@hotmail.com>
#
# Created:     04/06/2020
# Copyright:   (c) Steve Micallef
# Licence:     GPL
# -------------------------------------------------------------------------------

from sflib import SpiderFoot, SpiderFootPlugin
from elasticsearch import Elasticsearch

class sfp__stor_es(SpiderFootPlugin):
    """Elastic Search Storage::::Stores scan results into Elasticsearch instance."""
    _priority = 0

    # Default options
    opts = {
        'endpoint_url': "",
        'username': "",
        'password': "",
        '_store': True,
    }

    # Option descriptions
    optdescs = {
        'endpoint_url': "Endpoint URL to Elasticsearch instance",
        'username': "Elasticsearch username",
        'password': "Elasticsearch password"
    }

    def setup(self, sfc, userOpts=dict()):
        self.sf = sfc

        for opt in list(userOpts.keys()):
            self.opts[opt] = userOpts[opt]

    # What events is this module interested in for input
    # Because this is a storage plugin, we are interested in everything so we
    # can store all events for later analysis.
    def watchedEvents(self):
        return ["*"]

    # Handle events sent to this module
    def handleEvent(self, sfEvent):
        if not self.opts['_store']:
            self.sf.debug("Disabled storing on Elasticsearch")
            return None

        try:
            self.sf.debug("Creating client")
            
            esClient = Elasticsearch([self.opts['endpoint_url']], http_auth=(self.opts['username'], self.opts['password']))
            self.sf.debug(str(esClient))
            
            sfEventJSON = sfEvent.asDict()
            self.sf.debug(str(sfEventJSON))
            
            response = esClient.index(index=sfEvent.eventType.lower(), doc_type='SpiderFoot', body=sfEventJSON)
            self.sf.debug(str(response))

        except Exception as e:
            import traceback
            self.sf.error(str(traceback.format_exc()), False)

            self.sf.error(str(e), False)

        self.sf.debug("Storing an event to Elasticsearch: " + sfEvent.eventType)

# End of sfp__stor_es class
