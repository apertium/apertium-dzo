#!/usr/bin/env python3

# to run you'll need to 'sudo apt-get install python3-hfst' or equivalent
# pip might also work though see https://github.com/hfst/hfst/issues/448

# usage:
# copy to directory and in modes.xml add as first step:
# <program name="python3">
#   <file name="tokenize.py"/>
#   <file name="[code].automorf.hfst"/>
# </program>
# this will insert spaces so that analysis won't get stuck

import hfst

def list_options(spans, start, wlen):
    if start == wlen:
        yield []
    for i in range(start, wlen):
        if i in spans:
            for j in spans[i]:
                for op in list_options(spans, j, wlen):
                    yield [(i,j)] + op
        yield from list_options(spans, i+1, wlen)

def weight_options(spans, wlen):
    for op in list_options(spans, 0, wlen):
        unk_count = len(op)-1
        if len(op) == 0:
            unk_count = 1
        else:
            if op[0][0] != 0:
                unk_count += 1
            if op[-1][1] != wlen:
                unk_count += 1
        n = 0
        unk_len = 0
        for i,j in op:
            if (i - n) > 0:
                unk_len += (i - n)
            n = j
        if n < wlen:
            unk_len += (wlen - n)
        yield (op, unk_count, unk_len)

def process_word(word, analyzer, sout):
    spans = {}
    for i in range(len(word)):
        ls = []
        for j in range(i+1, len(word)+1):
            if len(analyzer.lookup(word[i:j])) != 0:
                ls.append(j)
        if ls:
            spans[i] = list(reversed(ls))
            # put the longest option first
            # so we can approximate LRLM when we randomize
    mins = []
    min_count = len(word)
    min_len = len(word)
    for op, count, ln in weight_options(spans, len(word)):
        if ln > min_len:
            continue
        elif (ln == min_len) and (count > min_count):
            continue
        elif (ln == min_len) and (count == min_count):
            mins.append(op)
        else:
            mins = []
            mins.append(op)
            min_count = count
            min_len = ln
    sout.write(' ')
    n = 0
    for i,j in mins[0]:
        if n < i:
            sout.write(word[n:i] + ' ')
        sout.write(word[i:j] + ' ')
        n = j
    if n < len(word):
        sout.write(word[n:] + ' ')

def process_stream(analyzer, sin, sout):
    alpha = analyzer.get_alphabet()
    cur_word = ''
    while True:
        c = sin.read(1)
        if c in alpha:
            cur_word += c
        else:
            if cur_word:
                process_word(cur_word, analyzer, sout)
            if c:
                cur_word = ''
                sout.write(c)
            else:
                break

if __name__ == '__main__':
    import argparse
    prs = argparse.ArgumentParser(description='Segment input stream using HFST')
    prs.add_argument('transducer')
    args = prs.parse_args()
    stream = hfst.HfstInputStream(args.transducer)
    analyzer = stream.read()
    import sys
    process_stream(analyzer, sys.stdin, sys.stdout)
