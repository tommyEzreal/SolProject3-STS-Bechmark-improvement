import sys
sys.path.append('/content/SolProject3-STS-Bechmark-improvement')

import pandas as pd
from torch.utils.data import DataLoader
from sentence_transformers import InputExample
from datetime import datetime 
import logging
from importlib import reload
from sentence_transformers import LoggingHandler
from tqdm.auto import tqdm 
from cross_encoder.CrossEncoder import CrossEncoder
from model_evaluation.model_evaluator import ModelEvaluator

import math 


reload(logging)
logging.basicConfig(
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG,
    handlers=[LoggingHandler()],
)


def extract_val_from_train(train,dev):
    
    # select val by label dist 
    val_ratio = (dev.groupby('labels.label').size() / dev.groupby('labels.label').size().sum()).to_frame('ratio')
    val_ratio['number'] = round(val_ratio['ratio'] * (len(train) *0.05)).astype(int) # train데이터의 5%를 val로 사용 
    
    val = pd.DataFrame()
    label = list(set(train['labels.label'].values))
    

    for i in label:
        try: # if sample size is bigger than 'number', skip sampling 
            sample = train.loc[train['labels.label']==i].sample(n=val_ratio['number'][i])
        except:
            continue 
        val = pd.concat([val,sample])
    
    
    train = train.drop(val.index)
    return train, val

# train, val 한번에 input_examples로 변환 
def create_input_examples(train,val):

    dfs = [train, val]
    input_examples = [[] for _ in range(2)]

    for i, df in enumerate(dfs):
        for _, row in tqdm(df.iterrows()):
            sentence1, sentence2, score = row[0], row[1], row[2]/5.0
            input_examples[i].append(InputExample(texts=[sentence1, sentence2], label=score))

    return input_examples[0], input_examples[1] # train, val


def train_ce(model_save_path,
             train, # DataFrame
             dev, # DataFrame
             num_epochs,
             train_batch_size,
             pretrained_model_name='klue/roberta-base',
             encoding = 'cross_encoding',
             verbose = True):
    # load pretrained model 
    cross_encoder = CrossEncoder(pretrained_model_name, num_labels=1)

    logging.info('extract_val_from_train')
    _train, val = extract_val_from_train(train, dev) # extract val from train 

    logging.info('create_input_examples')
    sts_train_examples, sts_val_examples = create_input_examples(_train,val)

    logging.info('assign_DataLoader_and_val_evaluator')
    train_dataloader = DataLoader(sts_train_examples,
                                    shuffle=True,
                                    batch_size = train_batch_size)
    val_evaluator = ModelEvaluator.from_input_examples(sts_val_examples, encoding=encoding, verbose = verbose)
    
    warmup_steps = math.ceil(len(train_dataloader) * num_epochs / train_batch_size*0.1) # 10%of train

    logging.info(f'start train model..')
    cross_encoder.fit(
        train_dataloader = train_dataloader,
        evaluator=val_evaluator,
        epochs=num_epochs,
        evaluation_steps=int(len(train_dataloader)*0.1),
        optimizer_params = {'lr':5e-5},
        warmup_steps=warmup_steps,
        output_path=model_save_path,
    )

    return cross_encoder

# if __name__ == '__main__':
#     model_save_path = '/content/sample_data/cross_encoder'
#     train = pd.read_csv('https://raw.githubusercontent.com/tommyEzreal/SolProject3-STS-Bechmark-improvement/main/data/KLUE_STS_train%20(2).csv')
#     train = train[['sentence1','sentence2','labels.label']]
#     dev = pd.read_csv('https://raw.githubusercontent.com/tommyEzreal/SolProject3-STS-Bechmark-improvement/main/data/KLUE_STS_val%20(2).csv')
#     dev = dev[['sentence1','sentence2','labels.label']]
#     num_epochs = 1
#     train_batch_size = 32
    
#     trained_model = train_ce(model_save_path, train, dev, num_epochs, train_batch_size)
    
    
    
    
    
