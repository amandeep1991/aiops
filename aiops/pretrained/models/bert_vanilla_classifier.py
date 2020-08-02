import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchtext.data import Dataset
from transformers import BertModel, BertTokenizer
import torch.nn.functional as F

class BertVanillaClassifier(nn.Module):
    def __init__(self, n_classes, pre_trained_model_name='bert-base-cased'):
        super(BertVanillaClassifier, self).__init__()
        self.bert = BertModel.from_pretrained(pre_trained_model_name)
        self.drop = nn.Dropout(p=0.3)
        self.out = nn.Linear(self.bert.config.hidden_size, n_classes)

    def forward(self, input_ids, attention_mask):
        _, pooled_output = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        output = self.drop(pooled_output)
        return self.out(output)


class BertVanillaClassifierPredictor:

    def __init__(self, model: BertVanillaClassifier):
        self.model = model

    def predict(self, data_loader, device=torch.device('cpu')):
        model = self.model.eval()

        texts = []
        predictions = []
        prediction_probs = []
        real_values = []

        with torch.no_grad():
            for d in data_loader:
                texts = d["text"]
                input_ids = d["input_ids"].to(device)
                attention_mask = d["attention_mask"].to(device)
                targets = d["targets"].to(device)

                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask
                )
                _, preds = torch.max(outputs, dim=1)

                probs = F.softmax(outputs, dim=1)

                texts.extend(texts)
                predictions.extend(preds)
                prediction_probs.extend(probs)
                real_values.extend(targets)

        predictions = torch.stack(predictions).cpu()
        prediction_probs = torch.stack(prediction_probs).cpu()
        real_values = torch.stack(real_values).cpu()
        return texts, predictions, prediction_probs, real_values


class BertVanillaClassifierDataset(Dataset):
    def __init__(self, texts, targets, tokenizer, max_len=180):
        self.texts = texts
        self.targets = targets
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, item):
        text = str(self.texts[item])
        target = self.targets[item]

        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            truncation=True,
            return_token_type_ids=False,
            pad_to_max_length=True,
            return_attention_mask=True,
            return_tensors='pt',
        )

        return {
            'text': text,
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'targets': torch.tensor(target, dtype=torch.long)
        }


class BertVanillaClassifierDataLoader:

    @staticmethod
    def create_data_loader(df: pd.DataFrame, tokenizer, batch_size=16, max_len=180, num_workers=4):
        ds = BertVanillaClassifierDataset(
            texts=df.text.to_numpy(),
            targets=df.sentiment.to_numpy(),
            tokenizer=tokenizer,
            max_len=max_len,
        )

        return DataLoader(
            ds,
            batch_size=batch_size,
            num_workers=num_workers
        )


if __name__ == "__main__":
    pretrained_model_name = 'bert-base-cased'
    model = BertVanillaClassifier(n_classes=4, pre_trained_model_name = pretrained_model_name)
    model.load_state_dict(torch.load("C:\\ML\\code\\prod\\python\\soa_binaries\\ml_models\\torch\\best_model_state-4.bin", map_location=torch.device('cpu')))
    predictor = BertVanillaClassifierPredictor(model=model)
    text_list = [
        """Your service is terrible.""",
        """Any updates please. We are still waiting the your reply on below points: Confirmation of applying the proactive monitoring on the CRON Jobs that were stopped frequently and need to be monitored. The root cause of why the CRON Jobs were stopped suddenly. Sharing the support model if exists, if not, what will be the model of support in the future.""",
        """This is terrible service""",
        """What were the outage times to each of these circuits?""",
        """Happy with your prompt response and resolution.""",
        """Primary Link is down and traffic is on secondary""",
        """Circuit is stable now. Do we know permanent fix was in place and no more flaps will be observed. Before even reaching to RFO, always first confirm the permanent fix. I have said this multiple times before.""",
        """Refer to OBS no 2007Y03522 , We have engage regional team to check with telco. Will get back soon.""",
    ]
    df = pd.DataFrame({"text": text_list, "sentiment":[1]*len(text_list)})
    bert_tokenizer = BertTokenizer.from_pretrained(pretrained_model_name)
    class_to_target = {'escalate': 0, 'urgent':1, 'neutral':2, 'positive':3}
    target_to_class = {v:k for k,v in class_to_target.items()}
    _, y_preds, y_pred_probs, _ = predictor.predict(BertVanillaClassifierDataLoader.create_data_loader(df, bert_tokenizer, batch_size=1, num_workers=0))
    for text, pred, prob in zip(text_list, y_preds, y_pred_probs):
        print("{} ({}) :: {}".format(target_to_class.get(pred.item()), round(prob[pred.item()].item()*100), text))
