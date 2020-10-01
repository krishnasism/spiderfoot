# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:         sfp_debounce
# Purpose:      Spiderfoot plugin to check if an email is
#               disposable using Debounce API.
#
# Author:      Krishnasis Mandal <krishnasis@hotmail.com>
#
# Created:     2020-10-10
# Copyright:   (c) Steve Micallef
# Licence:     GPL
# -------------------------------------------------------------------------------

import json
from spiderfoot import SpiderFootEvent, SpiderFootPlugin

class sfp_debounce(SpiderFootPlugin):

    meta = {
        'name': "Debounce",
        'summary': "Check whether an email is disposable",
        'flags': ["apikey"],
        'useCases': ["Footprint", "Investigate", "Passive"],
        'categories': ["Search Engines"],
        'dataSource': {
            'website': "https://debounce.io/",
            'model': "FREE_AUTH_LIMITED",
            'references': [
                "https://debounce.io/email-verification-api/"
            ],
            'apiKeyInstructions': [
                "Visit https://debounce.io",
                "Register a free account",
                "Navigate to https://app.debounce.io/api",
                "Click on 'Create API Key'",
                "The API key is listed under 'KEY'"
            ],
            'favIcon': "https://debounce.io/wp-content/uploads/2018/01/favicon-2.png",
            'logo': "https://debounce.io/wp-content/uploads/2018/01/debounce-logo-2.png",
            'description': "DeBounce email list cleaning service allows you to upload "
            "and validate lists of email addresses quickly and securely.",
        }
    }

    opts = {
        'api_key': ''
    }

    optdescs = {
        "api_key": "API Key for debounce.io"
    }

    results = None
    errorState = False

    def setup(self, sfc, userOpts=dict()):
        self.sf = sfc
        self.results = self.tempStorage()

        for opt in list(userOpts.keys()):
            self.opts[opt] = userOpts[opt]

    def watchedEvents(self):
        return [
            "EMAILADDR"
        ]

    # What events this module produces
    def producedEvents(self):
        return [
            "EMAILADDR_DISPOSABLE",
            "RAW_RIR_DATA"
        ]

    def queryEmailAddr(self, qry):
        res = self.sf.fetchUrl(
            f"https://api.debounce.io/v1/?api={self.opts['api_key']}&email={qry}",
            timeout=self.opts['_fetchtimeout'],
            useragent="SpiderFoot"
        )

        if res['content'] is None:
            self.sf.info(f"No Debounce info found for {qry}")
            return None

        try:
            return json.loads(res['content'])
        except Exception as e:
            self.sf.error(f"Error processing JSON response from Debounce: {e}")

        return None

    # Handle events sent to this module
    def handleEvent(self, event):
        eventName = event.eventType
        eventData = event.data

        if self.errorState:
            return

        self.sf.debug(f"Received event, {eventName}, from {srcModuleName}")

        if self.opts["api_key"] == "":
            self.sf.error(
                f"You enabled {self.__class__.__name__} but did not set an API key!"
            )
            self.errorState = True
            return None

        if eventData in self.results:
            self.sf.debug(f"Skipping {eventData}, already checked.")
            return

        self.results[eventData] = True

        content = self.queryEmailAddr(eventData)

        if content is None:
            return
        
        data = json.loads(content)
        
        evt = SpiderFootEvent("RAW_RIR_DATA", str(data), self.__name__, event)
        self.notifyListeners(evt)

        isFreeEmail = data.get('free_email')
        if isFreeEmail:
            evt = SpiderFootEvent("EMAILADDR_DISPOSABLE", eventdata, self.__name__, event)
            self.notifyListeners(evt)
        
# End of sfp_debounce class
