import difflib

Q = []
A = []
HQues = []
HAns = []
words = []
tokens = []

def get_data():
    with open('kgbBot/static_data/data.txt', 'r', encoding='utf-8') as file:
        for line in file:
            question, answer = line.strip().split(':')
            Q.append(question.strip())
            A.append(answer.strip())

def get_tokens():
    with open('kgbBot/static_data/tokens.txt', 'r', encoding='utf-8') as file:
        for line in file:
            word, token = line.strip().split(':')
            words.append(word.strip())
            tokens.append(token.strip())



def word_to_token(word, words_list, tokens_list):
    if word != ' ':
        try:
            index = words_list.index(word)
            return tokens_list[index]
        except ValueError:
            return None
    else:
        return ' '

def token_to_word(token, words_list, tokens_list):
    try:
        index = tokens_list.index(token)
        return words_list[index]
    except ValueError:
        return None

def sentence_to_tokens(sentence, words_list, tokens_list):
    words = sentence.split()
    new_tokens = []

    for word in words:
        token = word_to_token(word, words_list, tokens_list)
        if token is None:
            new_token = str(len(tokens_list) + 1)
            new_tokens.append(new_token)
            with open("kgbBot/static_data/tokens.txt", 'a', encoding='utf-8') as file:
                file.write(f"{word}:{new_token}\n")
            words_list.append(word)
            tokens_list.append(new_token)
        else:
            new_tokens.append(token)

    return [tokens_list[int(token) - 1] for token in new_tokens]

def tokens_to_sentence(tokens, words_list, tokens_list):
    words = [token_to_word(token, words_list, tokens_list) for token in tokens]
    words = [word for word in words if word is not None]
    if words:
        words[0] = words[0].capitalize()
    sentence = ' '.join(words)
    return sentence



def compare_strings(string1, string2):
    matcher = difflib.SequenceMatcher(None, string1, string2)
    return matcher.ratio() * 100

def neuroKGB(question):
    get_tokens()
    get_data()
    question = question.lower()
    question = sentence_to_tokens(question, words, tokens)
    maxod = 0
    imaxod = -1

    for i in Q:
        if compare_strings(question, i) > maxod:
            maxod = compare_strings(question, i)
            imaxod = Q.index(i)

    if imaxod == -1:
        return "Я не знаю что на это ответить."
    else:
        HQues.append(question)
        HAns.append(A[imaxod])
        if maxod < 60:
            return "⚠ " + tokens_to_sentence(A[imaxod], words, tokens)
        else:
            return tokens_to_sentence(A[imaxod], words, tokens)

def training(text):
    get_tokens()
    get_data()
    try:
        question, answer = text.split(":")
    except:
        return "Вы неправильно написали текст для обучения."
    if question == '':
        return 'Вы не написали вопрос.'
    elif answer == '':
        return "Вы не написали ответ."
    else:
        question_in_tokens_string = ' '.join(sentence_to_tokens(question, words, tokens))
        answer_in_tokens_string = ' '.join(sentence_to_tokens(answer, words, tokens))
        new_data = question_in_tokens_string+':'+answer_in_tokens_string
        with open('kgbBot/static_data/data.txt', 'a') as file:
            file.write(f'{new_data}\n')
        return 'Успешно!'

#while True:
#    try:
#        question = input("Введите вопрос >>>")
#        answer = BlockGPT3(question)
#        print(f"BlockGPT3: {answer}")
#    except KeyboardInterrupt:
#        print("\nДо свидания!")
#        exit()
