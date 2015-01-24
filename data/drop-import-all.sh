#!/bin/sh
curl -XDELETE 'localhost:9200/zebel_quotes'
./annoyed.sh
./bored.sh
./confused.sh
./general.sh