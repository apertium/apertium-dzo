# Algorithm to calculate weight/possibility for unknown tokenized analyses based on an input corpus

total_iters = 200
syllable_boundary = '་'
sentence_ending = '།'
alpha_var = 1
cache_num = 0

# Micro-story for word generation: (C total chunks in the corpus)
# 0. Word = empty
# 1. Pick a chunk character from the uniform distribution (1/C), more frequent chunks will have bigger overall probability
# 2. Add the chunk to the end of the word.
# 3. With probability 0.5, go to 1;
#    With probability 0.5, quit and output word.

chunk_gen = 0.5

# Generative story for the word sequence:
# H = 0 (H is the length of the history, the number of decisions taken so far)
# 1. With probability a/(a+H), generate a Dzongkha word according to the base distribution P0
# With probability H/(a+H), generate a Dzongkha word using the cache of words generated so far
# 2. Write down the word just chosen.
# 3. With probability 0.99,
# H = H + 1
# go to step 1 (and continue outputting words)
#    With probability 0.01, quit.

word_gen = 0.99

# Possibility/Weight for some derivation over a sequence w is calculated using the above.

#Base probability score of a given word (chunk sequence)
def prob_word(corpus, cur_word):
    #Probability score
    prob_score = 1.0
    #total number of chunks
    a = len(corpus)
    #calculate the probability score for the word through the micro-story
    for chunk in cur_word:
        prob_score = prob_score / a * chunk_gen
    prob_score = prob_score / chunk_gen * (1.0 - chunk_gen)
    return prob_score

#Probability score of a given derivation over a sequence
def prob_derivation(corpus, words, occurences):
    #Probability score
    prob_score = 1.0
    #calculate the probability score for the entire sequence through the micro-story
    for i in range(0, len(words)):
        oc_num = 0
        #Check if word is represented in occurences, if it is, note the number of times it has already appeared, and add 1 to occurences
        for oc in occurences:
            if words[i] == oc[0]:
                oc_num = oc[1]
                oc[1] += 1
        prob_score *= (alpha_var * prob_word(corpus, words[i]) + oc_num) / (alpha_var + i + cache_num) * word_gen
        #If word is not represented, push an entry to occurences
        if oc_num == 0:
            occurences.append([words[i],1])
    #Bandaid fix for prob_score
    prob_score = prob_score / word_gen * (1-word_gen)
    return prob_score

def add_count(words, occurences):
    global cache_num
    #For each word in this sequence of words
    for word in words:
        #Check if word is represented in occurences, if it is, add 1 to occurences
        flag = 0
        for oc in occurences:
            if word == oc[0]:
                oc[1] += 1
                flag = 1
                break
        #If word is not represented, push an entry to occurences
        if flag == 0:
            occurences.append([word,1])
    #Update total number of words seen
    cache_num += len(words)

#Changes the current sample based on probability score of possible changes
def new_sampling(corpus, words, occurences, cur_prob):
    #Set up change probability score
    change_prob = cur_prob
    #The words if the proposed change takes place
    change_words = []
    while True:
        #Choose a random changeable cut place
        i = randint(0, len(corpus))
        #If unchangeable, choose again
        if(corpus[i][1] == 2):
            continue
        #If changeable, evaluate the probability scores of changing
        else:
            #If we are proposing cutting a word
            if(corpus[i][1] == 0):
                corpus[i][1] = 1
                cur_word = []
                #Read new list of words
                for chunk in corpus:
                    #Add chunk to current word
                    cur_word.append(chunk[0])
                    #If chunk says cut, push to changed words
                    if chunk[1] != 0:
                        change_words.append(cur_word)
                        #Clear cur_word
                        cur_word = []
                change_prob = prob_derivation(corpus, change_words, occurences[:])
                if(randrange() < cur_prob/(cur_prob + change_prob)):
                    corpus[i][1] = 0
                    occurences = add_count(words, occurences)
                else:
                    words = change_words
                    occurences = add_count(words, occurences)
            #If we are proposing merging two words to one
            else:
                corpus[i][1] = 0
                cur_word = []
                #Read new list of words
                for chunk in corpus:
                    #Add chunk to current word
                    cur_word.append(chunk[0])
                    #If chunk says cut, push to changed words
                    if chunk[1] != 0:
                        change_words.append(cur_word)
                        #Clear cur_word
                        cur_word = []
                change_prob = prob_derivation(corpus, change_words, occurences[:])
                if(randrange() < cur_prob/(cur_prob + change_prob)):
                    corpus[i][1] = 1
                    occurences = add_count(words, occurences)
                else:
                    words = change_words
                    occurences = add_count(words, occurences)
            break

#Inits the sampling
def init_sampling(tokenizer, sin):
    alpha = tokenizer.get_alphabet()
    #The entire input, divided into chunks, each chunk has a mark on whether we cut after it to make a word
    corpus = []
    #Counting word appearances
    #For each word, record what is it in [0] and the number of times it has appeared before in [1], starting with
    words = []
    cut = 0;
    #Chunk management
    cur_chunk = ''
    #Word (Chunk combination) management
    cur_word = []
    #Number of select word appearances
    occurences = []
    while True:
        #Reads in characters one by one
        c = sin.read(1)
        if c == syllable_boundary:
            #Randomly decides to cut after a Dzongkha character, can only occur after "་"
            cur_chunk += c
            if(random.randrange() < 0.2):
                #20% possibility it does not cut the word at this but marks it as potential cutting place"་"
                cut = 0
            else:
                #80% possibility that it cuts here and calls it a word
                cut = 1
            places += 1
            corpus.append([cur_chunk,cut])
            cur_chunk = ''
        elif c == sentence_ending:
            #Sentence-ending punct, 100% cut and cannot be bridged across
            #To analyze as word form, adds to corpus '་' instead
            cur_chunk += syllable_boundary
            #sentence_ending means impossible bridge, so we put a "unchangeable" cut mark here
            cut = 2
            corpus.append([cur_chunk,cut])
            cur_chunk = ''
        elif c in alpha:
            #Adds to current chunk
            cur_chunk += c
        elif c:
            #If the character is a whitespace, this means that the previous chunk should be given a "unchangeable" cut mark,
            # regardless of what it was given
            temp = corpus.pop()
            temp[1] = 2
            corpus.append(temp)
        else:
            #Upon reaching the end of the input stream, break
            break
    for chunk in corpus:
        #Add chunk to current word
        cur_word.append(chunk[0])
        #If chunk says cut, push to words
        if chunk[1] != 0:
            words.append(cur_word)
            #Clear cur_word
            cur_word = []
    cur_prob = prob_derivation(corpus, words, occurences[:])
    add_count(words, occurences)
    for i in range(1, total_iters):
        new_sampling(corpus, words, occurences)
    return occurences


if __name__ == '__main__':
    import argparse
    prs = argparse.ArgumentParser(description='Segment input stream using HFST')
    prs.add_argument('transducer')
    args = prs.parse_args()
    stream_tok = hfst.HfstInputStream(args.transducer)
    tokenizer = hfst.HfstBasicTransducer(stream_tok.read())
    with open('blah.txt') as sin:
        out = init_sampling(tokenizer, sin)
    print(out)
