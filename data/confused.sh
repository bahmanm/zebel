#!/bin/sh
curl -XPOST 'localhost:9200/zebel_quotes/confused/_bulk?pretty' -d '
{"index": {"_index": "zebel_quotes", "_type": "confused"}}
{ "text": "YOUR MESSAGE GOES HERE - COPY THIS LINE AND THE ONE ABOVE TO ADD ANOTHER MESSAGE." }
'