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
from elasticsearch import Elasticsearch, AuthenticationException, ConnectionError, ConnectionTimeout, AuthorizationException, NotFoundError

class sfp__stor_es(SpiderFootPlugin):
    """Elastic Search Storage::::Stores scan results into Elasticsearch instance."""
    
    _priority = 0

    # Default options
    opts = {
        'endpoint_url': "",
        'username': "",
        'password': "",
        'max_retries': 0,
        'index': "spiderfoot"
        '_store': True,
    }

    # Option descriptions
    optdescs = {
        'endpoint_url': "Endpoint URL to Elasticsearch instance",
        'username': "Elasticsearch username",
        'password': "Elasticsearch password",
        'index': "Specify the index of data to be stored in Elasticsearch (lowercase)"
        'max_retries': "No. of times Spiderfoot should retry connecting to Elasticsearch endpoint in case of a failure"
    }

    errorState = False  

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

        if self.errorState:
            return None

        if not self.opts['_store']:
            self.sf.debug("Disabled storing on Elasticsearch")
            return None
        
        tries = int(self.opts['max_retries']) + 1
        tries = 2

        index = self.opts['index'].lower()

        for i in range(0, tries):

            try:       
                
                # Unique ID to identify the data
                dataID = self.sf.GUID + sfEvent.getHash()     

                esClient = Elasticsearch([self.opts['endpoint_url']], http_auth=(self.opts['username'], self.opts['password']), timeout=15, verify_certs=False)
                
                sfEventJSON = sfEvent.asDict()
                
                response = esClient.index(index=index, id=dataID, doc_type='SpiderFoot', body=sfEventJSON)

                if response['result'] == "created":
                    self.sf.debug("Storing an event to Elasticsearch: " + sfEvent.eventType)
                
            except AuthenticationException:

                self.sf.error("Invalid credentials provided", False)
                self.errorState = True
                return None
            
            except ConnectionError:
              
               # If maximum number of retry attempts is reached, it's an error
                if i < tries - 1:
                    self.sf.debug("Could not connect to Elasticsearch endpoint. Retrying connection.")
                    continue         
                
                self.sf.error("Could not connect to Elasticsearch endpoint. Please verify your endpoint URL", False)
                
                self.errorState = True
                return None

            except AuthorizationException:
                self.sf.error("User not authorized to perform inserts into Elasticsearch cluster.", False)
                self.errorState = True
                return None

            except NotFoundError:
                self.sf.error("Failed to locate the Elasticsearch resource. Please verify your endpoint URL", False)
                self.errorState = True
                return None

            except Exception as e:
                
                self.sf.error("An exception occured : " + str(e))
                return None


# End of sfp__stor_es class
