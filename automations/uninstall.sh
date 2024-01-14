#!/usr/bin/env bash

library_name="akr_ext_animepahe"
if pip show "$library_name" &> /dev/null; then
    echo "Uninstalling..."
    pip uninstall "$library_name" <<< "y"
fi