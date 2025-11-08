#!/bin/bash

for i in {3..20}
do
    echo "Converting philosophers$i.PNPRO"
    ~/storm/build/bin/storm-gspn --gspnfile philosophers-dl.$i.PNPRO --to-jani philosophers-dl.$i.jani  --capacity 1
done
