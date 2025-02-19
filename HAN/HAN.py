import dgl
import copy
import torch
import random
import numpy as np
import pandas as pd
from model import HAN
from sklearn.metrics import accuracy_score


def setup_seed(seed):
    """
    fix the random seed
    :param seed: the random seed
    """
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    return None

setup_seed(0)

# attribute
name2id = {}
id2name = {}

x = pd.read_csv("模型输入数据/features.csv")

for i in range(len(x)):
    name = x.loc[i][0]
    id2name[i] = name
    name2id[name] = i

x = x.iloc[:, 1:]
x = x.to_numpy()

# attribute

adj = pd.read_csv("模型输入数据/Network.csv")

max_id = x.shape[0]
edges_1 = []
edges_2 = []
for i in range(len(adj)):
    start = adj.loc[i][0]
    mid = adj.loc[i][1]
    end = adj.loc[i][2]
    # if start != "NA":
    #     try:
    #         name2id[start]
    #     except:
    #         name2id[start] = max_id
    #         id2name[max_id] = start
    #         max_id += 1
    #
    # if mid != "NA":
    #     try:
    #         name2id[mid]
    #     except:
    #         name2id[mid] = max_id
    #         id2name[max_id] = mid
    #         max_id += 1
    #
    # if end != "NA":
    #     try:
    #         name2id[end]
    #     except:
    #         name2id[end] = max_id
    #         id2name[max_id] = end
    #         max_id += 1

    if 1:
        try:
            edges_1.append([name2id[start], name2id[mid]])
        except:
            pass
        try:
            edges_1.append([name2id[mid], name2id[start]])
        except:
            pass
    if 1:
        try:
            edges_2.append([name2id[mid], name2id[end]])
        except:
            pass
        try:
            edges_2.append([name2id[end], name2id[mid]])
        except:
            pass

label = pd.read_csv("模型输入数据/label.csv")

y = np.zeros((x.shape[0], ))
for i in range(len(label["code"])):
    try:
        index = name2id[label["code"].iloc[i]]
        y[index] = label["label"].iloc[i]
    except:
        pass

y = torch.tensor(y).float()

# x = np.concatenate([x, np.zeros((len(name2id)-x.shape[0], 5))], axis=0)

x = torch.tensor(x).float()
# print(x.shape)
# print(len(id2name))
# print(len(name2id))
g = dgl.heterograph(
    {
        ('rna', 'type1', 'rna'): edges_1,
        ('rna', 'type2', 'rna'): edges_2
    }
)

# print(x.shape)
print(g)


# logits = rgcn_net(None, None)
# y_pred = (logits >= 0.5).int().squeeze(dim=-1)

# acc = accuracy_score(y[test_id], y_pred[test_id])
# print(acc)

# print(emb["inc_rna"].shape)
# print(emb["m_rna"].shape)

#
# GCN
criterion = torch.nn.BCELoss()

# print(g)
han_net = HAN(
    meta_paths=[["type1", "type2"], ["type2", "type1"]],
    in_size=x.shape[1],
    hidden_size=300,
    out_size=1,
    num_heads=[16],
    dropout=0,
)

optimizer = torch.optim.Adam(han_net.parameters(), lr=1e-3)

idx = list(range(x.shape[0]))
random.shuffle(idx)
idx = np.array(idx)

train_id = idx[:int(x.shape[0]*0.7)]
test_id = idx[int(x.shape[0]*0.7):]

best_acc = 0
for epoch in range(100):
    logits = han_net(g, x)
    loss = criterion(logits.squeeze(dim=-1)[train_id], y[train_id])
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    logits = han_net(g, x)
    y_pred = (logits >= 0.5).int().squeeze(dim=-1)
    acc = accuracy_score(y[test_id], y_pred[test_id])
    print(acc)
    if best_acc < acc:
        best_acc = acc
        best_model = copy.deepcopy(han_net)


logits = best_model(g, x)
y_pred = (logits >= 0.5).int().squeeze(dim=-1)

logits_list = logits[test_id][:, 0].data
index = sorted(range(len(logits_list)), key=lambda k: logits_list[k], reverse=True)
print(test_id[index])
for i in test_id[index]:
    print(id2name[i])

for i in test_id[index]:
    print(y_pred[i].detach().numpy())

print(logits_list[index])

acc = accuracy_score(y[test_id], y_pred[test_id])
print(acc)


from sklearn.metrics import confusion_matrix
cm = confusion_matrix(y[test_id], y_pred[test_id])
print(cm)

acc = accuracy_score(y[test_id], y_pred[test_id])
print("final", acc)

import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score, precision_score, f1_score, recall_score, classification_report

y_true = y[test_id]
y_pred = y_pred[test_id]
# 1.计算混淆矩阵
cm = confusion_matrix(y_true, y_pred)
conf_matrix = pd.DataFrame(cm, index=['0', '1'], columns=['0', '1'])  # 数据有5个类别
# 画出混淆矩阵
fig, ax = plt.subplots(figsize=(4.5, 4.5))
sns.heatmap(conf_matrix, annot=True, annot_kws={"size": 14}, cmap="Blues")
plt.ylabel('True label', fontsize=14)
plt.xlabel('Predicted label', fontsize=14)
plt.xticks(fontsize=14)
plt.yticks(fontsize=14)
plt.show()
logits = logits[test_id]
print('logits', logits)
from sklearn import metrics
fpr, tpr, thresholds = metrics.roc_curve(y_true, logits.detach().numpy())
auc = metrics.auc(fpr, tpr)

#
# # 2.计算accuracy
# print('accuracy_score', accuracy_score(y_true, y_pred))
#
# # 3.计算多分类的precision、recall、f1-score分数
print("final", acc)
print('precision', precision_score(y_true, y_pred))
print('recall', recall_score(y_true, y_pred))
print('f1-score', f1_score(y_true, y_pred))
print('auc', auc)
#
# # 下面这个可以显示出每个类别的precision、recall、f1-score。
# print('classification_report\n', classification_report(y_true, y_pred))

from sklearn.metrics import roc_curve, auc
import matplotlib.pyplot as plt

fpr, tpr, thersholds = roc_curve(y_true, logits.detach().numpy())
for i in range(len(y_true)):
    print(int(y_true[i].item()), logits[i].item())

for i, value in enumerate(thersholds):
    print("%f %f %f" % (fpr[i], tpr[i], value))

roc_auc = auc(fpr, tpr)

print("fpr:", fpr)
print("tpr:", tpr)

plt.plot(fpr, tpr, 'k--', label='ROC (area = {0:.4f})'.format(roc_auc), lw=2)

plt.xlim([-0.05, 1.05])  # 设置x、y轴的上下限，以免和边缘重合，更好的观察图像的整体
plt.ylim([-0.05, 1.05])
# plt.plot([0 ,1], [0, 1], color='navy', linestype='--')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')  # 可以使用中文，但需要导入一些库即字体
plt.title('ROC Curve')
plt.legend(loc="lower right")
plt.show()
print(len(y_true))