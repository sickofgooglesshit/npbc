#!/bin/bash
pyinstaller -F --add-data includes/config.json:includes --add-data includes/undelivered_help.pdf:includes --distpath bin npbc.py