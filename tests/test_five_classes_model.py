from aiops.pretrained.models.five_classes import TextClassifierWithBertEmbeddings
from aiops.utils.text_preprocessing.text_cleaning import HtmlTextCleaning
from aiops.utils.text_preprocessing.bert import Tokenizer
from aiops.utils.data_augmentation.bert import FiveClassesClassificationDataSet

tokenizer = Tokenizer()
tokenize_and_cut = tokenizer.cut_and_tokenize_first
print(tokenize_and_cut("networkk"))
TEXT = tokenizer.get_text_processor()
LABEL = tokenizer.get_label_processor()
five_classes_classification_dataset = FiveClassesClassificationDataSet(tokenizer, "my_domain_specific_data.txt")
merged_train_data, merged_valid_data, merged_test_data = five_classes_classification_dataset.get_merged_dataset()
LABEL.build_vocab(merged_train_data)
print(LABEL.vocab.stoi)