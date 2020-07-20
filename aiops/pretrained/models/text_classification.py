import torch
import torch.nn as nn
from torch import optim
from transformers import BertModel

from aiops.config import logger


class BertEmbeddingsClassifier(nn.Module):
    '''
    Tokenizer should build vocabulary in advance
    '''
    def __init__(self, hidden_dim, output_dim, n_layers, bidirectional, dropout, tokenizer, output_label_to_index=None, bert=BertModel.from_pretrained('bert-base-uncased')):
        super().__init__()
        self.bert = bert
        embedding_dim = self.bert.config.to_dict()['hidden_size']
        self.tokenizer = tokenizer
        self.rnn = nn.GRU(embedding_dim, hidden_dim, num_layers=n_layers, bidirectional=bidirectional, batch_first=True,
                          dropout=0 if n_layers < 2 else dropout)
        self.out = nn.Linear(hidden_dim * 2 if bidirectional else hidden_dim, output_dim)
        self.dropout = nn.Dropout(dropout)
        self.output_label_to_index = self.tokenizer.get_label_processor().vocab.stoi if not output_label_to_index else output_label_to_index
        self.output_index_to_label = {v: k for k, v in self.output_label_to_index.items()}

    def forward(self, text):
        with torch.no_grad():
            embedded = self.bert(text)[0]
        _, hidden = self.rnn(embedded)
        if self.rnn.bidirectional:
            hidden = self.dropout(torch.cat((hidden[-2, :, :], hidden[-1, :, :]), dim=1))
        else:
            hidden = self.dropout(hidden[-1, :, :])
        output = self.out(hidden)
        return output

    def freeze_learning_of_bert_weights(self):
        for name, param in self.named_parameters():
            if name.startswith('bert'):
                param.requires_grad = False

        def count_parameters(model):
            ll = [p.numel() for p in model.parameters() if p.requires_grad]
            return sum(ll)

        if 10 == 10:
            for name, param in self.named_parameters():
                if param.requires_grad:
                    logger.debug("{} : {}".format(name, len(param)))

        logger.debug(f'The model has {count_parameters(self):,} trainable parameters')

    def get_optimizer(self, optimizer_func=optim.Adam):
        return optimizer_func(self.parameters())

    def get_loss(self, loss_func=nn.CrossEntropyLoss):
        return loss_func()

    def load_model(self, model_path, device_name='cpu'):
        self.load_state_dict(torch.load(model_path, map_location=torch.device(device_name)))

    def classify(self, sentence):
        return self.classify_first_tokenized_split(sentence)

    def classify_first_tokenized_split(self, sentence):
        return self._classify_first_tokenized_split(self, self.tokenizer, sentence)

    def _classify_first_tokenized_split(self, model, tokenizer, sentence):
        model.eval()
        tokens = tokenizer.get_first_tokenized_split(sentence)
        indexed = [tokenizer.init_token_idx] + tokenizer.bert_tokenizer.convert_tokens_to_ids(tokens) + [tokenizer.eos_token_idx]
        tensor = torch.LongTensor(indexed)
        tensor_new = tensor.unsqueeze(0)
        model_output = model(tensor_new)
        model_output = torch.nn.functional.softmax(model_output, dim=1).data
        text_prediction_dict = {}
        for index, probability in enumerate(model_output[0]):
            text_prediction_dict.update({self.output_index_to_label.get(index): round(100 * probability.item(), 2)})
        return text_prediction_dict

    def classify_by_tokenized_splits(self, sentence):
        return self._classify_text_internal(self, self.tokenizer, sentence)

    def _classify_text_internal(self, model, tokenizer, sentence):
        model.eval()
        text_prediction_dict = {}
        for text_split, text_split_tokens in tokenizer.get_tokenized_splits(sentence).items():
            indexed = [tokenizer.init_token_idx] + tokenizer.bert_tokenizer.convert_tokens_to_ids(text_split_tokens) + [tokenizer.eos_token_idx]
            tensor = torch.LongTensor(indexed)
            tensor_new = tensor.unsqueeze(0)
            model_output = model(tensor_new)
            model_output = torch.nn.functional.softmax(model_output, dim=1).data
            split_text_prediction_dict = {}
            for index, probability in enumerate(model_output[0]):
                split_text_prediction_dict.update({self.output_index_to_label.get(index): round(100 * probability.item(), 2)})
            text_prediction_dict.update(split_text_prediction_dict)
        return text_prediction_dict

    @staticmethod
    def categorical_accuracy(prediction, y):
        max_prediction = prediction.argmax(dim=1, keepdim=True)  # get the index of the max probability
        correct = max_prediction.squeeze(1).eq(y)
        return correct.sum() / torch.FloatTensor([y.shape[0]])
