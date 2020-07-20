import datetime
import sys
import time

import torch

from aiops.config import logger


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

    def custom_training(self):
        epoch_loss = 0
        epoch_acc = 0
        self.model.train()
        for batch in self.train_iterator:
            self.optimizer.zero_grad()
            predictions_temp = self.model(batch.text)
            predictions = predictions_temp.squeeze(1)
            loss_value = self.loss(predictions, batch.label)
            acc = ModelTraining.categorical_accuracy(predictions, batch.label)
            loss_value.backward()
            self.optimizer.step()
            epoch_loss += loss_value.item()
            epoch_acc += acc.item()
            break
        return epoch_loss / len(self.train_iterator), epoch_acc / len(self.train_iterator)

    def evaluate(self):
        epoch_loss = 0
        epoch_acc = 0
        self.model.eval()
        with torch.no_grad():
            for batch in self.valid_iterator:
                predictions = self.model(batch.text).squeeze(1)
                loss = self.loss(predictions, batch.label)
                acc = ModelTraining.categorical_accuracy(predictions, batch.label)
                epoch_loss += loss.item()
                epoch_acc += acc.item()
        return epoch_loss / len(self.valid_iterator), epoch_acc / len(self.valid_iterator)

    def run_epochs_training(self, model_name='aiops_model_001_after_epoch_{}.pt'):
        training_loss_array, training_accuracy_array, validation_loss_array, validation_accuracy_array = [],[],[],[]
        for epoch in range(self.no_of_epochs):
            logger.info(f'Epoch: {epoch + 1:02} started!')
            start_time = time.time()
            train_loss, train_acc = self.custom_training()
            valid_loss, valid_acc = self.evaluate()
            end_time = time.time()
            epoch_mins, epoch_secs = ModelTraining.epoch_time(start_time, end_time)
            if valid_loss < self.best_valid_loss:
                self.best_valid_loss = valid_loss
                model_file_name = model_name.format(str(epoch + 1).zfill(3))
                logger.info("Saving model to the directory: '{}'".format(model_file_name))
                torch.save(self.model.state_dict(), model_file_name)
            logger.info(f'Epoch: {epoch + 1:02} | Epoch Time: {epoch_mins}m {epoch_secs}s | Train Loss: {train_loss:.3f} | Train Acc: {train_acc * 100:.2f}% | Val. Loss: {valid_loss:.3f} |  Val. Acc: {valid_acc * 100:.2f}%')
            training_loss_array.append(train_loss)
            training_accuracy_array.append(train_acc)
            validation_loss_array.append(valid_loss)
            validation_accuracy_array.append(valid_acc)
        return training_loss_array, training_accuracy_array, validation_loss_array, validation_accuracy_array

    @staticmethod
    def epoch_time(start_time, end_time):
        elapsed_time = end_time - start_time
        elapsed_mins = int(elapsed_time / 60)
        elapsed_secs = int(elapsed_time - (elapsed_mins * 60))
        return elapsed_mins, elapsed_secs

    @staticmethod
    def categorical_accuracy(preds, y):
        max_preds = preds.argmax(dim=1, keepdim=True)  # get the index of the max probability
        correct = max_preds.squeeze(1).eq(y)
        return correct.sum() / torch.FloatTensor([y.shape[0]])
