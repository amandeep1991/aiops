import datetime
import sys
import time

import torch


class ModelTraining:

    def __init__(self, model, optimizer, loss, train_iterator, valid_iterator, no_of_epochs) -> None:
        super().__init__()
        self.loss = loss
        self.model = model
        self.optimizer = optimizer
        self.train_iterator = train_iterator
        self.valid_iterator = valid_iterator
        self.no_of_epochs = no_of_epochs
        self.best_valid_loss = sys.maxsize

    def custom_training(self, model, data_iterator, optimizer, criterion, no_of_epochs):
        epoch_loss = 0
        epoch_acc = 0
        model.train()
        for batch in data_iterator:
            optimizer.zero_grad()
            predictions_temp = model(batch.text)
            print("predictions_temp: '{}'".format(predictions_temp))
            predictions = predictions_temp.squeeze(1)
            print("predictions: '{}'".format(predictions))
            loss = criterion(predictions, batch.label)
            print("batch.label: '{}'".format(batch.label))
            print("loss: '{}'".format(loss))
            # acc = binary_accuracy(predictions, batch.label)
            acc = self.categorical_accuracy(predictions, batch.label)
            print("acc: '{}'".format(acc))
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            epoch_acc += acc.item()
            break
        return epoch_loss / len(data_iterator), epoch_acc / len(data_iterator)

    def categorical_accuracy(preds, y):
        max_preds = preds.argmax(dim=1, keepdim=True)  # get the index of the max probability
        correct = max_preds.squeeze(1).eq(y)
        return correct.sum() / torch.FloatTensor([y.shape[0]])

    def evaluate(self, model, data_iterator, criterion):
        epoch_loss = 0
        epoch_acc = 0
        model.eval()
        with torch.no_grad():
            for batch in data_iterator:
                predictions = model(batch.text).squeeze(1)
                loss = criterion(predictions, batch.label)
                acc = self.categorical_accuracy(predictions, batch.label)
                epoch_loss += loss.item()
                epoch_acc += acc.item()
        return epoch_loss / len(data_iterator), epoch_acc / len(data_iterator)

    def run_epochs_training(self):
        for epoch in range(self.no_of_epochs):
            print(f'Epoch: {epoch + 1:02} started!')
            start_time = time.time()
            train_loss, train_acc = self.custom_training(self.model, self.train_iterator, self.optimizer, self.loss)
            valid_loss, valid_acc = self.evaluate(self.model, self.valid_iterator, self.loss)
            end_time = time.time()
            epoch_mins, epoch_secs = ModelTraining.epoch_time(start_time, end_time)
            if valid_loss < best_valid_loss:
                best_valid_loss = valid_loss
                model_file_name = 'aiops_model_001_after_epoch_{}.pt'.format(str(epoch + 1).zfill(3))
                print("Saving model to the directory: '{}'".format(model_file_name))
                torch.save(self.model.state_dict(), model_file_name)
            print(f'Epoch: {epoch + 1:02} | Epoch Time: {epoch_mins}m {epoch_secs}s')
            print(f'\tTrain Loss: {train_loss:.3f} | Train Acc: {train_acc * 100:.2f}%')
            print(f'\t Val. Loss: {valid_loss:.3f} |  Val. Acc: {valid_acc * 100:.2f}%')
            print("Current Time", datetime.datetime.now())

    @staticmethod
    def epoch_time(start_time, end_time):
        elapsed_time = end_time - start_time
        elapsed_mins = int(elapsed_time / 60)
        elapsed_secs = int(elapsed_time - (elapsed_mins * 60))
        return elapsed_mins, elapsed_secs
