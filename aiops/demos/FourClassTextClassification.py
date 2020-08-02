SEED = 1234
N_EPOCHS = 22
N_CLASSES = 4
BATCH_SIZE = 8
HIDDEN_DIM = 256
OUTPUT_DIM = N_CLASSES
N_LAYERS = 2
BIDIRECTIONAL = True
DROPOUT = 0.25
best_valid_loss = float('inf')

import torch
from torchtext import data
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

from aiops.pretrained.models.bert_with_gru_classifier import BertWithGruClassifier
from aiops.pretrained.models.training import ModelTraining
from aiops.utils.text_preprocessing.cleaning import HtmlTextCleaning
from aiops.utils.text_preprocessing.bert import Tokenizer
from aiops.utils.data_augmentation.bert import DomainSpecificClassificationDataSet, FOUR

tokenizer = Tokenizer()
tokenize_and_cut = tokenizer.get_first_tokenized_split
tokenize_and_cut("networkk")


TEXT = tokenizer.get_text_processor()
LABEL = tokenizer.get_label_processor()
import os
os.chdir("C:/ML/code/prod/python/aiops")

four_colored_classes_classification_dataset = FOUR(tokenizer, "my_domain_specific_data--type2-retagged.txt")

merged_train_data, merged_valid_data = four_colored_classes_classification_dataset.get_train_and_valid_domain_dataset(0.9)


LABEL.build_vocab(merged_train_data)
print(LABEL.vocab.stoi)

from torchtext import data
merged_train_data, merged_valid_data = data.BucketIterator.splits(
    (merged_train_data, merged_valid_data), batch_size = BATCH_SIZE, sort=False, device = device)

model = BertWithGruClassifier(HIDDEN_DIM, OUTPUT_DIM, N_LAYERS, BIDIRECTIONAL, DROPOUT, tokenizer)
model = model.to(device)

model.freeze_learning_of_bert_weights()

optimizer = model.get_optimizer()
loss = model.get_loss()
loss = loss.to(device)

model_trainer = ModelTraining(model, optimizer, loss, merged_train_data, merged_valid_data, N_EPOCHS)
training_loss_array, training_accuracy_array, validation_loss_array, validation_accuracy_array = model_trainer.run_epochs_training(model_name="aiops_FOUR_ep-{}.pt")

model_path = "C:/ML/code/prod/python/soa_binaries/ml_models/torch/aiops_FOUR_ep-062.pt"
model = BertWithGruClassifier(HIDDEN_DIM, OUTPUT_DIM, N_LAYERS, BIDIRECTIONAL, DROPOUT, tokenizer, output_label_to_index={'amber': 0, 'grey': 1, 'red': 2, 'green': 3})
model.load_model(model_path)
model.classify("This film is terrible")
model.classify("who replaced bert parks as the host of the miss america pageant ?")
model.classify("Again not all users affected but it is widespread and causing frustration")
model.classify("What were the outage times to each of these circuits?")
model.classify("What were the outage times to each of these circuits?")
model.classify("Getting the module delivered 3 days late is not acceptable.")
model.classify("Module delivered 3 days late and this is not acceptable.")
model.classify("This film is great")
model.classify("Facing this issue from last few days, so kindly help me in resolving the same.")
model.classify("Why the issue is not resolved till now")
