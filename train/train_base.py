"""
正常的对抗训练
"""

import torchattacks
import torch

from utils.utils import *


class Trainer_base:
    def __init__(self, args, writer, attack_name, device, loss_function=torch.nn.CrossEntropyLoss()):
        self.args = args
        self.writer = writer
        self.device = device

        self.attack_name = attack_name

        self.loss_fn = loss_function

    def get_attack(self, model):
        if self.attack_name == 'pgd':
            return torchattacks.PGD(model=model,
                                    eps=self.args.epsilon,
                                    alpha=self.args.alpha,
                                    steps=self.args.iters,
                                    random_start=True)
        elif self.attack_name == 'fgsm':
            return torchattacks.FGSM(model=model,
                                     eps=self.args.epsilon)
        else:
            raise 'no match attack method'

    def train(self, **kwargs):
        pass

    def valid(self, model, valid_loader, use_pseudo_label=False):
        total_acc = 0.
        num = 0
        total_adv_acc = 0.

        attack_method = self.get_attack(model)

        model.eval()

        with torch.no_grad():
            for idx, (data, label) in enumerate(valid_loader):
                data, label = data.to(self.device), label.to(self.device)

                output = model(data)

                pred = torch.max(output, dim=1)[1]
                std_acc = evaluate(pred.cpu().numpy(), label.cpu().numpy(), 'sum')

                total_acc += std_acc
                num += output.shape[0]

                with torch.enable_grad():
                    adv_data = attack_method(data,
                                             pred if use_pseudo_label else label)
                adv_output = model(adv_data)

                adv_pred = torch.max(adv_output, dim=1)[1]
                adv_acc = evaluate(adv_pred.cpu().numpy(), label.cpu().numpy(), 'sum')
                total_adv_acc += adv_acc

        model.train()

        return total_acc / num, total_adv_acc / num

