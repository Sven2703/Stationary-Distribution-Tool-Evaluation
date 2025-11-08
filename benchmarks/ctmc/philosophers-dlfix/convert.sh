#!/bin/bash

for i in {3..20}
do
    echo "Converting philosophers$i.PNPRO"
    ~/storm/build/bin/storm-gspn --gspnfile philosophers-dlfix.$i.PNPRO --to-jani philosophers-dlfix.$i.jani  --capacity 1
done