from torchtext import data
from transformers import BertTokenizer, BertModel


class Tokenizer:

    def __init__(self, model_name='bert-base-uncased') -> None:
        super().__init__()
        self.bert_tokenizer = BertTokenizer.from_pretrained(model_name)
        self.bert_model = BertModel.from_pretrained(model_name)
        self.init_token = self.bert_tokenizer.cls_token
        self.eos_token = self.bert_tokenizer.sep_token
        self.pad_token = self.bert_tokenizer.pad_token
        self.unk_token = self.bert_tokenizer.unk_token
        self.init_token_idx = self.bert_tokenizer.cls_token_id
        self.eos_token_idx = self.bert_tokenizer.sep_token_id
        self.pad_token_idx = self.bert_tokenizer.pad_token_id
        self.unk_token_idx = self.bert_tokenizer.unk_token_id
        self.max_input_length = self.bert_tokenizer.max_model_input_sizes[model_name]
        self.embedding_dim_from_bert_model = self.bert_model.config.to_dict()['hidden_size']
        self.text_processor = data.Field(batch_first=True, use_vocab=False, tokenize=self.cut_and_tokenize_first,
                   preprocessing=self.bert_tokenizer.convert_tokens_to_ids, init_token=self.init_token_idx,
                   eos_token=self.eos_token_idx, pad_token=self.pad_token_idx, unk_token=self.unk_token_idx)
        self.data_processor = data.LabelField()

    def tokenize(self, text):
        return self.bert_tokenizer.tokenize(text)

    def cut_and_tokenize(self, text):
        start = 0
        end = len(text)
        token_list = []
        for token_start in range(start, end, self.max_input_length):
            token_list.append(self.tokenize(text[token_start: token_start + self.max_input_length]))
            token_start += self.max_input_length
        return token_list

    def cut_and_tokenize_first(self, text):
        start = 0
        end = len(text)
        for token_start in range(start, end, self.max_input_length):
            return self.tokenize(text[token_start: token_start + self.max_input_length])

    def get_text_processor(self):
        return self.text_processor

    def get_label_processor(self):
        return self.data_processor


if __name__ == "__main__":
    tokenizer = Tokenizer()
    print(tokenizer.tokenize("time"))
