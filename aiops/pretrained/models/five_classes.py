import logging

import torch
import torch.nn as nn
from torch import optim
from transformers import BertModel


class TextClassifierWithBertEmbeddings(nn.Module):
    def __init__(self, hidden_dim, output_dim, n_layers, bidirectional, dropout, tokenizer, bert=BertModel.from_pretrained('bert-base-uncased')):
        super().__init__()
        self.bert = bert
        embedding_dim = self.bert.config.to_dict()['hidden_size']
        self.tokenizer = tokenizer
        self.rnn = nn.GRU(embedding_dim, hidden_dim, num_layers=n_layers, bidirectional=bidirectional, batch_first=True,
                          dropout=0 if n_layers < 2 else dropout)
        self.out = nn.Linear(hidden_dim * 2 if bidirectional else hidden_dim, output_dim)
        self.dropout = nn.Dropout(dropout)
        self.output_label_to_index = { key:value for key, value in self.tokenizer.get_label_processor().vocab.stoi.items()}
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

        logging.debug(f'The model has {count_parameters(self):,} trainable parameters')

    def get_optimizer(self, optimizer_func=optim.Adam):
        return optimizer_func(self.parameters())

    def get_loss(self, loss_func=nn.CrossEntropyLoss):
        return loss_func()

    def model_loading(self, model_path):
        self.load_state_dict(torch.load(model_path))

    def classify_text(self, sentence):
        return self.classify_text_internal(self, self.tokenizer, sentence)

    def classify_text_internal(self, model, tokenizer, sentence):
        model.eval()
        tokens = tokenizer.tokenize(sentence)
        tokens = tokens[:self.max_input_length - 2]
        indexed = [self.init_token_idx] + tokenizer.convert_tokens_to_ids(tokens) + [self.eos_token_idx]
        tensor = torch.LongTensor(indexed)
        tensor_new = tensor.unsqueeze(0)
        model_output = model(tensor_new)
        model_output = torch.nn.functional.softmax(model_output, dim=1).data
        output_dict = {}
        for index, probability in enumerate(model_output[0]):
            output_dict.update({self.output_index_to_label.get(index): round(100 * probability.item(), 2)})
        return output_dict
