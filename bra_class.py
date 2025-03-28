#i have used the supplied lab1 solution code we were given and worked towards during the labs, and expanded on it, every change/addition I have made I commented and explained
#i removed the comments that were present in the file before for readability; easier to spot what changes I have made 

# IMPORTS
import pandas as pd
import numpy as np
import re
import math
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, roc_curve, auc)
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier#imports deicsiontree classifier
from sklearn.ensemble import RandomForestClassifier#imports randomforest classifier
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
import os
import subprocess
nltk.download('stopwords')
#
import time #will use it to evaluate the execution time of each model which is another metric I'm using to check efficiency 
#

# DEFINE TEXT PREPROCESSING METHODS
def remove_html(text):
    html = re.compile(r'<.*?>')
    return html.sub(r'', text)
def remove_emoji(text):
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"  # enclosed characters
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

final_stop_words_list = stopwords.words('english')

def remove_stopwords(text):
    return " ".join([word for word in str(text).split() if word not in final_stop_words_list])

def clean_str(string):
    string = re.sub(r"[^A-Za-z0-9(),.!?\'\`]", " ", string)
    string = re.sub(r"\'s", " \'s", string)
    string = re.sub(r"\'ve", " \'ve", string)
    string = re.sub(r"\)", " ) ", string)
    string = re.sub(r"\?", " ? ", string)
    string = re.sub(r"\s{2,}", " ", string)
    string = re.sub(r"\\", "", string)
    string = re.sub(r"\'", "", string)
    string = re.sub(r"\"", "", string)
    return string.strip().lower()

#choose the dataset (options: 'pytorch', 'tensorflow', 'keras', 'incubator-mxnet', 'caffe')
#
# choose dataset here
#
#
project = 'tensorflow'
path = f'datasets/{project}.csv'

pd_all = pd.read_csv(path)
pd_all = pd_all.sample(frac=1, random_state=999)  # Shuffle
pd_all['Title+Body'] = pd_all.apply(
    lambda row: row['Title'] + '. ' + row['Body'] if pd.notna(row['Body']) else row['Title'],
    axis=1
)
pd_tplusb = pd_all.rename(columns={
    "Unnamed: 0": "id",
    "class": "sentiment",
    "Title+Body": "text"
})
pd_tplusb.to_csv('Title+Body.csv', index=False, columns=["id", "Number", "sentiment", "text"])


#CONFIGURING PARAMETERS
datafile = 'Title+Body.csv'
out_csv_name = f'../{project}_NB.csv'
data = pd.read_csv(datafile).fillna('')
text_col = 'text'
original_data = data.copy()
data[text_col] = data[text_col].apply(remove_html)
data[text_col] = data[text_col].apply(remove_emoji)
data[text_col] = data[text_col].apply(remove_stopwords)
data[text_col] = data[text_col].apply(clean_str)

#
def run_experiment(tfidf, classifier, label, data, repeats, project='project', params=None):
    text_col = 'text'
    accuracies = []
    precisions = []
    recalls = []
    f1_scores = []
    auc_values = []
    processing_times = []#this parameter will be the time taken, itll be used for evaluation
    all_runs_log = []#List to hold all raw results per run


    for repeated_time in range(repeats):
        t0 = time.time()#starts calculating the time which will be used for evaluationn

        indices = np.arange(data.shape[0])
        train_index, test_index = train_test_split(
            indices, test_size=0.2, random_state=repeated_time
        )

        train_text = data[text_col].iloc[train_index]
        test_text = data[text_col].iloc[test_index]
        y_train = data['sentiment'].iloc[train_index]
        y_test = data['sentiment'].iloc[test_index]

        X_train = tfidf.fit_transform(train_text).toarray()
        X_test = tfidf.transform(test_text).toarray()

        model = classifier

        if params:
            grid = GridSearchCV(model, params, cv=5, scoring='roc_auc')
            grid.fit(X_train, y_train)
            model = grid.best_estimator_

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)



        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average='macro', zero_division=0)#adding zero division to remove interruption for decision tree runs
        rec = recall_score(y_test, y_pred, average='macro')
        f1 = f1_score(y_test, y_pred, average='macro')
 
        try:
            fpr, tpr, _ = roc_curve(y_test, y_pred, pos_label=1)
            auc_val = auc(fpr, tpr)
        except:
            auc_val = 0
        

        t1 = time.time()#finish time
        elapsed = t1 - t0
        

        accuracies.append(acc)
        precisions.append(prec)
        recalls.append(rec)
        f1_scores.append(f1)
        auc_values.append(auc_val)
        processing_times.append(elapsed)#minus start time from finish time to  get the processing times

        #save each run’s raw results
        all_runs_log.append({
            'Repeat': repeated_time + 1,
            'Accuracy': acc,
            'Precision': prec,
            'Recall': rec,
            'F1': f1,
            'AUC': auc_val,
            'Time(s)': elapsed
        })

    #aggregate results
    final_accuracy = np.mean(accuracies)
    final_precision = np.mean(precisions)
    final_recall = np.mean(recalls)
    final_f1 = np.mean(f1_scores)
    final_auc = np.mean(auc_values)
    final_time = np.mean(processing_times)#gets the mean of the processing times for evaluatiion

    print(f"\n=== Results for {label} ===")
    print(f"Accuracy:  {final_accuracy:.4f}")
    print(f"Precision: {final_precision:.4f}")
    print(f"Recall:    {final_recall:.4f}")
    print(f"F1 Score:  {final_f1:.4f}")
    print(f"AUC:       {final_auc:.4f}")
    print(f"Time:      {final_time:.4f} s")#outputs final time 
            
    #saving mean results
    mean_results_dir = os.path.join("results", "mean")
    os.makedirs(mean_results_dir, exist_ok=True)
    mean_results_path = os.path.join(mean_results_dir, f"{project}_{label}.csv")

    df_log = pd.DataFrame({
        'Experiment': [label],
        'repeated_times': [repeats],
        'Accuracy': [final_accuracy],
        'Precision': [final_precision],
        'Recall': [final_recall],
        'F1': [final_f1],
        'AUC': [final_auc],
        'Avg_Time(s)': [final_time],
        'CV_list(AUC)': [str(auc_values)]
    })
    df_log.to_csv(mean_results_path, index=False)

    #saving raw results
    raw_results_dir = os.path.join("results", "raw", project)
    os.makedirs(raw_results_dir, exist_ok=True)

    raw_results_path = os.path.join(raw_results_dir, f"{label}_raw.csv")

    pd.DataFrame({
        'Run': list(range(repeats)),
        'Accuracy': accuracies,
        'Precision': precisions,
        'Recall': recalls,
        'F1': f1_scores,
        'AUC': auc_values,
        'Processing Time (s)': processing_times
    }).to_csv(raw_results_path, index=False)

    print(f"Mean results saved to: {mean_results_path}")
    print(f"Raw results saved to: {raw_results_path}")


nb_params = {
    'var_smoothing': np.logspace(-12, 0, 13)
}
#THIS IS MY PARAMETERS THAT I PASS FOR THE GRIDCV FUNCTION ALONG WITH THE CLASSIFIERS, ALL RUN x TIMES (Repeat variable), can be changed
#decision tree grid
dt_params = {
    'max_depth': [None, 10],#how deep each tree goes
    'min_samples_split': [2, 5],#min samples to split a node 
    'criterion': ['gini']#impurity measure for splitting
}

rf_params = {
    'n_estimators': [100], #number of trees in the forest
    'max_depth': [None, 10], #how deep each tree goes
    'criterion': ['gini']      
}

#models
original_tfidf = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=1000 
    )

improved_tfidf = TfidfVectorizer(
    ngram_range=(1, 2),
    max_features=1000,
    sublinear_tf=True,
    min_df=2, #ignores terms that appear in less than 2 documents, wouldn't be useful for learning patterns and reduces overfitting
    max_df=0.90 #ignores terms that appear in more than 90% of documentsn removing noise
)

enhanced_improved_tfidf = TfidfVectorizer(
    ngram_range=(1, 3),#instead of using up to two-word phrases it uses three, e.g. (fails on load), which improves contextual features
    max_features=1500,#uses more features which will make it more expressive although can make it slower
    sublinear_tf=True,
    min_df=2,
    max_df=0.9
)

naive_bayes = GaussianNB()

decision_tree = DecisionTreeClassifier(
    criterion='gini',    
    max_depth=None,        
    random_state=42 #for consistency
    
)

random_forest = RandomForestClassifier(
    n_estimators=100,     #number of trees built
    max_depth=None,
    random_state=42,      #for consistency  
    n_jobs=1             #uses one core to compare it with dt and nb
)


REPEAT = 25
#naive bayes runs
run_experiment(original_tfidf, naive_bayes, "NB_OriginalTFIDF", data, REPEAT, project=project, params=nb_params)
run_experiment(improved_tfidf, naive_bayes, "NB_ImprovedTFIDF", data, REPEAT, project=project, params=nb_params)
run_experiment(enhanced_improved_tfidf, naive_bayes, "NB_EnhancedTFIDF", data, REPEAT, project=project, params=nb_params)

#decision tree runs
run_experiment(original_tfidf, decision_tree, "DT_OriginalTFIDF", data, REPEAT, project=project,params=dt_params)
run_experiment(improved_tfidf, decision_tree, "DT_ImprovedTFIDF", data, REPEAT, project=project,params=dt_params)
run_experiment(enhanced_improved_tfidf, decision_tree, "DT_EnhancedTFIDF", data, REPEAT, project=project,params=dt_params)

#random forest runs
run_experiment(original_tfidf, random_forest, "RF_OriginalTFIDF", data, REPEAT, project=project,params=rf_params)
run_experiment(improved_tfidf, random_forest, "RF_ImprovedTFIDF", data, REPEAT, project=project,params=rf_params)
run_experiment(enhanced_improved_tfidf, random_forest, "RF_EnhancedTFIDF", data, REPEAT, project=project,params=rf_params)
