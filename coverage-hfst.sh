#!/bin/bash

CORPUS=dzo1.corpus.basic1.txt
ANALYSER=dzo.automorf.hfst
LG=$(echo $CORPUS | sed 's:.*\/::' | sed -E 's:(.*\..*)\..*\.txt.*:\1:') # get corpus prefix

TMPCORPUS=/tmp/$LG.corpus.txt

if [[ $1 =~ .*bz2 ]]; then
	CAT="bzcat"
else
	CAT="cat"
fi;

$CAT $CORPUS > $TMPCORPUS

echo "Generating hitparade (might take a bit!)"

cat $TMPCORPUS | apertium-destxt | hfst-proc -w $ANALYSER | python3 tokenizer.py | apertium-retxt | sed -E $'s/\\$[^^]*/\\$\\\n/g' > /tmp/$LG.parade.txt

echo "TOP UNKNOWN WORDS:"

cat /tmp/$LG.parade.txt | grep '\*' | sort | uniq -c | sort -rn | head -n20

TOTAL=`grep -v '^$' /tmp/$LG.parade.txt | wc -l`
KNOWN=`grep -v '^$' /tmp/$LG.parade.txt | grep -v '\*' | wc -l`
UNKNOWN=`grep -v '^$' /tmp/$LG.parade.txt | grep '\*' | wc -l`

PERCENTAGE=`echo $KNOWN/$TOTAL | calc -p | sed 's/[\s\t]//g'`

echo "coverage: $KNOWN / $TOTAL ($PERCENTAGE)"
echo "remaining unknown forms: $UNKNOWN"

DATE=`date`;
echo -e $LG $DATE"\t"$KNOWN"/"$TOTAL"\t"$PERCENTAGE >> history.log
tail -1 history.log
rm $TMPCORPUS /tmp/$LG.parade.txt
