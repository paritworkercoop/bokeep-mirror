#!/bin/bash

THIS_SCRIPT_DIR=`dirname $BASH_SOURCE`

# convert possibly relative path to absolute
cd $THIS_SCRIPT_DIR
THIS_SCRIPT_DIR=`pwd`
BOKEEP_INSTALL="$THIS_SCRIPT_DIR/../"
DATA_DIR="$BOKEEP_INSTALL/share/"
BOKEEP_BIN="$BOKEEP_INSTALL/bin/"

USER_BOKEEP_DIR=~/bo-keep

cd $USER_BOKEEP_DIR

bizs=''
for candidate in ls *; do \
    if test -d $candidate; then bizs="$bizs $candidate"; fi
done
choice=`zenity --text "choose a business/organization" \
    --list --column="business/organization" $bizs`

PYTHONPATH="$PYTHONPATH:$choice" exec gnucash-env \
$BOKEEP_BIN/bo_keep_payroll.py $choice payday run
