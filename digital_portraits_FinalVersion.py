# digital_portraits
# ryq
# 针对不同的数据集，注意分类数量、训练函数、训练轮次的超参数设定

# 导入
import shutil
import pandas as pd
import sys
sys.path.append("..")
from d2lzh_pytorch import *
import torch.nn.functional as F

from sklearn.utils import shuffle
import random

from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split as tts
from torch import nn
from PIL import Image
from PIL import ImageDraw
from torch.utils import data
from torch.utils.data import DataLoader
from torchvision import transforms
from xgboost import XGBClassifier as xgbc

import category_encoders as ce
import matplotlib.pyplot as plt

from sklearn.metrics import roc_auc_score
from sklearn.metrics import precision_recall_fscore_support
from sklearn.metrics import f1_score, precision_recall_curve, PrecisionRecallDisplay

from sklearn.metrics import precision_recall_curve, auc, f1_score
import matplotlib.pyplot as plt
import numpy as np
from sklearn.preprocessing import label_binarize

from sklearn.manifold import TSNE
# from torch.utils.data import DataLoader
# from torchvision import transforms
import os
import torch
import time
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 数据集
global data_name
data_name = "helo"
global data_root
# data_root = r'D:\ryq\dataset'
data_root = r'D:\ryqcode\mrlf\dataset'
batch_size = 8
num_epochs = 30
ir = 0.005


# 对数据进行准备和处理的类
class DataPrepare:

    # self.df 数据集的df，当前对象的一个DataFrame类型（二维表格或异构数据）数据
    # self.data_root 数据集根目录
    # self.data_name 数据集名
    # self.x_cols 特征列
    # self.y_col  标签列
    # self.df 按列索引
    # self.importance_list [特征重要性]
    # self.import_combine [特征名称,重要性]的二维列表
    # self.import_column_set 绘图列索引
    # self.import_dict {'特征名称'：'重要性'}的字典
    def __init__(self, data_root, data_name):
        self.data_root = data_root
        self.data_name = data_name
        self.continuous_features = []
        self.discrete_features = []
        self.all_features = []
        self.x_cols = []
        self.y_col = []
        self.df = []
        self.importance_list = []
        self.import_combine = []
        # self.import_column_set = {}
        self.import_dict = {}

    # 定义列名
    def column_names(self):
        if self.data_name == 'adult':
            self.continuous_features = ['age', 'fnlwgt', 'education-num', 'capital-gain', 'capital-loss', 'hours-per-week']
            self.discrete_features = ['workclass', 'education', 'marital-status', 'occupation', 'relationship', 'race', 'sex',
                                      'native-country']
            self.all_features = ['age', 'workclass', 'fnlwgt', 'education', 'education-num', 'marital-status', 'occupation',
                                 'relationship', 'race', 'sex', 'capital-gain', 'capital-loss', 'hours-per-week',
                                 'native-country', 'salary']
            self.x_cols = ['age', 'workclass', 'fnlwgt', 'education', 'education-num', 'marital-status', 'occupation',
                           'relationship', 'race', 'sex', 'capital-gain', 'capital-loss', 'hours-per-week',
                           'native-country']
            self.y_col = 'salary'
        elif self.data_name == 'wine':
            self.continuous_features = ['Alcohol', 'Malic acid', 'Ash', 'Alcalinity of ash',
                                        'Magnesium', 'Total phenols', 'Flavanoid',
                                        'Nonflavanoid phenols', 'Proanthocyanins', 'Color intensity', 'Hue',
                                        'OD280/OD315 of diluted wines', 'Proline']
            self.discrete_features = []
            # wine标签列在第一列
            self.all_features = ['category', 'Alcohol', 'Malic acid', 'Ash', 'Alcalinity of ash',
                                 'Magnesium', 'Total phenols', 'Flavanoid',
                                 'Nonflavanoid phenols', 'Proanthocyanins', 'Color intensity', 'Hue',
                                 'OD280/OD315 of diluted wines', 'Proline']
            self.x_cols = ['Alcohol', 'Malic acid', 'Ash', 'Alcalinity of ash',
                           'Magnesium', 'Total phenols', 'Flavanoid',
                           'Nonflavanoid phenols', 'Proanthocyanins', 'Color intensity', 'Hue',
                           'OD280/OD315 of diluted wines', 'Proline']
            self.y_col = 'category'
        elif self.data_name == 'lris':
            self.continuous_features = ['col1', 'col2', 'col3', 'col4']
            self.discrete_features = []
            self.all_features = ['col1', 'col2', 'col3', 'col4', 'category']
            self.x_cols = ['col1', 'col2', 'col3', 'col4']
            self.y_col = 'category'
        elif self.data_name == 'diamonds':
            self.continuous_features = ['carat', 'depth', 'table', 'price', 'x', 'y', 'z']
            self.discrete_features = ['color', 'clarity']
            self.all_features = ['carat', 'cut', 'color', 'clarity', 'depth', 'table', 'price', 'x', 'y', 'z']
            self.x_cols = ['carat', 'color', 'clarity', 'depth', 'table', 'price', 'x', 'y', 'z']
            self.y_col = 'cut'
        elif self.data_name == 'breast_cancer':
            self.all_features = ['Sample code number', 'Clump Thickness', 'Uniformity of Cell Size',
                                 'Uniformity of Cell Shape', 'Marginal Adhesion', 'Single Epithelial Cell Size',
                                 'Bare Nuclei', 'Bland Chromatin', 'Normal Nucleoli',
                                 'Mitoses', 'Class']
            self.continuous_features = ['Clump Thickness', 'Uniformity of Cell Size',
                                        'Uniformity of Cell Shape', 'Marginal Adhesion', 'Single Epithelial Cell Size',
                                        'Bare Nuclei', 'Bland Chromatin', 'Normal Nucleoli',
                                        'Mitoses']
            self.discrete_features = []
            self.x_cols = ['Clump Thickness', 'Uniformity of Cell Size',
                           'Uniformity of Cell Shape', 'Marginal Adhesion', 'Single Epithelial Cell Size',
                           'Bare Nuclei', 'Bland Chromatin', 'Normal Nucleoli',
                           'Mitoses']
            self.y_col = 'Class'
        elif self.data_name == 'helo':
            self.all_features = ['RiskPerformance', 'ExternalRiskEstimate', 'MSinceOldestTradeOpen',
                                 'MSinceMostRecentTradeOpen', 'AverageMInFile', 'NumSatisfactoryTrades',
                                 'NumTrades60Ever2DerogPubRec', 'NumTrades90Ever2DerogPubRec', 'PercentTradesNeverDelq',
                                 'MSinceMostRecentDelq', 'MaxDelq2PublicRecLast12M','MaxDelqEver', 'NumTotalTrades',
                                 'NumTradesOpeninLast12M', 'PercentInstallTrades', 'MSinceMostRecentInqexcl7days',
                                 'NumInqLast6M', 'NumInqLast6Mexcl7days', 'NetFractionRevolvingBurden',
                                 'NetFractionInstallBurden', 'NumRevolvingTradesWBalance', 'NumInstallTradesWBalance',
                                 'NumBank2NatlTradesWHighUtilization', 'PercentTradesWBalance'
                                 ]
            self.continuous_features = ['ExternalRiskEstimate', 'MSinceOldestTradeOpen',
                                        'MSinceMostRecentTradeOpen', 'AverageMInFile', 'NumSatisfactoryTrades',
                                        'NumTrades60Ever2DerogPubRec', 'NumTrades90Ever2DerogPubRec', 'PercentTradesNeverDelq',
                                        'MSinceMostRecentDelq', 'MaxDelq2PublicRecLast12M','MaxDelqEver', 'NumTotalTrades',
                                        'NumTradesOpeninLast12M', 'PercentInstallTrades', 'MSinceMostRecentInqexcl7days',
                                        'NumInqLast6M', 'NumInqLast6Mexcl7days', 'NetFractionRevolvingBurden',
                                        'NetFractionInstallBurden', 'NumRevolvingTradesWBalance', 'NumInstallTradesWBalance',
                                        'NumBank2NatlTradesWHighUtilization', 'PercentTradesWBalance']
            self.discrete_features = []
            self.x_cols = ['ExternalRiskEstimate', 'MSinceOldestTradeOpen',
                           'MSinceMostRecentTradeOpen', 'AverageMInFile', 'NumSatisfactoryTrades',
                           'NumTrades60Ever2DerogPubRec', 'NumTrades90Ever2DerogPubRec', 'PercentTradesNeverDelq',
                           'MSinceMostRecentDelq', 'MaxDelq2PublicRecLast12M','MaxDelqEver', 'NumTotalTrades',
                           'NumTradesOpeninLast12M', 'PercentInstallTrades', 'MSinceMostRecentInqexcl7days',
                           'NumInqLast6M', 'NumInqLast6Mexcl7days', 'NetFractionRevolvingBurden',
                           'NetFractionInstallBurden', 'NumRevolvingTradesWBalance', 'NumInstallTradesWBalance',
                           'NumBank2NatlTradesWHighUtilization', 'PercentTradesWBalance']
            self.y_col = 'RiskPerformance'
        elif self.data_name == 'churn':
            self.continuous_features = ['CreditScore', 'Age', 'Tenure',
                                        'Balance', 'NumOfProducts',
                                        'HasCrCard', 'IsActiveMember', 'EstimatedSalary']
            self.discrete_features = ['Surname', 'Geography', 'Gender']
            self.all_features = ['RowNumber', 'CustomerId', 'Surname', 'CreditScore', 'Geography',
                                 'Gender', 'Age', 'Tenure', 'Balance', 'NumOfProducts',
                                 'HasCrCard', 'IsActiveMember', 'EstimatedSalary', 'Exited']
            self.x_cols = ['Surname', 'CreditScore', 'Geography',
                           'Gender', 'Age', 'Tenure', 'Balance', 'NumOfProducts',
                           'HasCrCard', 'IsActiveMember', 'EstimatedSalary']
            self.y_col = 'Exited'
        elif self.data_name == 'churn':
            self.continuous_features = ['CreditScore', 'Age', 'Tenure',
                                        'Balance', 'NumOfProducts',
                                        'HasCrCard', 'IsActiveMember', 'EstimatedSalary']
            self.discrete_features = ['Surname', 'Geography', 'Gender']
            self.all_features = ['RowNumber', 'CustomerId', 'Surname', 'CreditScore', 'Geography',
                                 'Gender', 'Age', 'Tenure', 'Balance', 'NumOfProducts',
                                 'HasCrCard', 'IsActiveMember', 'EstimatedSalary', 'Exited']
            self.x_cols = ['Surname', 'CreditScore', 'Geography',
                           'Gender', 'Age', 'Tenure', 'Balance', 'NumOfProducts',
                           'HasCrCard', 'IsActiveMember', 'EstimatedSalary']
            self.y_col = 'Exited'
        elif self.data_name == 'blastchar':
            self.continuous_features = ['SeniorCitizen', 'tenure', 'MonthlyCharges']
            self.discrete_features = ['customerID', 'gender', 'Partner', 'Dependents',
                                      'PhoneService', 'MultipleLines', 'InternetService', 'OnlineSecurity',
                                      'OnlineBackup', 'DeviceProtection', 'TechSupport', 'StreamingTV',
                                      'StreamingMovies',
                                      'Contract', 'PaperlessBilling', 'PaymentMethod', 'TotalCharges']
            self.all_features = ['customerID', 'gender', 'SeniorCitizen', 'Partner', 'Dependents',
                                 'tenure', 'PhoneService', 'MultipleLines', 'InternetService', 'OnlineSecurity',
                                 'OnlineBackup', 'DeviceProtection', 'TechSupport', 'StreamingTV', 'StreamingMovies',
                                 'Contract', 'PaperlessBilling', 'PaymentMethod', 'MonthlyCharges', 'TotalCharges',
                                 'Churn']
            self.x_cols = ['customerID', 'gender', 'SeniorCitizen', 'Partner', 'Dependents',
                           'tenure', 'PhoneService', 'MultipleLines', 'InternetService', 'OnlineSecurity',
                           'OnlineBackup', 'DeviceProtection', 'TechSupport', 'StreamingTV', 'StreamingMovies',
                           'Contract', 'PaperlessBilling', 'PaymentMethod', 'MonthlyCharges', 'TotalCharges']
            self.y_col = 'Churn'
        elif self.data_name == 'higgs_smal':
            self.continuous_features = ['DER_mass_MMC', 'DER_mass_transverse_met_lep', 'DER_mass_vis', 'DER_pt_h',
                                        'DER_deltaeta_jet_jet', 'DER_mass_jet_jet', 'DER_prodeta_jet_jet', 'DER_deltar_tau_lep', 'DER_pt_tot',
                                        'DER_sum_pt', 'DER_pt_ratio_lep_tau', 'DER_met_phi_centrality', 'DER_lep_eta_centrality', 'PRI_tau_pt',
                                        'PRI_tau_eta', 'PRI_tau_phi', 'PRI_lep_pt', 'PRI_lep_eta', 'PRI_lep_phi',
                                        'PRI_met', 'PRI_met_phi', 'PRI_met_sumet',
                                        'PRI_jet_num', 'PRI_jet_leading_pt', 'PRI_jet_leading_eta', 'PRI_jet_leading_phi', 'PRI_jet_subleading_pt',
                                        'PRI_jet_subleading_eta', 'PRI_jet_subleading_phi', 'PRI_jet_all_pt', 'Weight']
            self.discrete_features = []
            self.all_features = ['EventId', 'DER_mass_MMC', 'DER_mass_transverse_met_lep', 'DER_mass_vis', 'DER_pt_h',
                                 'DER_deltaeta_jet_jet', 'DER_mass_jet_jet', 'DER_prodeta_jet_jet', 'DER_deltar_tau_lep', 'DER_pt_tot',
                                 'DER_sum_pt', 'DER_pt_ratio_lep_tau', 'DER_met_phi_centrality', 'DER_lep_eta_centrality', 'PRI_tau_pt',
                                 'PRI_tau_eta', 'PRI_tau_phi', 'PRI_lep_pt', 'PRI_lep_eta', 'PRI_lep_phi',
                                 'PRI_met', 'PRI_met_phi', 'PRI_met_sumet',
                                 'PRI_jet_num', 'PRI_jet_leading_pt', 'PRI_jet_leading_eta', 'PRI_jet_leading_phi', 'PRI_jet_subleading_pt',
                                 'PRI_jet_subleading_eta', 'PRI_jet_subleading_phi', 'PRI_jet_all_pt', 'Weight', 'Label']
            self.x_cols = ['DER_mass_MMC', 'DER_mass_transverse_met_lep', 'DER_mass_vis', 'DER_pt_h',
                           'DER_deltaeta_jet_jet', 'DER_mass_jet_jet', 'DER_prodeta_jet_jet', 'DER_deltar_tau_lep', 'DER_pt_tot',
                           'DER_sum_pt', 'DER_pt_ratio_lep_tau', 'DER_met_phi_centrality', 'DER_lep_eta_centrality', 'PRI_tau_pt',
                           'PRI_tau_eta', 'PRI_tau_phi', 'PRI_met', 'PRI_met_phi', 'PRI_met_sumet',
                           'PRI_jet_num', 'PRI_jet_leading_pt', 'PRI_jet_leading_eta', 'PRI_jet_leading_phi', 'PRI_jet_subleading_pt',
                           'PRI_jet_subleading_eta', 'PRI_jet_subleading_phi', 'PRI_jet_all_pt', 'Weight']
            self.y_col = 'Label'
        elif self.data_name == 'forest':
            self.continuous_features = ['f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10']
            self.discrete_features = ['f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17', 'f18', 'f19', 'f20',
                                       'f21', 'f22', 'f23', 'f24', 'f25', 'f26', 'f27', 'f28', 'f29', 'f30',
                                       'f31', 'f32', 'f33', 'f34', 'f35', 'f36', 'f37', 'f38', 'f39', 'f40',
                                       'f41', 'f42', 'f43', 'f44', 'f45', 'f46', 'f47', 'f48', 'f49', 'f50',
                                       'f51', 'f52', 'f53', 'f54']
            self.all_features = ['f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10',
                                   'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17', 'f18', 'f19', 'f20',
                                   'f21', 'f22', 'f23', 'f24', 'f25', 'f26', 'f27', 'f28', 'f29', 'f30',
                                   'f31', 'f32', 'f33', 'f34', 'f35', 'f36', 'f37', 'f38', 'f39', 'f40',
                                   'f41', 'f42', 'f43', 'f44', 'f45', 'f46', 'f47', 'f48', 'f49', 'f50',
                                   'f51', 'f52', 'f53', 'f54', 'type']
            self.x_cols = ['f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10',
                           'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17', 'f18', 'f19', 'f20',
                           'f21', 'f22', 'f23', 'f24', 'f25', 'f26', 'f27', 'f28', 'f29', 'f30',
                           'f31', 'f32', 'f33', 'f34', 'f35', 'f36', 'f37', 'f38', 'f39', 'f40',
                           'f41', 'f42', 'f43', 'f44', 'f45', 'f46', 'f47', 'f48', 'f49', 'f50',
                           'f51', 'f52', 'f53', 'f54'
                           ]
            self.y_col = 'type'


    # 加载数据
    def load_data(self):
        if self.data_name == 'adult':
            data_list = []
            with open(self.data_root + r'\adult.data') as f:
                # 读取1数据行
                line = f.readline()
                # 遍历1行所有列
                while line:
                    line = line.replace("\n", "")
                    line = line.replace(" ", "")
                    params = line.split(",")
                    data_list.append(params)
                    line = f.readline()
            data_list = data_list[:-2]
            # 注意这里是两个文件
            with open(self.data_root + r'\adult.test') as f:
                line = f.readline()
                while line:
                    line = line.replace("\n", "")
                    line = line.replace(" ", "")
                    line = line.replace(".", "")
                    params = line.split(",")
                    data_list.append(params)
                    line = f.readline()
            data_list = data_list[:-2]
            self.df = pd.DataFrame(data_list, columns=self.all_features)
            self.df = shuffle(self.df)
        elif self.data_name == 'wine':
            data_list = []
            with open(self.data_root + r'\wine.data') as f:
                line = f.readline()
                while line:
                    line = line.replace("\n", "")
                    line = line.replace(" ", "")
                    params = line.split(",")
                    data_list.append(params)
                    line = f.readline()
            self.df = pd.DataFrame(data_list, columns=self.all_features)
            self.df = shuffle(self.df)
        elif self.data_name == 'lris':
            data_list = []
            with open(self.data_root + r'\iris.data') as f:
                line = f.readline()
                while line:
                    line = line.replace("\n", "")
                    line = line.replace(" ", "")
                    params = line.split(",")
                    data_list.append(params)
                    line = f.readline()
            data_list = data_list[:-2]
            self.df = pd.DataFrame(data_list, columns=self.all_features)
            self.df = shuffle(self.df)
            # print(self.df)
        elif self.data_name == 'diamonds':
            data_list = []
            with open(self.data_root + r'\diamondsample.data') as f:
                # 读取1数据行
                line = f.readline()
                # 遍历1行所有列
                while line:
                    line = line.replace("\n", "")
                    line = line.replace(" ", "")
                    params = line.split(",")
                    data_list.append(params)
                    line = f.readline()
            data_list = data_list[:-2]
            self.df = pd.DataFrame(data_list, columns=self.all_features)
            self.df = shuffle(self.df)
        elif self.data_name == 'breast_cancer':
            data_list = []
            with open(self.data_root + r'\breast_cancer.data') as f:
                # 读取1数据行
                line = f.readline()
                # 遍历1行所有列
                while line:
                    line = line.replace("\n", "")
                    line = line.replace(" ", "")
                    line = line.replace('?', str(np.nan))
                    params = line.split(",")
                    data_list.append(params)
                    line = f.readline()
            data_list = data_list[:-1]
            self.df = pd.DataFrame(data_list, columns=self.all_features)
            self.df = shuffle(self.df)
            # 去除ID列
            self.df = self.df.drop(self.all_features[0], axis=1)
            # 去除缺失值行
            self.df = self.df.dropna()
        elif self.data_name == 'helo':
            data_list = []
            with open(self.data_root + r'\helosample.data') as f:
                # 读取1数据行
                line = f.readline()
                # 遍历1行所有列
                while line:
                    line = line.replace("\n", "")
                    line = line.replace(" ", "")
                    params = line.split(",")
                    data_list.append(params)
                    line = f.readline()
            data_list = data_list[:-2]
            self.df = pd.DataFrame(data_list, columns=self.all_features)
            self.df = shuffle(self.df)
        elif self.data_name == 'churn':
            data_list = []
            with open(self.data_root + r'\churn.data') as f:
                # 读取1数据行
                line = f.readline()
                # 遍历1行所有列
                while line:
                    line = line.replace("\n", "")
                    line = line.replace(" ", "")
                    params = line.split(",")
                    data_list.append(params)
                    line = f.readline()
            data_list = data_list[:-2]
            self.df = pd.DataFrame(data_list, columns=self.all_features)
            self.df = shuffle(self.df)
            # 去除ID列
            self.df = self.df.drop(self.all_features[:2], axis=1)
            # print(self.df)
        elif self.data_name == 'blastchar':
            data_list = []
            with open(self.data_root + r'\blastchar.data') as f:
                # 读取1数据行
                line = f.readline()
                # 遍历1行所有列
                while line:
                    line = line.replace("\n", "")
                    line = line.replace(" ", "")
                    params = line.split(",")
                    data_list.append(params)
                    line = f.readline()
            data_list = data_list[:-2]
            self.df = pd.DataFrame(data_list, columns=self.all_features)
            self.df = shuffle(self.df)
            # 去除缺失值行
            self.df = self.df.dropna()
        elif self.data_name == 'higgs_smal':
            data_list = []
            with open(self.data_root + r'\higgs.data') as f:
                # 读取1数据行
                line = f.readline()
                # 遍历1行所有列
                while line:
                    line = line.replace("\n", "")
                    line = line.replace(" ", "")
                    params = line.split(",")
                    data_list.append(params)
                    line = f.readline()
            data_list = data_list[:-2]
            self.df = pd.DataFrame(data_list, columns=self.all_features)
            self.df = shuffle(self.df)
            # 去除ID列
            self.df = self.df.drop(self.all_features[0], axis=1)
        elif self.data_name == 'forest':
            data_list = []
            with open(self.data_root + r'\forestsample.data') as f:
                # 读取1数据行
                line = f.readline()
                # 遍历1行所有列
                while line:
                    line = line.replace("\n", "")
                    line = line.replace(" ", "")
                    params = line.split(",")
                    data_list.append(params)
                    line = f.readline()
            data_list = data_list[:-1]
            self.df = pd.DataFrame(data_list, columns=self.all_features)
            self.df = shuffle(self.df)

    # 数据预处理
    def preprocessing(self):
        # 需要特征工程的数据集

        # 解决出现adult数据集出现的age = |1x3Crossvalidator 空白行的补丁
        if self.data_name == 'adult':
            value_to_remove = '|1x3Crossvalidator'
            self.df = self.df[self.df['age'] != value_to_remove]

        for col in self.continuous_features:
            self.df[col] = self.df[col].astype(float)
            # 防止出现负数
            self.df[col] = self.df[col].apply(lambda x: abs(x) if x < 0 else x)
        for col in self.discrete_features:
            self.df[col] = self.df[col].astype(str)
        # 离散特征连续化，如男-》0，女-》1
        # 按列转化
        # lelist = {}
        # for col in self.discrete_features:
        #     le = LabelEncoder()
        #     le.fit(np.hstack([self.df[col]]))
        #     self.df[col] = le.transform(self.df[col])
        #     del le
        # 标签列序数编码
        le = LabelEncoder()
        le.fit(np.hstack([self.df[self.y_col]]))
        self.df[self.y_col] = le.transform(self.df[self.y_col])
        # print(self.df[self.y_col])
        del le
        # 定义CatBoostEncoder，使用模型编码将类别特征转化为数值特征
        cbe_encoder = ce.cat_boost.CatBoostEncoder()
        cbe_encoder.fit(self.df[self.discrete_features], self.df[self.y_col])
        self.df[self.discrete_features] = cbe_encoder.transform(self.df[self.discrete_features])
        # 将所有特征值归一化
        scaler = MinMaxScaler()
        self.df[self.x_cols] = scaler.fit_transform(self.df[self.x_cols])
        # pd.set_option('display.max_rows', None)
        # pd.set_option('display.max_columns', None)
        # print(pd.DataFrame(self.df))
        # print(self.df)

    # xgboost训练得特征重要值
    def xgboost_train(self):
        train_dataa, test_dataa = tts(self.df, test_size=0.1, random_state=420)
        train_x = train_dataa[self.x_cols]
        train_y = train_dataa[self.y_col]
        # print(train_y)
        test_x = test_dataa[self.x_cols]
        test_y = test_dataa[self.y_col]
        # print(test_y)
        # 数值特征的用weight，类别特征的用cover
        xgb_classifier = xgbc(importance_type='weight', n_estimators=200).fit(train_x, train_y)
        self.importance_list = xgb_classifier.feature_importances_.tolist()
        score = xgb_classifier.score(test_x, test_y)
        print(score)
        # print(self.importance_list)
        # print(train_y)

    # 组合x_cols和importance值
    def combining(self):
        import_combine = []
        for i in range(len(self.importance_list)):
            import_combine.append([self.x_cols[i], self.importance_list[i]])
        # import_combine.sort(key=takeSecond)
        # 列名+重要性
        self.import_combine = import_combine
        # print(self.import_combine)
        # 每个值索引对应它的重要性
        for i in range(len(import_combine)):
            self.import_dict[import_combine[i][0]] = import_combine[i][1]

    # 绘矩形图
    def dp_rectangle(self):
        # 批量生成
        # 图集文件夹
        # print(self.df[self.y_col])
        if os.path.exists("atlas_rectangle"):
            shutil.rmtree("atlas_rectangle")
        os.mkdir("atlas_rectangle")
        # 每张图片索引
        photo_idx = 0
        # iterrows会导致数值类型转变为float,故标签0/1/2变为0.0/1.0/2.0
        for _, row in self.df.iterrows():
            # 生成纯黑画板
            # 每个特征，最宽100，最高100
            image = Image.new("1", (130 + self.df.shape[1] * 20, 140))
            image.paste(0, (0, 0, 130 + self.df.shape[1] * 20, 140))
            draw = ImageDraw.Draw(image)
            # 起始位置，左下角。每个矩形，从左上往右下画
            x_idx = 20
            y_idx = image.height - 20
            for idx, column in enumerate(self.x_cols):
                feature_importance = self.import_dict[column]
                value = row[column]
                # print(value)
                width = feature_importance * 100
                # print(width)
                height = value * 100
                # print(height)
                x_start = x_idx
                y_start = y_idx - height
                x_end = x_idx + width
                y_end = y_idx
                draw.rectangle((x_start, y_start, x_end, y_end), fill=255, outline=None)
                x_idx = x_end + 20
                y_idx = image.height - 20
            # image.show()
            # 不存在该类别图片路径则生成
            # 标签是图集的名字
            # print(row[self.y_col])
            if not os.path.exists("atlas_rectangle/" + str(int(row[self.y_col]))):
                os.mkdir("atlas_rectangle/" + str(int(row[self.y_col])))
            image.save("atlas_rectangle/" + str(int(row[self.y_col])) + "/" + str(photo_idx) + ".png")
            photo_idx += 1

    # 绘折线图
    def dp_line(self):
        if os.path.exists("atlas_line"):
            shutil.rmtree("atlas_line")
        os.mkdir("atlas_line")
        # 每张图片索引
        photo_idx = 0
        # iterrows会导致数值类型转变为float,故标签0/1/2变为0.0/1.0/2.0
        for _, row in self.df.iterrows():
            # 生成纯黑画板
            # 每个特征，最宽100，最高100
            # 矩形图宽度设定没问题，折线图的宽度，让他与矩形图一致同时又适合自己需要一定的手动调试
            image = Image.new("1", (130 + self.df.shape[1] * 20, 140))
            image.paste(0, (0, 0, 130 + self.df.shape[1] * 20, 140))
            draw = ImageDraw.Draw(image)
            # 折线从左往右画
            x_idx = 20
            # 按重要性进行特征排序
            combined = self.import_combine
            # print(combined)
            combined.sort(key=lambda x: x[1], reverse=True)  # 按照重要性进行排序
            sorted_features = [x[0] for x in combined]  # 提取排序后的特征名称
            # print(sorted_features)
            last_x, last_y = None, None  # 上一个点的坐标
            for idx, column in enumerate(sorted_features):
                value = row[column]
                # print(value)
                y_idx = 120 - value * 100
                # plt.plot(x_idx, y_idx, label=column)
                draw.point((x_idx, y_idx), fill=1)
                if last_x is not None and last_y is not None:
                    draw.line((last_x, last_y, x_idx, y_idx), fill=1)
                last_x, last_y = x_idx, y_idx
                x_idx += 30
            # image.show()
            # 不存在该类别图片路径则生成
            # 标签是图集的名字
            # print(row[self.y_col])
            if not os.path.exists("atlas_line/" + str(int(row[self.y_col]))):
                os.mkdir("atlas_line/" + str(int(row[self.y_col])))
            image.save("atlas_line/" + str(int(row[self.y_col])) + "/" + str(photo_idx) + ".png")
            photo_idx += 1


# 类后应该有两行空行
# 产生一个实例/对象
# 调用这个对象的所有功能方法（创建一个对象后，需要显式地调用对象的方法来执行特定的操作，或者也可以将调用写到init里）
prepare_handler = DataPrepare(data_root, data_name)
prepare_handler.column_names()
prepare_handler.load_data()
prepare_handler.preprocessing()
prepare_handler.xgboost_train()
prepare_handler.combining()
prepare_handler.dp_rectangle()
prepare_handler.dp_line()


# 搭建CNN第5代Resnet残差网络
class Residual(nn.Module):
    def __init__(self, in_channels, out_channels, use_1x1conv=False, stride=1):
        super(Residual, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, stride=stride)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1)
        if use_1x1conv:
            self.conv3 = nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride)
        else:
            self.conv3 = None
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.bn2 = nn.BatchNorm2d(out_channels)

    def forward(self, x):
        y = F.relu(self.bn1(self.conv1(x)))
        y = self.bn2(self.conv2(y))
        if self.conv3:
            x = self.conv3(x)
        return F.relu(y + x)


def resnet_block(in_channels, out_channels, num_residuals, first_block=False):
    if first_block:
        assert in_channels == out_channels
    blk = []
    for i in range(num_residuals):
        if i == 0 and not first_block:
            blk.append(Residual(in_channels, out_channels, use_1x1conv=True, stride=2))
        else:
            blk.append(Residual(out_channels, out_channels))
    return nn.Sequential(*blk)


class DualBranchResNet(nn.Module):
    def __init__(self, num_classes):
        super(DualBranchResNet, self).__init__()

        self.rectangle_branch = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        )

        self.line_branch = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=3, stride=2, padding=1),
        )

        # 对比旧版，减少了每个模组内残差块的数量
        self.resnet_blocks = nn.ModuleList([
            resnet_block(128, 128, 1, first_block=True),
            resnet_block(128, 256, 1),
            resnet_block(256, 256, 1),
            resnet_block(256, 512, 1)
        ])

        # 更加简洁规范
        self.global_avg_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(512, num_classes)

    def forward(self, rectangle, line):
        rectangle_features = self.rectangle_branch(rectangle)
        line_features = self.line_branch(line)
        line_features = line_features.mean(dim=(2, 3), keepdim=True).repeat(1, 1, rectangle_features.size(2),
                                                                            rectangle_features.size(3))
        features = torch.cat([rectangle_features, line_features], dim=1)
        for block in self.resnet_blocks:
            features = block(features)
        features = self.global_avg_pool(features)
        # 将特征张量 features 进行了视图变换，将其重新塑造成了一个二维张量，将特征张量转换成适合输入到全连接层
        features = features.view(features.size(0), -1)
        output = self.fc(features)
        # print(output,)
        return output


# 加载图数据集并进行预处理
# 创建数据集对象
# 提取整理数据对象
# 图像+标签
class MyDataset(data.Dataset):
    def __init__(self, rectangle_path, line_path, dataset_type):
        self.rectangle_path = rectangle_path
        self.line_path = line_path
        self.dataset_type = dataset_type
        # 每个图像的路径及它对应的标签
        self.rectangle_paths, self.rectangle_labels = self.read_file(self.rectangle_path)
        self.line_paths, self.line_labels = self.read_file(self.line_path)

    # 定义了获取2张图像和它对应标签的方法
    def __getitem__(self, index):
        # 矩形
        rectangle_img = self.rectangle_paths[index]
        rectangle_label = self.rectangle_labels[index]
        rectangle_img = Image.open(rectangle_img)
        rectangle_img = self.img_transform(rectangle_img)
        # 折线
        line_img = self.line_paths[index]
        line_label = self.line_labels[index]
        line_img = Image.open(line_img)
        line_img = self.img_transform(line_img)
        return rectangle_img, line_img, int(rectangle_label), int(line_label)

    def __len__(self):
        return len(self.rectangle_paths)

    def read_file(self, path):
        # 从文件夹中读取数据
        file_path_list = []
        label_list = []
        for root, dirs, files in os.walk(path):
            for name in files:
                file_path_list.append(os.path.join(root, name))
                label_list.append(int(root[-1]))
            # print(label_list)
        l3 = []
        for i in range(len(file_path_list)):
            l3.append([file_path_list[i], label_list[i]])
        self.shuffle(l3)
        # for item in l3:
        #     print(item[1])
        file_path_list = []
        label_list = []
        for i in range(len(l3)):
            file_path_list.append(l3[i][0])
            label_list.append(l3[i][1])
        # 划分训练集、验证集和测试集，8:1:1
        if self.dataset_type == 0:
            return file_path_list[:int(0.80 * len(file_path_list))], label_list[:int(0.80 * len(label_list))]
        elif self.dataset_type == 1:
            return file_path_list[int(0.80 * len(file_path_list)):int(0.90 * len(file_path_list))], label_list[int(
                0.80 * len(file_path_list)):int(0.90 * len(label_list))]
        else:
            return file_path_list[int(0.90 * len(file_path_list)):], label_list[int(0.90 * len(label_list)):]

    # 洗牌算法（Fisher-Yates 算法）
    @staticmethod
    def shuffle(data):
        n = len(data)
        for i in range(n - 1, 0, -1):
            j = random.randint(0, i)
            data[i], data[j] = data[j], data[i]
        return data

    # 虽然有警告，但这里不能设置静态，静态方法不能访问类的属性
    # 已解决
    @staticmethod
    def img_transform(img):
        # 图像转化为张量，图像归一化，再输入神经网络
        transform = transforms.Compose(
            [
                transforms.ToTensor(),
                # transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
                # transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
                transforms.Normalize(mean=[0.5], std=[0.5])
            ]
        )
        img = transform(img)
        return img


# 训练、验证和测试数据加载器，Adam优化器
# dataset_type代表了训练0、验证1和测试2数据集类型，与文件夹的标签命名无关
train_data = MyDataset(rectangle_path='./atlas_rectangle', line_path='./atlas_line', dataset_type=0)
train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True)
valid_data = MyDataset(rectangle_path='./atlas_rectangle', line_path='./atlas_line', dataset_type=1)
valid_loader = DataLoader(valid_data, batch_size=batch_size, shuffle=True)
test_data = MyDataset(rectangle_path='./atlas_rectangle', line_path='./atlas_line', dataset_type=2)
test_loader = DataLoader(test_data, batch_size=batch_size, shuffle=True)

# 括号内为分类数字
net = DualBranchResNet(2)
# 加载最优参数
# model_params_path = 'model_params.pth'
# if os.path.exists(model_params_path):
#     net.load_state_dict(torch.load(model_params_path))
#     print("成功加载模型参数：", model_params_path)
# else:
#     print("模型参数文件不存在：", model_params_path)
# 模型所有参数的优化
optimizer = torch.optim.Adam(net.parameters(), lr=ir)
if hasattr(torch.cuda, 'empty_cache'):
    torch.cuda.empty_cache()


# 接下来几个函数中的X_rectangle、X_line不可以改小写，会导致性能变差。原因未知。
# train_ch6的acc函数
# 准确率
def evaluate_accuracy(data_iter, net, device):
    # 设置模型为评估模式
    net.eval()
    acc_sum, n = 0.0, 0
    with torch.no_grad():
        for X_rectangle, X_line, y_rectangle, y_line in data_iter:
            X_rectangle = X_rectangle.to(device)
            X_line = X_line.to(device)
            y = y_rectangle.to(device)
            y_hat = net(X_rectangle, X_line)
            acc_sum += (y_hat.argmax(dim=1) == y).sum().cpu().item()
            n += y.shape[0]
    # 恢复模型为训练模式
    net.train()
    return acc_sum / n


# 二分类
# AUC
def evaluate_auc(data_iter, net, device):
    net.eval()
    y_true = []
    y_score = []
    with torch.no_grad():
        for X_rectangle, X_line, y_rectangle, y_line in data_iter:
            X_rectangle = X_rectangle.to(device)
            X_line = X_line.to(device)
            y = y_rectangle.to(device)
            y_hat = net(X_rectangle, X_line)
            y_true.extend(y.cpu().numpy())
            y_score.extend(y_hat[:, 1].cpu().numpy())  # Assuming y_hat is the probability scores for positive class
    y_true = np.array(y_true)
    y_score = np.array(y_score)
    auc = roc_auc_score(y_true, y_score, multi_class='ovr')
    net.train()
    return auc


# F1 Score
def evaluate_f1(data_iter, net, device, times):
    net.eval()
    y_true = []
    y_pred = []
    y_scores = []
    with torch.no_grad():
        for X_rectangle, X_line, y_rectangle, y_line in data_iter:
            X_rectangle = X_rectangle.to(device)
            X_line = X_line.to(device)
            y = y_rectangle.cpu().numpy()  # Assuming y is in numpy format
            y_hat = net(X_rectangle, X_line).argmax(dim=1).cpu().numpy()
            y_scores.append(net(X_rectangle, X_line).cpu().numpy())
            y_true.extend(y)
            y_pred.extend(y_hat)
    if times == 1:
        y_scores = np.concatenate(y_scores)  # Combine scores from all batches
        precision, recall, _ = precision_recall_curve(y_true, y_scores[:, 1])  # Adjust based on your actual output
        # 绘制 PR 曲线图
        plt.figure()
        disp = PrecisionRecallDisplay(precision=precision, recall=recall)
        disp.plot()
        plt.title('Precision-Recall curve')
        plt.show()
    f1 = f1_score(y_true, y_pred, average='micro')
    net.train()
    return f1

# 定义提取特征的函数
def extract_features(model, data_loader):
    model.eval()
    features = []
    labels = []
    with torch.no_grad():
        for X_rectangle, X_line, y_rectangle, y_line in data_loader:
            X_rectangle = X_rectangle.to(device)
            X_line = X_line.to(device)
            y = y_rectangle.to(device)
            features.append(model(X_rectangle, X_line).cpu().numpy())
            labels.extend(y.cpu().numpy())
    return np.concatenate(features), np.array(labels)

# 定义 t-SNE 可视化的函数
def plot_tsne(features, labels, num_classes):
    tsne = TSNE(n_components=2, random_state=0)
    tsne_results = tsne.fit_transform(features)
    plt.figure(figsize=(10, 8))
    unique_labels = np.unique(labels)
    for label in unique_labels:
        plt.scatter(tsne_results[labels == label, 0], tsne_results[labels == label, 1], label=str(label))
    plt.legend()
    plt.title('t-SNE Visualization')
    plt.show()

# 双分支ResNet的训练函数
# train_iter训练数据迭代器，用于遍历训练集数据
def train_ch6(net, train_iter, valid_iter, test_iter, optimizer, device, num_epochs):
    net = net.to(device)
    print("training on", device)
    loss = torch.nn.CrossEntropyLoss()
    batch_count = 0
    best_valid_acc = 0.0  # 记录最佳验证集准确率
    best_test_acc = 0.0  # 记录最佳测试集准确率
    best_test_auc = 0.0  # 记录最佳测试集AUC
    best_test_f1 = 0.0  # 记录最佳测试集F1_Score
    for epoch in range(num_epochs):
        train_l_sum, train_acc_sum, n = 0.0, 0.0, 0
        start = time.time()
        # 遍历训练数据，同时获取矩形图和折线图数据
        for X_rectangle, X_line, y_rectangle, y_line in train_iter:
            X_rectangle = X_rectangle.to(device)
            X_line = X_line.to(device)
            y = y_rectangle.to(device)
            # 通过双分支网络处理数据
            y_hat = net(X_rectangle, X_line)
            # 计算损失
            l = loss(y_hat, y)
            # 反向传播和更新权重
            optimizer.zero_grad()
            l.backward()
            optimizer.step()
            # 累加损失和正确预测的数量
            train_l_sum += l.cpu().item()
            train_acc_sum += (y_hat.argmax(dim=1) == y).sum().cpu().item()
            n += y.shape[0]
            batch_count += 1
        # 计算验证集准确率
        valid_acc = evaluate_accuracy(valid_iter, net, device)
        if valid_acc > best_valid_acc:
            best_valid_acc = valid_acc
            # 保存当前模型参数（或者其他操作）
            torch.save(net.state_dict(), 'model_params.pth')
        # 计算测试集准确率
        test_acc = evaluate_accuracy(test_iter, net, device)
        if test_acc > best_test_acc:
            best_test_acc = test_acc
        # 计算测试集AUC
        test_auc = evaluate_auc(test_iter, net, device)
        if test_auc > best_test_auc:
            best_test_auc = test_auc
        # 计算测试集F1 Score
        test_f1 = evaluate_f1(test_iter, net, device, 0)
        if test_f1 > best_test_f1:
            best_test_f1 = test_f1
        # 打印训练统计信息
        print('epoch %d,   loss %.4f,   train acc %.4f,   valid acc %.4f,   time %.1f sec'
              % (epoch, train_l_sum / n, train_acc_sum / n, valid_acc, time.time() - start))
        print('test acc %.4f,   test auc %.4f,   test f1 %.4f'
              % (test_acc, test_auc, test_f1))
        # print("\n")
        # print(1)
    # 加载最优参数
    model_params_path = 'model_params.pth'
    if os.path.exists(model_params_path):
        net.load_state_dict(torch.load(model_params_path))
        print("成功加载模型参数：", model_params_path)
    else:
        print("模型参数文件不存在：", model_params_path)
    # 在所有epoch完成之后，评估模型在测试集上的准确率
    test_acc = evaluate_accuracy(test_iter, net, device)
    test_auc = evaluate_auc(test_iter, net, device)
    # 最后一次绘制图像
    test_f1 = evaluate_f1(test_iter, net, device, 1)
    print("\n")
    print("Final test accuracy: %.4f,   Final test auc: %.4f,   Final test f1: %.4f"
          % (test_acc, test_auc, test_f1))
    print("Best test accuracy: %.4f,   Best test auc: %.4f,   Best test f1: %.4f"
          % (best_test_acc, best_test_auc, best_test_f1))
    # 提取测试数据的特征
    test_features, test_labels = extract_features(net, test_loader)
    # 执行 t-SNE 降维
    plot_tsne(test_features, test_labels, 7)


# 多分类
# AUC
def multi_auc(data_iter, net, device, num_classes = 5):
        net.eval()
        # 真实标签的各个类别
        y_true = []
        # 每个类别的预测概率
        y_score = []
        with torch.no_grad():
            for X_rectangle, X_line, y_rectangle, y_line in data_iter:
                X_rectangle = X_rectangle.to(device)
                X_line = X_line.to(device)
                # 标签移动到GPU上
                y = y_rectangle.to(device)
                # 获取每个类别的原始分数，通常是一个向量
                y_hat = net(X_rectangle, X_line)
                # 整理真实标签
                y_true.extend(y.cpu().numpy())
                # 对于多分类，用 softmax 函数将 logits 转换为概率
                y_score.extend(torch.nn.functional.softmax(y_hat, dim=1).cpu().numpy())
        y_true = np.array(y_true)
        # print(y_true)
        y_score = np.array(y_score)
        # print(y_true)
        # 计算每个类的 AUC 并计算宏观平均 AUC
        auc_scores = []
        for i in range(num_classes):
            auc_i = roc_auc_score((y_true == i).astype(int), y_score[:, i], multi_class='ovr')
            auc_scores.append(auc_i)
        macro_auc = np.mean(auc_scores)
        net.train()
        # 返回平均AUC
        return macro_auc


# 多分类f1
def multi_f1(data_iter, net, device, times, average='macro'):
    net.eval()
    y_true_list = []
    # 模型预测的类别
    y_pred_list = []
    y_score_list = []
    with torch.no_grad():
        for X_rectangle, X_line, y_rectangle, y_line in data_iter:
            X_rectangle = X_rectangle.to(device)
            X_line = X_line.to(device)
            y = y_rectangle.to(device)
            y_hat = net(X_rectangle, X_line)
            # 获取预测的类别
            _, y_pred = torch.max(y_hat, 1)
            y_true_list.extend(y.cpu().numpy())
            y_pred_list.extend(y_pred.cpu().numpy())
            # 模型输出logits，使用softmax转换为概率
            y_score_list.extend(torch.nn.functional.softmax(y_hat, dim=1).cpu().numpy())
    y_true = np.array(y_true_list)
    y_pred = np.array(y_pred_list)
    y_score = np.array(y_score_list)
    # 宏平均f1分数
    f1 = f1_score(y_true, y_pred, average=average)
    # 最后一次绘制微平均PR曲线
    if times == 1:
        # 对每个类的输出进行二值化
        # 每行一个样本，每列一个类别，有点行one-hot
        y_true_bin = label_binarize(y_true, classes=np.unique(y_true))
        n_classes = y_true_bin.shape[1]
        # 计算每个类别的PR
        precision = dict()
        recall = dict()
        for i in range(n_classes):
            # 精确率、召回率、阈值
            precision[i], recall[i], _ = precision_recall_curve(y_true_bin[:, i], y_score[:, i])
            # 计算每个类的平均精度分数
            # average_precision = auc(recall[i], precision[i])
            # print(f'Class {i} - AUC: {average_precision:0.2f}')
        # 计算精度和召回率的微平均值，即对所有类别的精度和召回率进行平均
        precision_micro, recall_micro, _ = precision_recall_curve(y_true_bin.ravel(), y_score.ravel())
        # 微平均 AUC
        average_precision_micro = auc(recall_micro, precision_micro)
        # print(f'Micro-average - AUC: {average_precision_micro:0.2f}')
        # 绘制微平均值的PR曲线
        plt.figure()
        plt.plot(recall_micro, precision_micro,
                 label='Micro-average PR curve (AUC = {0:0.2f})'.format(average_precision_micro))
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title('Micro-average Precision-Recall curve')
        plt.legend()
        plt.show()
    net.train()
    return f1

# 定义提取特征的函数
def extract_features(model, data_loader):
    model.eval()
    features = []
    labels = []
    with torch.no_grad():
        for X_rectangle, X_line, y_rectangle, y_line in data_loader:
            X_rectangle = X_rectangle.to(device)
            X_line = X_line.to(device)
            y = y_rectangle.to(device)
            features.append(model(X_rectangle, X_line).cpu().numpy())
            labels.extend(y.cpu().numpy())
    return np.concatenate(features), np.array(labels)

# 定义 t-SNE 可视化的函数
def plot_tsne(features, labels, num_classes):
    tsne = TSNE(n_components=2, random_state=0)
    tsne_results = tsne.fit_transform(features)
    plt.figure(figsize=(10, 8))
    unique_labels = np.unique(labels)
    for label in unique_labels:
        plt.scatter(tsne_results[labels == label, 0], tsne_results[labels == label, 1], label=str(label))
    plt.legend()
    plt.title('t-SNE Visualization')
    plt.show()

# 多分支ResNet的训练函数
def train_ch7(net, train_iter, valid_iter, test_iter, optimizer, device, num_epochs):
    net = net.to(device)
    print("training on", device)
    loss = torch.nn.CrossEntropyLoss()
    batch_count = 0
    best_valid_acc = 0.0  # 记录最佳验证集准确率
    best_test_acc = 0.0  # 记录最佳测试集准确率
    best_test_auc = 0.0  # 记录最佳测试集AUC
    best_test_f1 = 0.0  # 记录最佳测试集F1_Score
    for epoch in range(num_epochs):
        train_l_sum, train_acc_sum, n = 0.0, 0.0, 0
        start = time.time()
        # 遍历训练数据，同时获取矩形图和折线图数据
        for X_rectangle, X_line, y_rectangle, y_line in train_iter:
            X_rectangle = X_rectangle.to(device)
            X_line = X_line.to(device)
            y = y_rectangle.to(device)
            # 通过双分支网络处理数据
            y_hat = net(X_rectangle, X_line)
            # 计算损失
            l = loss(y_hat, y)
            # 反向传播和更新权重
            optimizer.zero_grad()
            l.backward()
            optimizer.step()
            # 累加损失和正确预测的数量
            train_l_sum += l.cpu().item()
            train_acc_sum += (y_hat.argmax(dim=1) == y).sum().cpu().item()
            n += y.shape[0]
            batch_count += 1
        # 计算验证集准确率
        valid_acc = evaluate_accuracy(valid_iter, net, device)
        if valid_acc > best_valid_acc:
            best_valid_acc = valid_acc
            # 保存当前模型参数（或者其他操作）
            torch.save(net.state_dict(), 'model_params.pth')
        # 计算测试集准确率
        test_acc = evaluate_accuracy(test_iter, net, device)
        if test_acc > best_test_acc:
            best_test_acc = test_acc
        # 计算测试集AUC
        test_auc = multi_auc(test_iter, net, device)
        # if test_auc > best_test_auc:
        #     best_test_auc = test_auc
        # test_auc = 1
        # 计算测试集F1 Score
        test_f1 = multi_f1(test_iter, net, device, 0)
        if test_f1 > best_test_f1:
            best_test_f1 = test_f1
        # 打印训练统计信息
        print('epoch %d,   loss %.4f,   train acc %.4f,   valid acc %.4f,   time %.1f sec'
              % (epoch, train_l_sum / batch_count, train_acc_sum / n, valid_acc, time.time() - start))
        print('test acc %.4f,   test auc %.4f,   test f1 %.4f'
              % (test_acc, test_auc, test_f1))
        # print("\n")
        # print(1)
    # 加载最优参数
    model_params_path = 'model_params.pth'
    if os.path.exists(model_params_path):
        net.load_state_dict(torch.load(model_params_path))
        print("成功加载模型参数：", model_params_path)
    else:
        print("模型参数文件不存在：", model_params_path)
    # 在所有epoch完成之后，评估模型在测试集上的准确率
    test_acc = evaluate_accuracy(test_iter, net, device)
    test_auc = multi_auc(test_iter, net, device)
    # test_auc = 1
    # 最后一次绘制图像
    test_f1 = multi_f1(test_iter, net, device, 1)
    print("\n")
    print("Final test accuracy: %.4f,   Final test auc: %.4f,   Final test f1: %.4f"
          % (test_acc, test_auc, test_f1))
    print("Best test accuracy: %.4f,   Best test auc: %.4f,   Best test f1: %.4f"
          % (best_test_acc, best_test_auc, best_test_f1))
    # 提取测试数据的特征
    test_features, test_labels = extract_features(net, test_loader)
    # 执行 t-SNE 降维
    plot_tsne(test_features, test_labels, 7)


# 模型训练
# 前向传播、损失计算、反向传播、参数更新和模型评估
# ch6用于二分类，ch7为多分类
train_ch6(net, train_loader, valid_loader, test_loader, optimizer, 'cuda:0', num_epochs)




