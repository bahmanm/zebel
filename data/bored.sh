#!/bin/sh
curl -XPOST 'localhost:9200/zebel_quotes/bored/_bulk?pretty' -d '
{"index": {"_index": "zebel_quotes", "_type": "bored"}}
{ "text": "YOUR MESSAGE GOES HERE - COPY THIS LINE AND THE ONE ABOVE TO ADD ANOTHER MESSAGE." }
'
