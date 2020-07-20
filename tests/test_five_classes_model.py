from aiops.pretrained.models.text_classification import BertEmbeddingsClassifier
from aiops.utils.text_preprocessing.bert import Tokenizer
from aiops.utils.data_augmentation.bert import FiveClassesClassificationDataSet
from torchtext import data

N_EPOCHS = 7
BATCH_SIZE = 2
HIDDEN_DIM = 256
OUTPUT_DIM = 5
N_LAYERS = 2
BIDIRECTIONAL = True
DROPOUT = 0.25
device = None

tokenizer = Tokenizer()
print(tokenizer.get_tokenized_splits("networkk"))
TEXT = tokenizer.get_text_processor()
LABEL = tokenizer.get_label_processor()
five_classes_classification_dataset = FiveClassesClassificationDataSet(tokenizer, "my_domain_specific_data.txt")
merged_train_data, merged_valid_data, merged_test_data = five_classes_classification_dataset.get_merged_dataset()
LABEL.build_vocab(merged_train_data)
print(LABEL.vocab.stoi)

train_iterator, valid_iterator, test_iterator = data.BucketIterator.splits(
    (merged_train_data, merged_valid_data, merged_test_data), batch_size = BATCH_SIZE, sort=False, device = device)

model = BertEmbeddingsClassifier(HIDDEN_DIM, OUTPUT_DIM, N_LAYERS, BIDIRECTIONAL, DROPOUT, tokenizer)

model_path = "aiops_model_001_after_epoch_007.pt"
model_path = "aiops_model_002_after_epoch_007.pt"
model.load_model(model_path)
model.classify_first_tokenized_split("This film is terrible")
model.classify_first_tokenized_split("This film is great")
model.classify_first_tokenized_split("Facing this issue from last few days, so kindly help me in resolving the same.")
model.classify_first_tokenized_split("Why the issue is not resolved till now")
