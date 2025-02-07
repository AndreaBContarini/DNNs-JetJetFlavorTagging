# -*- coding: utf-8 -*-
"""LSTM.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1AmkoSioHT-W5xYIoyX839tu2Wrd2PMfy

# **Long Short Term Memory RNN (LSTM)**

#1. Librerie e dataset
"""

from google.colab import drive
drive.mount('/content/gdrive')

!ls /content/gdrive/MyDrive

"""Reinstallo le librerie per averle alla versione più aggiornata:"""

!pip install pandas
!pip install matplotlib
!pip install numpy
!pip install torch
!pip install torchvision
!pip install torchsummary
!pip install torchmetrics

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
import torchvision
from torchvision.transforms import ToTensor
from torch.utils.data import DataLoader, Dataset
from torch import nn
import torch.nn.functional as F
from torch import optim
from sklearn.model_selection import train_test_split
from sklearn.decomposition import PCA
import itertools

"""Carico il dataset dal file numpy compresso:"""

!rm -rf Dataset_numpy.npz
!gdown 19Qu3CfGdsaV70U-WMTRQS3GGCH-lN7SR

"""Prendo meno dati del **dataset** totale: 25000 (obiettivo: velocizzare)"""

N = int(25E3)

dataset = np.load('Dataset_numpy.npz')
tmp_X = dataset['X'].reshape(int(11E6),16)
tmp_y = dataset['y'].reshape(int(11E6),1)
X = tmp_X[:N]
y = tmp_y[:N]

print(np.shape(y))
print(np.shape(X))

"""**GPU**"""

if torch.cuda.is_available():
  print('Numero di GPU disponibili: ',torch.cuda.device_count())
  for i in range(0,torch.cuda.device_count()):
    print(torch.cuda.get_device_name(i))

# se la GPU è disponibile setto device='cuda', altrimenti 'cpu
device = ('cuda' if torch.cuda.is_available() else 'cpu') # Tramite questo oggetto si realizzerà lo spostamento
print("Computation device:", device, "\n")

"""#2. Trattamento dati

Preparazione e normalizzazione dei dati:
"""

a=int(N*0.8)
b=int(N*0.1)
c=N-a-b

# "Med" sta per "mediano": step intermedio

X_train, X_med, y_train, y_med = train_test_split(X, y, test_size = b+c)
X_vali, X_test, y_vali, y_test = train_test_split(X_med, y_med, test_size = c)

mean = np.mean(X_train, axis = 0)
stddev = np.std(X_train, axis = 0)

X_train_norm = (X_train-mean)/stddev
X_vali_norm = (X_vali-mean)/stddev
X_test_norm = (X_test-mean)/stddev

"""Creazione della Classe LSTMDataset (questa cella deve essere runnata anche per usare altre parti del notebook):"""

class LSTMDataset(Dataset):
    def __init__(self, data, labels):
        self.labels = labels #target
        self.sequence_length = sequence_length #lunghezza dela sequenza
        self.y = torch.tensor(labels).float()
        self.X = torch.tensor(data).float()

    def __len__(self):
        return self.X.shape[0]

    # il metodo __getitem__ implementa la logica del dataset

    def __getitem__(self, i):
       outx = self.X[i:i+1,:] # Serve per creare la dimensione aggiuntiva necessaria al funzionamento dell'unità LSTM
       outy = self.y[i]

       return outx, outy

"""Creazione dataset e dataloader:"""

from torch.utils.data import DataLoader
torch.manual_seed(101)

batch_size = 100
sequence_length = 1

train_sequence_dataset = LSTMDataset(
    data = X_train_norm,
    labels = y_train,
    # sequence_length = sequence_length
)

vali_sequence_dataset = LSTMDataset(
    data = X_vali_norm,
    labels = y_vali,
    # sequence_length = sequence_length
)

test_sequence_dataset = LSTMDataset(
    data = X_test_norm,
    labels = y_test,
    # sequence_length = sequence_length
)

train_loader = DataLoader(train_sequence_dataset, batch_size=batch_size, shuffle=False,drop_last=True)
vali_loader = DataLoader(vali_sequence_dataset, batch_size=batch_size, shuffle=False,drop_last=True)
test_loader = DataLoader(test_sequence_dataset, batch_size=batch_size, shuffle=False,drop_last=True)

x, y = next(iter(train_loader))

print("Features shape:", x.shape)
print("Target shape:", y.shape)
print(x)

"""#3. LSTM model"""

from torch import nn

#Struttura della rete neurale LSTM

class myLSTM(nn.Module):
    def __init__(self, input_dim, hidden_dim=16, l1=512, l2=256, l3=128, pdrop=0.3):
        super().__init__()
        self.input_dim = input_dim  # num. di features
        self.hidden_dim = hidden_dim
        self.num_layers = 1 #uso una LSTM con un solo layer

        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            batch_first=True, # necessario se l'input ha shape (batch, seq. len., features) altrimenti (seq.len., batch, features)
            num_layers=self.num_layers
        )

        self.layer1 = nn.Linear(in_features=self.hidden_dim, out_features=l1)
        nn.init.xavier_uniform(self.layer1.weight)
        self.drop1 = nn.Dropout(p=pdrop)
        self.layer2 = nn.Linear(l1, l2)
        nn.init.xavier_uniform(self.layer2.weight)
        self.drop2 = nn.Dropout(p=pdrop)
        self.layer3 = nn.Linear(l2, l3)
        nn.init.xavier_uniform(self.layer3.weight)
        self.drop3 = nn.Dropout(p=pdrop)
        self.layer4 = nn.Linear(l3, 2)
        nn.init.uniform_(self.layer4.weight, a=-0.05, b=0.05)


    def forward(self, x):
        batch_size = x.shape[0]
        # valore iniziale per hidden state e cell state (inzializzo a 0)

        h0 = torch.zeros(self.num_layers, batch_size, self.hidden_dim).requires_grad_().to(device)
        c0 = torch.zeros(self.num_layers, batch_size, self.hidden_dim).requires_grad_().to(device)

        # mi interessa solo l'hidden state: non considero cell state ed output
        on, (hn, cn) = self.lstm(x, (h0, c0))

        # la prima dimensione di h è il numero di layers, pari a 1

        x = self.layer1(hn[0])
        x = F.relu(x)
        x = self.drop1(x)
        x = self.layer2(x)
        x = F.relu(x)
        x = self.drop2(x)
        x = self.layer3(x)
        x = F.relu(x)
        x = self.layer4(x)
        out = F.log_softmax(x, dim=1)
        return out

"""#4. *Ottimizzazione iperparametri*

Ciclo *for* per l'ottimizzazione di alcuni degli iperparametri della rete.

Si vanno ad ottimizzare:

*   Dimensioni dei layer del percettrone finale
*   La *hidden dim* della *LSTM*
*   La probabilità di *dropout* (utile per il percettrone finale);

##Ricerca dei parametri ottimizzati
"""

import time

from torchmetrics import AUROC

loss_func = nn.CrossEntropyLoss()

metric_func = AUROC(num_classes=2)

from torch import optim
LR_ST = 2E-3

contatore = 0

list_l1 = [2**10,2**9,2**8]
list_l2 = [2**9,2**8,2**7]
list_l3 = [2**8,2**7,2**6,2**5]
list_hidden_dim = [14,15,16,70]
list_pdrop = [0.0,0.5,0.9]

Riassunto_Ottimizzazione = {} #Creo un dizionario vuoto in cui raccogliere le performance delle varie reti neurali testate.

for L1 in list_l1:
  for L2 in list_l2:
    for L3 in list_l3:
      for HD in list_hidden_dim:
        for PDROP in list_pdrop:
          contatore += 1
          t0 = time.time()
          model = myLSTM(input_dim=16, hidden_dim=HD, l1=L1, l2=L2, l3=L3, pdrop=PDROP)
          model = model.to(device)
          LR_ST = 2E-3

          opt = optim.SGD(model.parameters(), lr = LR_ST, momentum = 0.9)

          scheduler = optim.lr_scheduler.StepLR(opt, 50, gamma=0.05, last_epoch=-1, verbose=True)

          feat, label = next(iter(train_loader))

          feat=feat.to(device)
          label=label.to(device)

          out = model(feat)

          if out != None:
            print("Parametri Rete: l1=",L1," l2=",L2," l3=",L3," hidden_dim=",HD," pdrop=",PDROP, "["+str(contatore)+"/"+str(len(list_l1)*len(list_l2)*len(list_l3)*len(list_hidden_dim)*len(list_pdrop))+"]")
          import time


          # numero di epoche
          epochs = 10


          # liste su cui salvare il valore della loss e della metrica ad ogni epoca
          hist_loss = []
          hist_metric = []
          hist_vloss = []
          hist_vmetric = []


          # loop sulle epoche
          for epoch in range(epochs):

                  # training step (in cui aggiorniamo i pesi della rete neurale)
                  model.train()
                  train_loss = 0
                  train_metric = 0
                  counter = 0
                  for xb, yb in train_loader:
                      counter += 1
                      yb=yb.type(torch.LongTensor) # Necessario questo casting, secondo le specifiche della classe CrossEntropy
                      xb=xb.to(device)
                      yb=yb.to(device).view(batch_size)
                      pred = model(xb)
                      # calcolo loss e metrica
                      loss = loss_func(pred, yb)
                      prob_pred = torch.exp(pred)
                      metric = metric_func(prob_pred, yb)
                      # aggiorno la loss e metrica totale
                      train_loss += loss.item()
                      train_metric += metric.item()
                      # backpropagation
                      opt.zero_grad() #resetta i gradienti prima di eseguire la backpropagation
                      loss.backward() #calcola i gradeinti della loss
                      opt.step() #aggiorna i pesi

                      # RESET DELLE METRICHE (*IMPORTANTISSIMO*)

                      metric_func.reset()

                  train_loss /= counter
                  train_metric /= (counter)
                  hist_loss.append(train_loss)
                  hist_metric.append(train_metric)

                  # validation step (non vengono aggiornati i pesi)
                  model.eval()
                  vali_loss = 0
                  vali_metric = 0
                  counter = 0
                  with torch.no_grad(): #evita che si aggiornino i pesi
                      for xb, yb in vali_loader:
                        counter += 1

                        yb=yb.type(torch.LongTensor) # Necessario questo casting, secondo le specifiche della classe CrossEntropy

                        xb=xb.to(device)
                        yb=yb.to(device).view(batch_size)

                        pred = model(xb) #predizione del modello
                        # calcolo loss e metrica
                        vloss = loss_func(pred, yb)

                        prob_pred = torch.exp(pred)
                        vmetric = metric_func(prob_pred, yb)

                        vali_loss += vloss.item()
                        vali_metric += vmetric.item()

                        # RESET DELLE METRICHE (*IMPORTANTISSIMO*)

                        metric_func.reset()

                  vali_loss /= counter
                  vali_metric /= (counter)
                  hist_vloss.append(vali_loss)
                  hist_vmetric.append(vali_metric)



                  elapsed_time = time.time()-t0

                  scheduler.step()

                  #salvataggio nel dizionario della migliore iterazione della rete fra le varie epoche in cui è stata ottimizzata
                  if epoch == epochs-1:
                    hist_vloss = np.array(hist_vloss)
                    hist_vmetric = np.array(hist_vmetric)
                    Riassunto_Ottimizzazione["input_dim=16, l1="+str(L1)+", l2="+str(L2)+", l3="+str(L3)+", hidden_dim="+str(HD)+", pdrop="+str(PDROP)]=np.array([hist_vloss[np.argmax(hist_vmetric)],hist_vmetric[np.argmax(hist_vmetric)]]) #per discriminare le epoche della stessa rete in base alla metrica posse al posto di hist_vloss nelle parentesi tonde hist_vmetric.
                    print('Elapsed time:', time.time()-t0, 'Loss:', hist_vloss[np.argmax(hist_vmetric)],'Metrica:',hist_vmetric[np.argmax(hist_vmetric)])

"""Cella che ricerca i parametri ottimizzati"""

Valori_Ottimizzazione = np.array(list(Riassunto_Ottimizzazione.values()))
optimized_index = np.argmax(Valori_Ottimizzazione[:,1])
best_loss_metric = Valori_Ottimizzazione[optimized_index]
parametri_ottimizzati = [key for key,value in Riassunto_Ottimizzazione.items() if value[1]==best_loss_metric[1]]

print("Parametri della Rete Ottimizzata:")
print(parametri_ottimizzati)
print("Best Validation Loss and Validation Metric:", best_loss_metric)

"""Parametri ottimizzati trovati dal programma ottimizzatore:


*   l1 = 256
*   l2 = 128
*   l3 = 64
*   hidden dimension = 14
*   probabilità di dropout = 0.0

La loss e la metrica (AUROC) migliori della rete che ha vinto la corsa dell'ottimizzazione sono:

Cross Entropy Loss: 0.19634474

Roc Auc: 0.90967505

#5. Preliminari necessari
"""

#Prendo tutti e 11 milioni di dati del dataset.

N = int(11E6)

dataset = np.load('Dataset_numpy.npz')
tmp_X = dataset['X'].reshape(int(11E6),16)
tmp_y = dataset['y'].reshape(int(11E6),1)
X = tmp_X[:N]
y = tmp_y[:N]

print(np.shape(y))
print(np.shape(X))

"""##i) Splitting: train - test - validation (+ normalizzazione)"""

a=int(N*0.8)
b=int(N*0.1)
c=N-a-b

X_train, X_med, y_train, y_med = train_test_split(X, y, test_size = b+c,shuffle=False)
X_vali, X_test, y_vali, y_test = train_test_split(X_med, y_med, test_size = c,shuffle=False)

mean = np.mean(X_train, axis = 0)
stddev = np.std(X_train, axis = 0)

X_train_norm = (X_train-mean)/stddev
X_vali_norm = (X_vali-mean)/stddev
X_test_norm = (X_test-mean)/stddev

"""##ii) Dataset e Dataloaders"""

from torch.utils.data import DataLoader
torch.manual_seed(101)

batch_size = 100
sequence_length = 1

train_sequence_dataset = LSTMDataset(
    data = X_train_norm,
    labels = y_train,
)

vali_sequence_dataset = LSTMDataset(
    data = X_vali_norm,
    labels = y_vali,
)

test_sequence_dataset = LSTMDataset(
    data = X_test_norm,
    labels = y_test,
)

train_loader = DataLoader(train_sequence_dataset, batch_size=batch_size, shuffle=False,drop_last=True)
vali_loader = DataLoader(vali_sequence_dataset, batch_size=batch_size, shuffle=False,drop_last=True)
test_loader = DataLoader(test_sequence_dataset, batch_size=batch_size, shuffle=False,drop_last=True)

x, y = next(iter(train_loader))

print("Features shape:", x.shape)
print("Target shape:", y.shape)
print(x)

"""##iii) Definizioni preliminari utili al training
Definisco: ottimizzatori, scheduler, funzioni di metrica e loss e variabili da inizializzare
"""

loss_func = nn.CrossEntropyLoss()
from torch import optim
LR_ST = 2E-3

from torchmetrics import AUROC

metric_func = AUROC(num_classes=2)

num_hidden_units = 16
model_2 = myLSTM(input_dim=16, l1=256, l2=128, l3=64, hidden_dim=14, pdrop=0.0)

opt = optim.SGD(model_2.parameters(), lr = LR_ST, momentum = 0.9)

scheduler = optim.lr_scheduler.StepLR(opt, 50, gamma=0.05, last_epoch=-1, verbose=True)

epochs_done = 0

print(model_2)

#from torchsummary import summary
#summary(model_2.cuda(), input_size=(1,16))

"""Sposto il modello della rete sulla GPU"""

model_2.to(device)
print(next(model_2.parameters()).device)

"""## iv) **Best** and **last model** classes"""

class SaveBestModel: # Ad ogni epoca si controlla se il modello è migliorato; in caso, lo si salva
  def __init__(self, best_valid_loss = float('inf')): #object initialized with best_loss = +infinite. In questo modo si è sicuri che anche solo la prima epoca verrà salvata
      self.best_valid_loss = best_valid_loss


  def __call__(
      self, current_valid_loss,
      epoch, model, optimizer, criterion, metric,
  ):
      if current_valid_loss < self.best_valid_loss:
         self.best_valid_loss = current_valid_loss
         torch.save({'model' : model,
                'epoch': epoch+1,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': criterion,
                'metric': metric,
                'best validation loss': current_valid_loss,
                }, 'best_model.pt') # Si crea un dizionario per aver ulteriori informazioni sul modello che è stato salvato. Vanno bene sia i formati pt, sia pth


class SaveLastModel:
  def __init__(self, dummy=0):
        self.dummy = 0

  def __call__(
      self,current_vali_loss, epoch, model, criterion, metric, scheduler, optimizer):
      torch.save({'model' : model,
                'epoch': epoch+1,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': criterion,
                'metric': metric,
                'vali loss': current_vali_loss,
                'scheduler': scheduler,
                'optimizer': optimizer,
                }, 'last_model.pt') # Si crea un dizionario per aver ulteriori informazioni sul modello che è stato salvato. Vanno bene sia i formati pt, sia pth

"""#**Training loop (1)**

###1a tranche
"""

# Commented out IPython magic to ensure Python compatibility.
import time

save_best_model = SaveBestModel()
save_last_model = SaveLastModel()

# numero di epoche
epochs = 45 - epochs_done

# liste su cui salvare il valore della loss e della metrica ad ogni epoca per poterli graficare in funzione
# dell'epoca a fine addestramento
hist_loss = []
hist_metric = []
hist_vloss = []
hist_vmetric = []


# loop sulle epoche
for epoch in range(epochs):
    t0 = time.time()

    # training step (in cui aggiorniamo i pesi della rete neurale)
    model_2.train()
    train_loss = 0
    train_metric = 0
    counter = 0
    for xb, yb in train_loader:
        counter += 1

        yb=yb.type(torch.LongTensor) # Necessario questo casting, secondo le specifiche della classe CrossEntropy

        xb=xb.to(device)
        #print(len(xb[0][0].tolist()))
        yb=yb.to(device).view(batch_size)

        # print(xb.view(batch_size).shape())

        pred = model_2(xb)

        # calcolo loss e metrica
        loss = loss_func(pred, yb)
        prob_pred = torch.exp(pred)
        metric = metric_func(prob_pred, yb)

        # aggiorno la loss e metrica totale
        train_loss += loss.item()
        train_metric += metric.item()

        # backpropagation
        opt.zero_grad() #resetta i gradienti prima di eseguire la backpropagation
        loss.backward() #calcola i gradeinti della loss
        opt.step() #aggiorna i pesi

        # RESET DELLE METRICHE (*IMPORTANTISSIMO*)

        metric_func.reset()


    train_loss /= counter
    train_metric /= (counter)
    hist_loss.append(train_loss)
    hist_metric.append(train_metric)

    # validation step (non vengono aggiornati i pesi)
    model_2.eval()
    vali_loss = 0
    vali_metric = 0
    counter = 0
    with torch.no_grad(): #evita che si aggiornino i pesi
      for xb, yb in vali_loader:
        counter += 1

        yb=yb.type(torch.LongTensor) # Necessario questo casting, secondo le specifiche della classe CrossEntropy

        xb=xb.to(device)
        yb=yb.to(device).view(batch_size)

        pred = model_2(xb) #predizione del modello
        # calcolo loss e metrica
        vloss = loss_func(pred, yb)

        prob_pred = torch.exp(pred)
        vmetric = metric_func(prob_pred, yb)

        vali_loss += vloss.item()
        vali_metric += vmetric.item()

        # RESET DELLE METRICHE (*IMPORTANTISSIMO*)

        metric_func.reset()

    vali_loss /= counter
    vali_metric /= (counter)
    hist_vloss.append(vali_loss)
    hist_vmetric.append(vali_metric)

    ########### SALVO SU DRIVE IL BEST MODEL ###########
    save_best_model(vali_loss, epoch, model_2, opt, loss_func, metric_func)

    model_save_name1 = 'best_model.pt'
    path1 = F"/content/gdrive/MyDrive/{model_save_name1}"
    torch.save(model_2.state_dict(), path1)


    #printout su colab di epoche, loss e metrica
    elapsed_time = time.time()-t0
    print("epoch: %d, time(s): %.4f, train loss: %.6f, train metric: %.6f, vali loss: %.6f, vali metric: %.6f"
#           % (epoch+1, elapsed_time, train_loss, train_metric, vali_loss, vali_metric))

    # update learning rate schedule alla fine di ogni epoca
    scheduler.step() #serve per aggiornare il learning rate schedular


    ########### SALVO SU DRIVE IL LAST MODEL ###########
    save_last_model(vali_loss, epoch+epochs_done, model_2, loss_func, metric_func, scheduler, opt)

    model_save_name2 = 'last_model.pt'
    path2 = F"/content/gdrive/MyDrive/{model_save_name2}"
    torch.save(model_2.state_dict(), path2)

"""### **SAVING LISTS on drive .txt files**
(NECESSARY FOR PLOTTING LATER ON)

####hist_loss_save
"""

hist_loss_save = 'hist_loss.txt'
path_a = F"/content/gdrive/MyDrive/{hist_loss_save}"

with open(path_a, 'w') as temp_file:
    for i in hist_loss:
        temp_file.write("%f, " % i)
        #temp_file.write(hist_loss)

#vedo cosa ho printato
#file = open(path_a, 'r')
#print(file.read())
#file.close()

"""####hist_metric_save"""

hist_metric_save = 'hist_metric.txt'
path_b = F"/content/gdrive/MyDrive/{hist_metric_save}"

with open(path_b, 'w') as temp_file:
    for item in hist_metric:
        temp_file.write("%f, " % item)

#file = open(path_b, 'r')
#print(file.read())
#file.close()

"""####hist_vloss_save"""

hist_vloss_save = 'hist_vloss.txt'
path_c = F"/content/gdrive/MyDrive/{hist_vloss_save}"

with open(path_c, 'w') as temp_file:
    for item in hist_vloss:
        temp_file.write("%f, " % item)

#file = open(path_c, 'r')
#print(file.read())
#file.close()

"""####hist_vmetric_save"""

hist_vmetric_save = 'hist_vmetric.txt'
path_d = F"/content/gdrive/MyDrive/{hist_vmetric_save}"

with open(path_d, 'w') as temp_file:
    for item in hist_vmetric:
        temp_file.write("%f, " % item)

#file = open(path_d, 'r')
#print(file.read())
#file.close()

"""#**Re-loading**
**Si interrompe il runtime: devo RICARICARE tutte le librerie, dati e parametri necessari**

#**Training loop (2)**

###2a tranche
"""

# Commented out IPython magic to ensure Python compatibility.
import time

device = ('cuda' if torch.cuda.is_available() else 'cpu')

# Carico il BEST da drive
model_name1 = 'best_model.pt'
path1 = F"/content/gdrive/MyDrive/{model_name1}"
model = myLSTM(input_dim=16, l1=256, l2=128, l3=64, hidden_dim=14, pdrop=0.0)
model.load_state_dict(torch.load(path1))
model.to(device) #metto modello su GPU
model.train()

# Carico il LAST da drive
model_name2 = 'last_model.pt'
path2 = F"/content/gdrive/MyDrive/{model_name2}"
model.load_state_dict(torch.load(path1))
model.to(device) #metto modello su GPU
model.train()

save_best_model = SaveBestModel()
save_last_model = SaveLastModel()

# numero di epoche
epochs = 55 - epochs_done

# liste su cui salvare il valore della loss e della metrica ad ogni epoca per poterli graficare in funzione
# dell'epoca a fine addestramento
hist_loss = []
hist_metric = []
hist_vloss = []
hist_vmetric = []

# loop sulle epoche
for epoch in range(epochs):
    t0 = time.time()

    # training step (in cui aggiorniamo i pesi della rete neurale)
    model_2.train()
    train_loss = 0
    train_metric = 0
    counter = 0
    for xb, yb in train_loader:
        counter += 1

        yb=yb.type(torch.LongTensor) # Necessario questo casting, secondo le specifiche della classe CrossEntropy

        xb=xb.to(device)
        #print(len(xb[0][0].tolist()))
        yb=yb.to(device).view(batch_size)

        # print(xb.view(batch_size).shape())

        pred = model_2(xb)

        # calcolo loss e metrica
        loss = loss_func(pred, yb)
        prob_pred = torch.exp(pred)
        metric = metric_func(prob_pred, yb)

        # aggiorno la loss e metrica totale
        train_loss += loss.item()
        train_metric += metric.item()

        # backpropagation
        opt.zero_grad() #resetta i gradienti prima di eseguire la backpropagation
        loss.backward() #calcola i gradeinti della loss
        opt.step() #aggiorna i pesi

        # RESET DELLE METRICHE (*IMPORTANTISSIMO*)

        metric_func.reset()


    train_loss /= counter
    train_metric /= (counter)
    hist_loss.append(train_loss)
    hist_metric.append(train_metric)

    # validation step (non vengono aggiornati i pesi)
    model_2.eval()
    vali_loss = 0
    vali_metric = 0
    counter = 0
    with torch.no_grad(): #evita che si aggiornino i pesi
      for xb, yb in vali_loader:
        counter += 1

        yb=yb.type(torch.LongTensor) # Necessario questo casting, secondo le specifiche della classe CrossEntropy

        xb=xb.to(device)
        yb=yb.to(device).view(batch_size)

        pred = model_2(xb) #predizione del modello
        # calcolo loss e metrica
        vloss = loss_func(pred, yb)

        prob_pred = torch.exp(pred)
        vmetric = metric_func(prob_pred, yb)

        vali_loss += vloss.item()
        vali_metric += vmetric.item()

        # RESET DELLE METRICHE (*IMPORTANTISSIMO*)

        metric_func.reset()

    vali_loss /= counter
    vali_metric /= (counter)
    hist_vloss.append(vali_loss)
    hist_vmetric.append(vali_metric)

    ########### SALVO SU DRIVE IL BEST MODEL ###########
    save_best_model(vali_loss, epoch, model_2, opt, loss_func, metric_func)

    model_save_name1 = 'best_model.pt'
    path1 = F"/content/gdrive/MyDrive/{model_save_name1}"
    torch.save(model.state_dict(), path1)


    #printout su colab dei epoche loss e metrica
    elapsed_time = time.time()-t0
    print("epoch: %d, time(s): %.4f, train loss: %.6f, train metric: %.6f, vali loss: %.6f, vali metric: %.6f"
#           % (epoch+1, elapsed_time, train_loss, train_metric, vali_loss, vali_metric))

    # update learning rate schedule alla fine di ogni epoca
    scheduler.step() #serve per aggiornare il learning rate schedular

    ########### SALVO SU DRIVE IL LAST MODEL ###########
    save_last_model(vali_loss, epoch+epochs_done, model_2, loss_func, metric_func, scheduler, opt)

    model_save_name2 = 'last_model.pt'
    path2 = F"/content/gdrive/MyDrive/{model_save_name2}"
    torch.save(model.state_dict(), path2)

"""###SALVATAGGIO NUOVO"""

hist_loss_save = 'hist_loss.txt'
path_a = F"/content/gdrive/MyDrive/{hist_loss_save}"

with open(path_a, 'a') as temp_file:
    for i in hist_loss:
        temp_file.write("%f, " % i)

#file = open(path_a, 'r')
#print(file.read())
#file.close()

hist_metric_save = 'hist_metric.txt'
path_b = F"/content/gdrive/MyDrive/{hist_metric_save}"

with open(path_b, 'a') as temp_file:
    for item in hist_metric:
        temp_file.write("%f, " % item)

hist_vloss_save = 'hist_vloss.txt'
path_c = F"/content/gdrive/MyDrive/{hist_vloss_save}"

with open(path_c, 'a') as temp_file:
    for i in hist_vloss:
        temp_file.write("%f, " % i)

hist_vmetric_save = 'hist_vmetric.txt'
path_d = F"/content/gdrive/MyDrive/{hist_vmetric_save}"

with open(path_d, 'a') as temp_file:
    for item in hist_vmetric:
        temp_file.write("%f, " % item)

"""###Carico gli array dai file .txt per plottare"""

print("ATTENZIONE: NON DEVO AVERE ARRAY UNIDIMENSIONALE, BENSI' N-DIMENSIONALE, con N == #epoche totali")
print()

import numpy as np
hist_loss_save = 'hist_loss.txt'
path_a = F"/content/gdrive/MyDrive/{hist_loss_save}"
hist_loaded_loss = np.fromfile(path_a, dtype=float, count=- 1, sep=',')
print(type(hist_loaded_loss))
print("Size array hist_loaded_loss =", hist_loaded_loss.size)

print()

hist_metric_save = 'hist_metric.txt'
path_b = F"/content/gdrive/MyDrive/{hist_metric_save}"
hist_loaded_metric = np.fromfile(path_b, dtype=float, count=- 1, sep=',')
print(type(hist_loaded_metric))
print("Size array hist_loaded_metric =" , hist_loaded_metric.size)

print()
hist_vloss_save = 'hist_vloss.txt'
path_c = F"/content/gdrive/MyDrive/{hist_vloss_save}"
hist_loaded_vloss = np.fromfile(path_c, dtype=float, count=- 1, sep=',')
print(type(hist_loaded_vloss))
print("Size array hist_loaded_vloss = ", hist_loaded_vloss.size)

print()

hist_vmetric_save = 'hist_vmetric.txt'
path_d = F"/content/gdrive/MyDrive/{hist_vmetric_save}"
hist_loaded_vmetric = np.fromfile(path_d, dtype=float, count=- 1, sep=',')
print(type(hist_loaded_vmetric))
print("Size array hist_loaded_vmetric = ", hist_loaded_vmetric.size)

"""#**PLOTTING section**:
Grafico l'ndamento della *Loss* e della Metrica (*AUC*) in funzione delle epoche
"""

plt.figure(figsize=(13, 6))
plt.subplot(1,2,2)
plt.plot(range(1,len(hist_loaded_loss)+1), hist_loaded_loss, '-o', color='orange', label='train loss')
plt.plot(range(1,len(hist_loaded_vloss)+1), hist_loaded_vloss, '-o', color='green', label='validation loss')
plt.xlabel('Epochs')
plt.ylabel('CrossEntropyLoss')
plt.title('ANDAMENTO DELLA LOSS')
plt.grid()
plt.legend(loc='center right')

plt.subplot(1,2,1)
plt.plot(range(1,len(hist_loaded_metric)+1),hist_loaded_metric, '-o', color='orange', label='train metric')
plt.plot(range(1,len(hist_loaded_vmetric)+1),hist_loaded_vmetric, '-o', color='green', label='validation metric')
plt.xlabel('Epochs')
plt.ylabel('Metric AUC')
plt.title('ANDAMENTO DELLA METRICA')
plt.grid()
plt.legend(loc='lower right')

plt.tight_layout()
plt.savefig('Andamento_Loss_Metrica_LSTM.pdf', format='pdf')
plt.show()

"""Salvataggio del modello finale"""

final_model = torch.load('./best_model.pt')
torch.save(final_model, './trained_model.pt')

"""#**Test**"""

# Commented out IPython magic to ensure Python compatibility.
from sklearn.metrics import roc_curve

loss_func = nn.CrossEntropyLoss()
from torch import optim

from torchmetrics import AUROC

metric_func = AUROC(num_classes=2)


plt.figure(figsize=(8,8))

model = torch.load('./trained_model.pt')
model['model'].eval()
test_loss = 0
test_metric = 0
counter = 0

megapred = []
megatarget = []
megapred = np.array(megapred)
megatarget = np.array(megatarget)

device = 'cpu' # Serve per soddisfare un comando interno alle operazioni del cell-state (che manda l'hidden state su device)

model['model'].to(device)

# with torch.no_grad(): #evita che si aggiornino i pesi
for xb, yb in test_loader:
  counter += 1

  yb=yb.type(torch.LongTensor) # Necessario questo casting, secondo le specifiche della classe CrossEntropy

  xb=xb.to(device)
  yb=yb.to(device).view(batch_size)

  pred = model['model'](xb) #predizione del modello

  # calcolo loss e metrica
  tloss = loss_func(pred, yb)

  prob_pred = torch.exp(pred)
  prob_positive = prob_pred[:,1].detach().numpy()
  tmetric = metric_func(prob_pred, yb)

  batch_target = yb.numpy()

  megapred = np.append(megapred, prob_positive)
  megatarget = np.append(megatarget, batch_target)

  test_loss += tloss.item()
  test_metric += tmetric.item()

  metric_func.reset()

test_loss /= counter
test_metric /= (counter)

fpr, tpr, thresholds = roc_curve(megatarget, megapred, pos_label=1)
plt.plot(fpr,tpr,'blue')
plt.ylabel('True Positive Rate')
plt.xlabel('False Positive Rate')
plt.title('Long Short Term Memory RNN')
plt.xlim(0,1)
plt.plot([0,1],[0,1],'--k')
plt.ylim(0,1)
plt.tight_layout()
plt.savefig('ROC_LSTM_Dataset_Normale_Test_set.pdf', format='pdf')
plt.show()

print("test loss: %.6f, test metric: %.6f"
#           % (test_loss, test_metric))



# Per far sì che il device sia di nuovo cuda, se disponibile:

if torch.cuda.is_available():
  print('Numero di GPU disponibili: ',torch.cuda.device_count())
  for i in range(0,torch.cuda.device_count()):
    print(torch.cuda.get_device_name(i))

device = ('cuda' if torch.cuda.is_available() else 'cpu') # Tramite questo oggetto si realizzerà lo spostamento
print("Computation device:", device, "\n")

"""##**Matrice di Confusione**"""

from sklearn.metrics import confusion_matrix

predictions = []

for i in range(len(megapred)):
  if megapred[i]<=0.5:
    predictions.append(0)
  else:
    predictions.append(1)

predictions = np.array(predictions)

conf_m = confusion_matrix(megatarget, predictions)
conf_m = conf_m.astype('float') / conf_m.sum(axis=1)[:, np.newaxis]
fig = plt.figure(figsize = (12,12))
ax = fig.add_subplot(111)
ax.imshow(conf_m, cmap ='gray')
thresh = conf_m.max()/2.5
ax.axis('off')
plt.title('Matrice di Confusione LSTM (Dataset Normale)',fontsize='xx-large')
for x in range(2):
    for y in range(2):
        val = round(conf_m[x][y],5) if conf_m[x][y] !=0 else 0
        ax.annotate(str(val), xy=(y,x),
                    horizontalalignment='center',
                    verticalalignment='center',
                    color='white' if conf_m[x][y]<thresh else 'black',
                    fontsize='xx-large')

plt.tight_layout()
plt.show()