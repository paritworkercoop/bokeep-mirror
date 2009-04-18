#!/bin/bash

THIS_SCRIPT_DIR=`dirname $BASH_SOURCE`

# convert possibly relative path to absolute
cd $THIS_SCRIPT_DIR
THIS_SCRIPT_DIR=`pwd`
BOKEEP_INSTALL="$THIS_SCRIPT_DIR/../"
DATA_DIR="$BOKEEP_INSTALL/share/"
BOKEEP_BIN="$BOKEEP_INSTALL/bin/"

USER_BOKEEP_DIR=~/bo-keep

if ! test -d $USER_BOKEEP_DIR; then \
    cp -ra "$DATA_DIR/bokeep_initialization" $USER_BOKEEP_DIR
fi

cd $USER_BOKEEP_DIR || exit 1
# convert relative path to absolute
USER_BOKEEP_DIR=`pwd`

if bizname=`zenity --entry --text="What is the business name?"`; then \
    mkdir "$bizname"
    if ! zenity --question --text \
"Would you like a new gnucash file to be created?
If you choose cancel, you will be prompted to find one that already 
exists"; then \
        if ! selected_file=`zenity --file-selection`; then \
            rmdir "$bizname"
	    exit 1
        fi
    else \
        selected_file="$bizname/books.gnucash"
	cp $DATA_DIR/bokeep_book_examples/books.gnucash $selected_file
    fi

    cp $DATA_DIR/bokeep_payroll_examples/* "$bizname"

    gnucash-env $BOKEEP_BIN/bo-keep-book-add "$bizname"
    gnucash-env $BOKEEP_BIN/bo_keep_module_control \
        "$bizname" add bokeep.modules.payroll
    gnucash-env $BOKEEP_BIN/bo_keep_module_control \
        "$bizname" enable bokeep.modules.payroll
    gnucash-env $BOKEEP_BIN/bo_keep_module_control "$bizname" \
        backend set bokeep.backend_modules.gnucash_backend
    gnucash-env $BOKEEP_BIN/bo_keep_module_control "$bizname" \
        backend setattr gnucash_file $USER_BOKEEP_DIR/$selected_file

    
fi