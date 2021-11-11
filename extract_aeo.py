import PyPDF2 #pip install PyPDF2
import os 
import pandas as pd
import spacy

# Discussion Partner: 
# Bowen Li and Ryan (Ziyang Wang)

# url = 'https://www.eia.gov/outlooks/aeo/pdf/aeo2019.pdf'
# url = 'https://www.eia.gov/outlooks/aeo/pdf/aeo2018.pdf'

# Sources
# Prof Levy notes and codes example
# https://www.dataquest.io/blog/tutorial-text-classification-in-python-using-spacy/
# https://www.kaggle.com/satishgunjal/tutorial-text-classification-using-spacy
# https://www.analyticsvidhya.com/blog/2017/04/natural-language-processing-made-easy-using-spacy-%E2%80%8Bin-python/
# https://course.spacy.io/en/chapter1
# https://applied-language-technology.readthedocs.io/en/latest/notebooks/part_iii/02_pattern_matching.html
# https://stackoverflow.com/questions/4843158/how-to-check-if-a-string-is-a-substring-of-items-in-a-list-of-strings
# https://spacy.io/api/doc
# https://realpython.com/natural-language-processing-spacy-python/
# https://www.delftstack.com/howto/python/python-max-value-in-list/
# https://stackoverflow.com/questions/268272/getting-key-with-maximum-value-in-dictionary
# https://stackoverflow.com/questions/55616470/adding-elements-to-an-empty-dataframe-in-pandas

# Logic of the Code
# First I read the pdf document and parse it as text file.
# In the count function I first pass the text to the nlp feature from spacy. 
# Create sentence list and then find sentences that only related to the
# energy type that we wanted to find and variable item yang we look for 
# (e.g price). I did search only one energy and one variable each time to 
# minimize error in searching the parent and child. After that assign the 
# variable that we seek as token and search the parent and child of that token
# if the parent and child contains up/down/unchaged/unavailable then add +1
# to counter. Find the maximum counter and assign value to the table. 
# Downside of this method is when sentence is too complicated, it is not going 
# to give us perfect answer but it is good enough. Ancestor and Child method
# is quiet robust and minimize us to use more complicated negation. 
# Matching function in Spacy but it is not robust enough for all sentences.


path = r'C:\Users\engel\Documents\GitHub\homework-2-natasiaengeline-1'
aeo2018 = 'aeo2018.pdf' 
aeo2019 = 'aeo2019.pdf' 

nlp = spacy.load("en_core_web_sm")

# parse pdf into text
def pdf_to_text(fname):
    pdf = PyPDF2.PdfFileReader(os.path.join(path, fname))

    text = []
    for pnum in range(4, 17):
        page = pdf.getPage(pnum)
        text.append(page.extractText())

    full_text = '\n'.join(text)
    full_text = full_text.lower().split()
    full_text = ' '.join(full_text)
    full_text = full_text.replace('ł', '').replace('š','')

    return full_text

aeo2018_text = pdf_to_text(aeo2018)
aeo2019_text = pdf_to_text(aeo2019)

# create counter 
def counter(text, energy_type, var_interest):
    doc = nlp(text)
    
    # create list of sentences
    sents_list = []
    for sent in doc.sents:
        sents_list.append(sent.text)

    # filter sentences to match only the words that we are looking for
    find_match =[*energy_type, *var_interest]
    sent_match = ([sent for sent in sents_list if 
                   all(word in sent for word in find_match)])
    
    # initial counter
    up_counter = 0
    down_counter = 0
    flat_counter = 0
    uncertain_counter = 0
    
    # find token index    
    if sent_match:
        for index, sent in enumerate(sent_match):
            doc = nlp(sent_match[index])
            index_num = ([token.i for token in doc if any 
                          (word in token.text for word in var_interest)])
        
        # counting based on the parent and child
        count = []
        for token_index in index_num:
            token = doc[token_index]
            variable_ancestors = list(token.ancestors)
            variable_children = list(token.children)
        
        up = ['raise', 'increase', 'up', 'growth', 'grow', 'higher']
        down = ['lower', 'decrease', 'down', 'decline']
        unchanged = ['unchanged', 'same', 'flat']
        uncertain = ['uncertainity']
        
        # count for ancestor        
        for ancestor in variable_ancestors:
            if ancestor.text in up:
                up_counter += 1
            elif ancestor.text in down:
                    down_counter += 1
            elif ancestor.text in unchanged:
                flat_counter += 1
            elif ancestor.text in uncertain:
                uncertain_counter += 1
        
        # count for children
        for children in variable_children:
            if children.text in up:
                up_counter += 1
            elif children.text in down:
                    down_counter += 1
            elif children.text in unchanged:
                flat_counter += 1
            elif children.text in uncertain:
                uncertain_counter += 1        
        
        # total counter for ancestor and child
        count = [up_counter, down_counter, flat_counter, uncertain_counter]
        
        # if counter is empty return no data available
        if all(value == 0 for value in count):
            count = 'No Data Available'
        else:
            identifier = {0:'Increase', 1:'Decrease', 2:'Unchanged', 
                          3:'Uncertain'}
            max_index = count.index(max(count))
            count = [identifier[max_index]]
            count = ''.join(count)
    
        return count 
    
    # if no sentence match, return no data is available 
    if not sent_match:
        count = 'No Data Available'
        
        return count

# function create the data frame
def aeo_table(text, energy_type): 
    # create data frame 
    col_names = ['energy type', 'price', 'emission', 'production', 
                 'export', 'import'] 

    df= pd.DataFrame([],columns = col_names)
    
    for energy in energy_type:
        price = counter(text, [energy], ['price'])
        emission = counter(text, [energy], ['emission'])  
        production = counter(text, [energy], ['production']) 
        energy_export = counter(text, [energy], ['export']) 
        energy_import = counter(text, [energy], ['import']) 
        
        df_tmp = pd.DataFrame([(energy, price, emission, production, 
                                energy_export, energy_import)], 
                              columns = col_names)
        
        df = df.append(df_tmp).reset_index(drop=True)
     
    return df

# define the energies and variable information
energies = ['coal', 'nuclear', 'wind', 'solar', 'oil']

aeo_table_2018 = aeo_table(aeo2018_text, energies)
aeo_table_2019 = aeo_table(aeo2019_text, energies)

# write to CSV for AEO 2018
(aeo_table_2018.
 to_csv(os.path.join(path,
                     r'AEO Table 2018.csv'), encoding='utf-8', index=False))

# write to CSV for AEO 2019
(aeo_table_2019.
 to_csv(os.path.join(path,
                     r'AEO Table 2019.csv'), encoding='utf-8', index=False))

