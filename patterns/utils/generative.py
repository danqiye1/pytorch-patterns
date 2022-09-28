"""
Training utility for Generative Replay

@author: Ye Danqi
"""
import torch
from torch.utils.data import DataLoader
from IPython import get_ipython

if get_ipython().__class__.__name__ == "ZMQInteractiveShell":
    from tqdm.notebook import tqdm
else:
    from tqdm import tqdm

def train_gan(
        generator, discriminator,
        dataset, batch_size=32,
        optim_g=None, optim_d=None,
        criterion=torch.nn.BCELoss(),
        device=torch.device("cpu"),
        feature_size=100
    ):
    """ Train one epoch of GAN.

    Args:
        generator (torch.nn.Module): GAN generator.
        discriminator (torch.nn.Module): GAN discriminator.
        dataset (torch.utils.data.DataSet): PyTorch DataSet of 
            training data.
        optim_g (torch.optim.Optimizer): Optimizer for generator.
            Defaults to None.
        optim_d (torch.optim.Optimizer): Optimizer for discriminator.
            Defaults to None.
        criterion (torch.nn.Module): PyTorch loss function.
        device (torch.device): The device for training.

    Returns:
        model (torch.nn.Module): A model that is trained. If immutable=False, this is
            the reference to the original model.
        loss (float): Average loss from this training epoch. 
    """
    generator = generator.to(device)
    discriminator = discriminator.to(device)
    generator.train()
    discriminator.train()

    running_g_loss = 0.0
    running_d_loss = 0.0

    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=2
    )

    num_batches = len(dataloader)

    if not optim_g:
        # Default optimizer if one is not provided
        optim_g = torch.optim.Adam(generator.parameters(), lr=0.001, betas=(0.5, 0.99))

    if not optim_d:
        # Default optimizer if one is not provided
        optim_d = torch.optim.Adam(discriminator.parameters(), lr=0.001, betas=(0.5, 0.99))
    
    for data in tqdm(dataloader):
        imgs, _ = data
        
        #########################
        # Training of Generator #
        #########################

        optim_g.zero_grad()

        # Sample random latent vector
        # and generate fake labels
        z = torch.randn((imgs.size(0), feature_size, 1, 1), device=device)
        labels = torch.full((imgs.size(0),), 1, dtype=torch.float, device=device)
        
        # Forward pass
        fake_imgs = generator(z)
    
        # Compute loss and backpropagate error gradients
        loss = criterion(discriminator(fake_imgs).squeeze(), labels)
        loss.backward()
        
        # Gradient descent
        optim_g.step()
        
        # Gather running loss
        running_g_loss += loss.item()

        #######################
        # Train Discriminator #
        #######################

        optim_d.zero_grad()
        
        label_real = torch.full((imgs.size(0),), 1, dtype=torch.float, device=device)
        label_fake = torch.full((imgs.size(0),), 0, dtype=torch.float, device=device)
        loss_on_real = criterion(discriminator(imgs.to(device)).squeeze(), label_real)
        loss_on_fake = criterion(discriminator(fake_imgs.detach()).squeeze(), label_fake)

        loss = loss_on_real + loss_on_fake

        loss.backward()
        optim_d.step()

        running_d_loss += loss.item()
        
    return running_g_loss / num_batches, running_d_loss / num_batches