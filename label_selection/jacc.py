"""
use jaccard distance to make new devset 
for below 3.0 score, high distance
above 3.0, low distance pairs are prioritized 
prevent model from predicting based on wordoverlap 

use Mecab for morpheme level tokenizing 

!pip install konlpy
!sudo apt-get install g++ openjdk-8-jdk 
!sudo apt-get install curl
!bash <(curl -s https://raw.githubusercontent.com/konlpy/konlpy/master/scripts/mecab.sh)
"""

import pandas as pd
from konlpy import *


# tokenize by morpheme-level 
def jaccard_distance(sentence_pair):
    mecab = Mecab()
    tokens1 = set(mecab.morphs(sentence_pair[0]))
    tokens2 = set(mecab.morphs(sentence_pair[1]))
    
    # Calculate the Jaccard distance between the two sets of morphemes
    jaccard_distance = len(tokens1.intersection(tokens2)) / len(tokens1.union(tokens2))

    return jaccard_distance
  
#리스트를 받으면 크기순(오름,내림) index 반환 
def top_n_idx(lst, n, reverse=True):

    indexed_lst = list(enumerate(lst))

    def get_key(pair):
        return pair[1] # 원소기준으로 정렬하기 위한 함수 
    
    
    sorted_idx = sorted(indexed_lst, key=get_key, reverse=reverse)
 
    
    top_n_idx = [idx for idx, val in sorted_idx[:n]] # top n index 추출
    return top_n_idx

    
# dataframe과 label을 입력하면 top_n을 출력  

# reverse = 'True' : top_n jacc_dist 
# reverse = 'False' : below_n jacc_dist

def rank_jacc(data_path, label:float, top_n:int, reverse = True):
    df = pd.read_csv(data_path)
    filtered_df = df[df['labels.label'] == label]
    pairs = list(zip(filtered_df['sentence1'],filtered_df['sentence2']))

    # jaccard distance 모든 각 문장 페어에 대해서 구하기
    overlap_score = []
    for sent_pair in pairs:
        overlap_score.append(jaccard_distance(sent_pair))
        

    # True = distance 높은 순으로 반환 / False = 낮은순 
    idx = top_n_idx(overlap_score, top_n, reverse=reverse)
    
    top_n_idx_of_df = filtered_df.iloc[idx].index.tolist() # 원본데이터의 idx를 반환 
    

    return df.iloc[top_n_idx_of_df]

